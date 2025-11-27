import asyncio
import aiohttp
import time
from typing import Optional, List, Dict
from asgiref.sync import sync_to_async
from django.db import transaction

from agent.index import CodeProcessor, FolderProcessor
from agent.dependency_parser import DependencyParser
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
        # Note: This service is instantiated per task, so it is not a singleton.
        # However, we use a semaphore to limit concurrent requests to GitHub/LLM to avoid rate limits.
        self.codeProcessor = CodeProcessor(llm_provider)
        self.folderProcessor = FolderProcessor(llm_provider)
        self.folderPathMap: Dict[str, int] = {}
        self.repoFileInfo: Optional[Dict[str, str]] = None
        self.semaphore = asyncio.Semaphore(20)  # Limit concurrent GitHub requests
        self.dependencyParser = DependencyParser()

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
        start_time = time.time()
        fullTree = await fetch_github_repo_tree(owner, repo, repo_details.sha)
        logger.info(f"Fetched repo tree in {time.time() - start_time:.2f}s")

        await update_status("Step 5: Filtering tree in memory...")
        filteredTree = self._filterTree(fullTree)

        await update_status("Step 6: Inserting folder structure into DB...")
        await self._insertFolders(filteredTree, branch, None)

        await update_status("Step 7: Fetching files and summarizing folders in parallel...")
        folder_progress = [0]  # Shared counter for folder progress
        folder_ready_events = {path: asyncio.Event() for path in self.folderPathMap.keys()}

        folders_start = time.time()
        folder_summary_task = asyncio.create_task(
            self._summarizeFolders(
                filteredTree,
                update_status,
                folder_progress,
                depth=0,
                folder_ready_events=folder_ready_events
            )
        )

        files_start = time.time()
        await self._fetchAndInsertFiles(filteredTree, update_status, folder_ready_events)
        logger.info(f"Fetched and inserted files in {time.time() - files_start:.2f}s")

        repo_summary = await folder_summary_task
        logger.info(f"Summarized folders in {time.time() - folders_start:.2f}s")

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

    async def _fetchAndInsertFiles(self, rootTree: RepoTreeResult, update_status_func=None, folder_ready_events: Optional[Dict[str, asyncio.Event]] = None):
        all_file_paths = []
        def gather_files(t: RepoTreeResult):
            all_file_paths.extend(t.files)
            for s in t.subdirectories:
                gather_files(s)
        gather_files(rootTree)
        
        if update_status_func:
            await update_status_func(f"Found {len(all_file_paths)} files to process...")
        
        progress_counter = 0
        progress_lock = asyncio.Lock()
        total_files = len(all_file_paths)

        async def fetch_content(fp: str, session: aiohttp.ClientSession):
            if not self.repoFileInfo:
                logger.error("repoFileInfo is None")
                return fp, None
                
            async with self.semaphore:
                try:
                    content = await fetch_github_repo_file(
                        self.repoFileInfo["repo_owner"],
                        self.repoFileInfo["repo_name"],
                        self.repoFileInfo["commit_sha"],
                        fp,
                        session
                    )
                    return fp, content
                except Exception as e:
                    logger.error(f"\tFailed fetching file: {fp}, error: {e}")
                    return fp, None

        async def summarize_file(file_path: str, content: Optional[str]):
            nonlocal progress_counter
            if not content: return None
            
            # Parse dependencies from the file content
            dependencies = self.dependencyParser.parse(content, file_path)
            
            aiSummary = None
            retries = 0
            wordDeduction = 0
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
            async with progress_lock:
                progress_counter += 1
                if update_status_func and total_files and progress_counter % 5 == 0:  # Update every 5 files
                    await update_status_func(f"Summarized {progress_counter}/{total_files} files...")
            
            return {"filePath": file_path, "content": content, "aiSummary": aiSummary, "dependencies": dependencies}

        async def process_files_for_folder(file_paths: List[str], folder_path: str, session: aiohttp.ClientSession):
            folder_event = folder_ready_events.get(folder_path) if folder_ready_events is not None else None

            if not file_paths:
                if folder_event:
                    folder_event.set()
                return

            try:
                async def process_single_file(fp):
                    _, content = await fetch_content(fp, session)
                    return await summarize_file(fp, content)

                tasks = [process_single_file(fp) for fp in file_paths]
                processed_files = await asyncio.gather(*tasks)

                files_to_create = []
                for f in processed_files:
                    if not f or not f["aiSummary"]: 
                        continue
                    file_path = f["filePath"]
                    folder_id = self.folderPathMap.get(folder_path)
                    if not folder_id:
                        continue

                    file_name = file_path.split("/")[-1]

                    files_to_create.append(File(
                        name=file_name,
                        folder_id=folder_id,
                        content=f["content"],
                        ai_summary=f["aiSummary"].summary,
                        usage=f["aiSummary"].usage,
                        dependencies=f.get("dependencies", [])
                    ))

                if files_to_create:
                    await File.objects.abulk_create(files_to_create)
            finally:
                if folder_event:
                    folder_event.set()

        async def process_folder(tree: RepoTreeResult, session: aiohttp.ClientSession):
            folder_path = tree.path
            file_task = asyncio.create_task(process_files_for_folder(tree.files, folder_path, session))
            sub_tasks = [asyncio.create_task(process_folder(sub, session)) for sub in tree.subdirectories]
            await asyncio.gather(file_task, *sub_tasks)

        async with aiohttp.ClientSession() as session:
            await process_folder(rootTree, session)

    async def _summarizeFolders(self, tree: RepoTreeResult, update_status_func=None, folder_progress=None, depth=0, folder_ready_events: Optional[Dict[str, asyncio.Event]] = None) -> Optional[str]:
        folder_name = tree.path or "/"
        
        # Parallelize subfolder summarization: Spawn tasks for all subdirectories immediately
        # so they can proceed independently as soon as their files are ready.
        tasks = [asyncio.create_task(self._summarizeFolders(subdir, update_status_func, folder_progress, depth + 1, folder_ready_events)) for subdir in tree.subdirectories]
        subfolders_future = asyncio.gather(*tasks) if tasks else None

        waitables = []
        if subfolders_future:
            waitables.append(subfolders_future)

        folder_event = None
        if folder_ready_events is not None:
            folder_event = folder_ready_events.get(tree.path)
            if folder_event:
                waitables.append(folder_event.wait())

        if waitables:
            await asyncio.gather(*waitables)

        subfolders_summaries_results = subfolders_future.result() if subfolders_future else []
        
        subfolders_summaries = []
        for i, summary in enumerate(subfolders_summaries_results):
            if summary:
                subfolders_summaries.append(f"Summary of folder {tree.subdirectories[i].path}:\n{summary}\n")

        folder_id = self.folderPathMap.get(tree.path)
        if not folder_id: return None

        files_in_folder = []
        async for f in File.objects.filter(folder_id=folder_id):
            files_in_folder.append(f)
        
        # Build file summaries with import information for LLM context
        file_summaries = []
        for f in files_in_folder:
            if f.ai_summary:
                summary_parts = [f"Summary of file {f.name}:\n{f.ai_summary}"]
                # Include import info to help LLM understand dependencies
                if f.dependencies:
                    summary_parts.append(f"Imports: {', '.join(f.dependencies[:10])}")  # Limit to avoid token overflow
                file_summaries.append("\n".join(summary_parts) + "\n")

        if not subfolders_summaries and not file_summaries:
            return None

        # Combine all context for the LLM
        combined_parts = subfolders_summaries + file_summaries
        combined = "\n\n".join(combined_parts)

        aiSummary = None
        retries = 0
        summaryDeduction = 0
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

        # Use the LLM-generated dependency graph with descriptive relationship labels
        dependency_graph = aiSummary.dependency_graph if hasattr(aiSummary, 'dependency_graph') else None

        await Folder.objects.filter(folder_id=folder_id).aupdate(
            ai_summary=aiSummary.summary,
            usage=aiSummary.usage,
            dependency_graph=dependency_graph if dependency_graph else None
        )
        
        if folder_progress is not None:
            folder_progress[0] += 1
            if update_status_func and folder_progress[0] % 5 == 0:
                await update_status_func(f"Summarized {folder_progress[0]} folders...")
                
        return aiSummary.summary
