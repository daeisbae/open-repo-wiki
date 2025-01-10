import asyncio
from typing import Optional, List, Dict

from agent.index import CodeProcessor, FolderProcessor
from db.model.branch import Branch
from db.model.file import File
from db.model.folder import Folder
from db.utils.connector import AsyncDBConnector
from github.fetch_repo import fetch_github_repo_details, fetch_github_repo_tree, RepoTreeResult, fetch_github_repo_file
from github.filterfile import whitelisted_file, blacklisted_file, whitelisted_filter, blacklisted_files, \
    blacklisted_folder, blacklisted_filter
from llm.llm_provider import LLMProvider
from db.model.repository import Repository, RepositoryData
from service.config import TokenProcessingConfig

from loguru import logger


class InsertRepoService:
    def __init__(self, db: AsyncDBConnector, llm_provider: LLMProvider):
        self.repository = Repository(db)
        self.branch = Branch(db)
        self.folder = Folder(db)
        self.file = File(db)
        self.codeProcessor = CodeProcessor(llm_provider)
        self.folderProcessor = FolderProcessor(llm_provider)
        self.folderPathMap: Dict[str, int] = {}
        self.repoFileInfo: Optional[Dict[str, str]] = None

    async def insertRepository(self, owner: str, repo: str) -> Optional[RepositoryData]:
        logger.info(f"Step 1: Fetching repository details for {owner}/{repo}...")
        repo_details = await fetch_github_repo_details(owner, repo)

        logger.info(f"Step 2: Inserting repository {repo_details.repo_owner}/{repo_details.repo_name} into DB...")
        repositoryData = await self.repository.insert(
            repo_details.url,
            repo_details.repo_owner,
            repo_details.repo_name,
            repo_details.language,
            repo_details.description,
            repo_details.default_branch,
            repo_details.topics,
            repo_details.stars,
            repo_details.forks,
        )

        # If the repo already exists, insert() might return None
        if not repositoryData:
            logger.info(f"Repository already exists: {owner}/{repo}")
            return None

        logger.info(f"Step 3: Inserting branch {repo_details.default_branch} into DB...")
        branchCommit = await self.branch.insert(
            repo_details.sha,
            repo_details.default_branch,
            repo_details.url,
            repo_details.commit_at
        )
        branchId = branchCommit.branch_id

        # Store info for summarization
        self.repoFileInfo = {
            "repo_owner": owner,
            "repo_name": repo,
            "commit_sha": repo_details.sha
        }

        logger.info(f"Step 4: Fetching entire repo tree for {owner}/{repo} @ {repo_details.sha}...")
        fullTree = await fetch_github_repo_tree(owner, repo, repo_details.sha)

        logger.info("Step 5: Filtering tree in memory...")
        filteredTree = self._filterTree(fullTree)

        logger.info("Step 6: Inserting folder structure into DB...")
        await self._insertFolders(filteredTree, branchId, None)

        logger.info("Step 7: Fetching and summarizing files in parallel...")
        await self._fetchAndInsertFiles(filteredTree)

        logger.info("Step 8: Summarizing folders bottom-up...")
        await self._summarizeFolders(filteredTree)

        logger.success(f"Done! Inserted and summarized repository {owner}/{repo} successfully.")
        return repositoryData

    def _filterTree(self, tree: RepoTreeResult) -> RepoTreeResult:
        logger.info(f'Filtering tree at path "{tree.path or "/"}"...')

        # 1) Filter files
        allowed_files = whitelisted_file(tree.files, whitelisted_filter)
        allowed_files = blacklisted_files(allowed_files, blacklisted_file)

        # 2) Filter subfolders
        allowed_subdirs = blacklisted_folder(tree.subdirectories, blacklisted_filter)

        # Recursively prune
        pruned_subdirs = []
        for subdir in allowed_subdirs:
            filtered_subdir = self._filterTree(subdir)
            # remove subdirs that contain no files or child subfolders
            if filtered_subdir.files or filtered_subdir.subdirectories:
                pruned_subdirs.append(filtered_subdir)

        return RepoTreeResult(
            path=tree.path,
            files=allowed_files,
            subdirectories=pruned_subdirs
        )

    async def _insertFolders(
            self,
            tree: RepoTreeResult,
            branch_id: int,
            parent_folder_id: Optional[int]
    ):
        folder_name = tree.path.split("/")[-1] if tree.path else ""  # root => ""
        folder_path = tree.path

        logger.info(f'\tInserting folder "{folder_name}" with path "{folder_path}"...')
        folderData = await self.folder.insert(folder_name, folder_path, branch_id, parent_folder_id)

        self.folderPathMap[folder_path] = folderData.folder_id

        # Recurse
        for subdir in tree.subdirectories:
            await self._insertFolders(subdir, branch_id, folderData.folder_id)

    async def _fetchAndInsertFiles(self, rootTree: RepoTreeResult):
        # 1) gather all file paths
        all_file_paths = []

        def gather_files(t: RepoTreeResult):
            all_file_paths.extend(t.files)
            for s in t.subdirectories:
                gather_files(s)

        gather_files(rootTree)
        logger.success(f"\tFound {len(all_file_paths)} files to process...")

        # 2) fetch file contents in parallel
        logger.info(f"\tFetching file contents in parallel...")

        async def fetch_content(fp: str):
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

        # 3) Summarize each file
        logger.info(f"\tGenerating summaries for files...")

        async def summarize_file(file_path: str, content: Optional[str]):
            if not content:
                return None
            aiSummary = None
            retries = 0
            wordDeduction = 0
            reducedContent = content

            while not aiSummary and retries < TokenProcessingConfig.get('maxRetries'):
                try:
                    # Simple approach: slice the content to fit the limit
                    slice_size = TokenProcessingConfig.get('characterLimit') - wordDeduction
                    reducedContent = content[: max(0, slice_size)]
                    if self.repoFileInfo is None:
                        logger.error("ERROR! repoFileInfo is empty!")
                        continue
                    aiSummary = await self.codeProcessor.generate(reducedContent, {
                        "path": file_path,
                        **(self.repoFileInfo or {})
                    })
                except Exception as e:
                    logger.error(f"\t[Retry {retries + 1}] Failed generating summary for {file_path}")
                finally:
                    retries += 1
                    wordDeduction += TokenProcessingConfig.get('reduceCharPerRetry')

            return {
                "filePath": file_path,
                "content": content,
                "aiSummary": aiSummary
            }

        summarize_coros = [summarize_file(fp, ct) for fp, ct in fetched_files]
        processed_files = await asyncio.gather(*summarize_coros)

        # 4) Insert file records in DB
        logger.info(f"\tInserting summarized files into DB...")
        for f in processed_files:
            if not f or not f["aiSummary"]:
                continue

            file_path = f["filePath"]
            folder_path = file_path.rpartition("/")[0]
            # root-level file => folder_path == ""
            folder_id = self.folderPathMap.get(folder_path, None)
            if folder_id is None:
                logger.critical(f"\tNo folder found for path: '{folder_path}' (file: '{file_path}')")
                continue

            file_name = file_path.split("/")[-1]
            logger.info(f'\t\tInserting file "{file_name}" (path: "{file_path}")...')
            await self.file.insert(
                file_name,
                folder_id,
                f["content"],
                f["aiSummary"].summary,
                f["aiSummary"].usage
            )

    async def _summarizeFolders(self, tree: RepoTreeResult) -> Optional[str]:
        logger.info(f'Summarizing folder "{tree.path or "/"}"...')

        # 1) Summarize subfolders first
        subfolders_summaries: List[str] = []
        for subdir in tree.subdirectories:
            child_summary = await self._summarizeFolders(subdir)
            if child_summary:
                subfolders_summaries.append(f"Summary of folder {subdir.path}:\n{child_summary}\n")

        # 2) Gather file summaries from DB
        folder_id = self.folderPathMap.get(tree.path, None)
        if folder_id is None:
            logger.critical(f"\tNo folder ID found for path: '{tree.path}'")
            return None

        files_in_folder = await self.file.select(folder_id)
        file_summaries = [
            f"Summary of file {f.name}:\n{f.ai_summary}\n"
            for f in files_in_folder
            if f.ai_summary
        ]

        if not subfolders_summaries and not file_summaries:
            logger.error(f'\tNo summaries found in folder "{tree.path}". Skipping...')
            return None

        # 3) Combine
        all_summaries = subfolders_summaries + file_summaries
        combined = "\n\n".join(all_summaries)

        # 4) Summarize with folderProcessor
        aiSummary = None
        retries = 0
        summaryDeduction = 0

        while not aiSummary and retries < TokenProcessingConfig.get('maxRetries'):
            try:
                slice_size = TokenProcessingConfig.get('characterLimit') - summaryDeduction
                reduced = combined[: max(0, slice_size)]
                aiSummary = await self.folderProcessor.generate([reduced], {
                    "path": tree.path,
                    **(self.repoFileInfo or {})
                })
            except Exception:
                logger.warning(f"\t[Retry {retries + 1}] Failed to summarize folder '{tree.path}'")
            finally:
                retries += 1
                summaryDeduction += TokenProcessingConfig.get('reduceCharPerRetry')

        if not aiSummary:
            logger.warning(f"\tNo AI summary produced for folder '{tree.path}' after max retries.")
            return None

        # 5) Store in DB
        logger.info(f"\tStoring AI summary for folder '{tree.path}'...")
        await self.folder.update(aiSummary.summary, aiSummary.usage, folder_id)

        return aiSummary.summary
