import asyncio
from typing import Optional, List, Dict
from asgiref.sync import sync_to_async
from django.db import transaction

from agent.index import CodeProcessor, FolderProcessor
from wiki_app.models import Repository, Branch, Folder, File, Topic
from github.fetch_repo import fetch_github_repo_details, fetch_github_repo_tree, RepoTreeResult, fetch_github_repo_file
from github.filterfile import whitelisted_file, blacklisted_file, whitelisted_filter, blacklisted_files, \
    blacklisted_folder, blacklisted_filter
from llm.llm_provider import LLMProvider
from wiki_app.config import TokenProcessingConfig
from wiki_app.allowed_languages import ALLOWED_LANGUAGES
from loguru import logger

class InsertRepoService:
    def __init__(self, llm_provider: LLMProvider):
        self.codeProcessor = CodeProcessor(llm_provider)
        self.folderProcessor = FolderProcessor(llm_provider)
        self.folderPathMap: Dict[str, int] = {}
        self.repoFileInfo: Optional[Dict[str, str]] = None
        self.github_semaphore = asyncio.Semaphore(10)  # Limit concurrent GitHub requests
        self.llm_semaphore = asyncio.Semaphore(TokenProcessingConfig['llmConcurrency'])  # Limit concurrent LLM requests

    async def insertRepository(self, owner: str, repo: str):
        # Create initial repository record to track status
        repo_url = f"https://github.com/{owner}/{repo}"
        repository, _ = await Repository.objects.aupdate_or_create(
            url=repo_url,
            defaults={
                'owner': owner,
                'repo': repo,
                'default_branch': 'main', # Temporary default
                'process_status': f"Starting processing for {owner}/{repo}..."
            }
        )

        async def update_status(msg: str):
            logger.info(msg)
            repository.process_status = msg
            await repository.asave(update_fields=['process_status'])

        await update_status(f"Step 1: Fetching repository details for {owner}/{repo}...")
        repo_details = await fetch_github_repo_details(owner, repo)

        if repo_details.language and repo_details.language not in ALLOWED_LANGUAGES:
            await update_status(f"Language {repo_details.language} not supported. Skipping.")
            return None

        await update_status(f"Step 2: Inserting repository {repo_details.repo_owner}/{repo_details.repo_name} into DB...")
        
        # Upsert Repository
        repository, created = await Repository.objects.aupdate_or_create(
            url=repo_details.url,
            defaults={
                'owner': repo_details.repo_owner,
                'repo': repo_details.repo_name,
                'language': repo_details.language,
                'descriptions': repo_details.description,
                'default_branch': repo_details.default_branch,
                'stars': repo_details.stars,
                'forks': repo_details.forks,
                'process_status': "Updating repository details..."
            }
        )
        
        # Handle Topics
        for topic_name in repo_details.topics:
            topic, _ = await Topic.objects.aget_or_create(topic_name=topic_name)
            await repository.topics.aadd(topic)

        if not created:
             logger.info(f"Repository updated: {owner}/{repo}")

        await update_status(f"Step 3: Inserting branch {repo_details.default_branch} into DB...")
        branch, _ = await Branch.objects.aget_or_create(
            repository=repository,
            last_commit_sha=repo_details.sha,
            defaults={
                'name': repo_details.default_branch,
                'commit_at': repo_details.commit_at,
            }
        )
        
        self.repoFileInfo = {
            "repo_owner": owner,
            "repo_name": repo,
            "commit_sha": repo_details.sha
        }

        await update_status(f"Step 4: Fetching entire repo tree for {owner}/{repo} @ {repo_details.sha}...")
        fullTree = await fetch_github_repo_tree(owner, repo, repo_details.sha)

        await update_status("Step 5: Filtering tree in memory...")
        filteredTree = self._filterTree(fullTree)

        await update_status("Step 6: Inserting folder structure into DB...")
        await self._insertFolders(filteredTree, branch, None)

        await update_status("Step 7: Fetching and summarizing files in parallel...")
        # We need to pass update_status to _fetchAndInsertFiles to get granular updates
        await self._fetchAndInsertFiles(filteredTree, update_status)

        await update_status("Step 8: Summarizing folders bottom-up...")
        repo_summary = await self._summarizeFolders(filteredTree, update_status, depth=0)

        # Store repo-level summary on the branch so the UI can detect completion
        if repo_summary:
            await Branch.objects.filter(branch_id=branch.branch_id).aupdate(
                ai_summary=repo_summary
            )

        await update_status("Done! Repository processed successfully.")
        return repository

    def _filterTree(self, tree: RepoTreeResult) -> RepoTreeResult:
        logger.info(f'Filtering tree at path "{tree.path or "/"}"...')
        allowed_files = whitelisted_file(tree.files, whitelisted_filter)
        allowed_files = blacklisted_files(allowed_files, blacklisted_file)
        allowed_subdirs = blacklisted_folder(tree.subdirectories, blacklisted_filter)
        pruned_subdirs = []
        for subdir in allowed_subdirs:
            filtered_subdir = self._filterTree(subdir)
            if filtered_subdir.files or filtered_subdir.subdirectories:
                pruned_subdirs.append(filtered_subdir)
        return RepoTreeResult(path=tree.path, files=allowed_files, subdirectories=pruned_subdirs)

    async def _insertFolders(self, tree: RepoTreeResult, branch: Branch, parent_folder: Optional[Folder]):
        folder_name = tree.path.split("/")[-1] if tree.path else ""
        folder_path = tree.path

        logger.info(f'\tInserting folder "{folder_name}" with path "{folder_path}"...')
        
        folder, _ = await Folder.objects.aget_or_create(
            path=folder_path,
            branch=branch,
            defaults={
                'name': folder_name,
                'parent_folder': parent_folder
            }
        )
        
        self.folderPathMap[folder_path] = folder.folder_id

        for subdir in tree.subdirectories:
            await self._insertFolders(subdir, branch, folder)

    async def _fetchAndInsertFiles(self, rootTree: RepoTreeResult, update_status_func=None):
        all_file_paths = []
        def gather_files(t: RepoTreeResult):
            all_file_paths.extend(t.files)
            for s in t.subdirectories:
                gather_files(s)
        gather_files(rootTree)
        
        if update_status_func:
            await update_status_func(f"Found {len(all_file_paths)} files to process...")
        
        async def fetch_content(fp: str):
            if not self.repoFileInfo:
                logger.error("repoFileInfo is None")
                return fp, None
                
            async with self.github_semaphore:
                try:
                    content = await fetch_github_repo_file(
                        self.repoFileInfo["repo_owner"],
                        self.repoFileInfo["repo_name"],
                        self.repoFileInfo["commit_sha"],
                        fp
                    )
                    return fp, content
                except Exception as e:
                    logger.error(f"\tFailed fetching file: {fp}, error: {e}")
                    return fp, None

        fetch_coros = [fetch_content(fp) for fp in all_file_paths]
        fetched_files = await asyncio.gather(*fetch_coros)

        if update_status_func:
            await update_status_func(f"Generating summaries for {len(fetched_files)} files...")
        
        # Track progress
        progress_counter = [0]  # Use list to allow modification in nested function
        total_files = len([f for f in fetched_files if f[1]])  # Count files with content
        
        async def summarize_file(file_path: str, content: Optional[str]):
            if not content: return None
            
            aiSummary = None
            retries = 0
            wordDeduction = 0
            async with self.llm_semaphore:
                while not aiSummary and retries < TokenProcessingConfig['maxRetries']:
                    try:
                        slice_size = TokenProcessingConfig['characterLimit'] - wordDeduction
                        reducedContent = content[: max(0, slice_size)]
                        aiSummary = await self.codeProcessor.generate(reducedContent, {
                            "path": file_path,
                            **(self.repoFileInfo or {})
                        })
                    except Exception:
                        pass
                    finally:
                        retries += 1
                        wordDeduction += TokenProcessingConfig['reduceCharPerRetry']
            
            # Update progress
            progress_counter[0] += 1
            if update_status_func and progress_counter[0] % 5 == 0:  # Update every 5 files
                await update_status_func(f"Summarized {progress_counter[0]}/{total_files} files...")
            
            return {"filePath": file_path, "content": content, "aiSummary": aiSummary}

        summarize_coros = [summarize_file(fp, ct) for fp, ct in fetched_files]
        processed_files = await asyncio.gather(*summarize_coros)

        if update_status_func:
            await update_status_func("Inserting summarized files into DB...")

        for f in processed_files:
            if not f or not f["aiSummary"]: continue
            file_path = f["filePath"]
            folder_path = file_path.rpartition("/")[0]
            folder_id = self.folderPathMap.get(folder_path)
            if not folder_id: continue
            
            file_name = file_path.split("/")[-1]
            
            # Use acreate for async creation
            await File.objects.acreate(
                name=file_name,
                folder_id=folder_id,
                content=f["content"],
                ai_summary=f["aiSummary"].summary,
                usage=f["aiSummary"].usage
            )

    async def _summarizeFolders(self, tree: RepoTreeResult, update_status_func=None, depth=0) -> Optional[str]:
        folder_name = tree.path or "/"
        
        # Only update status for top-level folders to avoid rapid overwrites
        if update_status_func and depth <= 1:
            await update_status_func(f'Summarizing folder "{folder_name}"...')

        # Parallelize subfolder summarization
        tasks = [self._summarizeFolders(subdir, update_status_func, depth + 1) for subdir in tree.subdirectories]
        subfolders_summaries_results = await asyncio.gather(*tasks)
        
        subfolders_summaries = []
        for i, summary in enumerate(subfolders_summaries_results):
            if summary:
                subfolders_summaries.append(f"Summary of folder {tree.subdirectories[i].path}:\n{summary}\n")

        folder_id = self.folderPathMap.get(tree.path)
        if not folder_id: return None

        files_in_folder = []
        async for f in File.objects.filter(folder_id=folder_id):
            files_in_folder.append(f)
            
        file_summaries = [
            f"Summary of file {f.name}:\n{f.ai_summary}\n"
            for f in files_in_folder
            if f.ai_summary
        ]

        if not subfolders_summaries and not file_summaries:
            return None

        combined = "\n\n".join(subfolders_summaries + file_summaries)

        aiSummary = None
        retries = 0
        summaryDeduction = 0
        async with self.llm_semaphore:
            while not aiSummary and retries < TokenProcessingConfig['maxRetries']:
                try:
                    slice_size = TokenProcessingConfig['characterLimit'] - summaryDeduction
                    reduced = combined[: max(0, slice_size)]
                    aiSummary = await self.folderProcessor.generate([reduced], {
                        "path": tree.path,
                        **(self.repoFileInfo or {})
                    })
                except Exception:
                    pass
                finally:
                    retries += 1
                    summaryDeduction += TokenProcessingConfig['reduceCharPerRetry']

        if not aiSummary: return None

        await Folder.objects.filter(folder_id=folder_id).aupdate(
            ai_summary=aiSummary.summary,
            usage=aiSummary.usage
        )
        return aiSummary.summary
