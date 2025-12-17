"""Summarization stage for files and folders.

This stage generates AI summaries for files and folders using LLM,
stores tree nodes in DynamoDB, and writes summaries to S3.

Ported from src/wiki_app/services.py for the AWS serverless architecture.

Requirements: 5.6, 5.7, 6.1, 6.2
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable

from botocore.exceptions import ClientError

from shared.models import JobStage, TreeNode, NodeType
from shared.storage.dynamodb import DynamoDBClient
from shared.storage.s3 import S3Client
from shared.github.client import GitHubClient, TreeResult, TreeItem

# Import LLM integration
from services.processor.llm import (
    LLMProvider,
    CodeProcessor,
    FolderProcessor,
    RepoInfo,
    FileSchema,
    FolderSchema,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configuration for token processing
TOKEN_PROCESSING_CONFIG = {
    "character_limit": 50000,
    "reduce_char_per_retry": 10000,
    "max_retries": 3,
}

# Progress update interval (every N files/folders)
PROGRESS_UPDATE_INTERVAL = 1


class SummarizeError(Exception):
    """Error during summarization stage."""
    pass


@dataclass
class SummarizeResult:
    """Result of the summarization stage."""
    files_processed: int
    folders_processed: int
    folder_only_mode: bool


class SummarizeStage:
    """Stage for generating AI summaries for files and folders.
    
    This stage:
    1. In full mode: summarizes all files, then folders
    2. In folder-only mode: only summarizes folders
    3. Stores tree nodes in DynamoDB
    4. Writes large summaries to S3
    5. Updates job progress periodically
    
    Requirements: 5.6, 5.7, 6.1, 6.2
    """

    def __init__(
        self,
        github_client: GitHubClient,
        dynamodb_client: DynamoDBClient,
        s3_client: S3Client,
        job_id: str,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """Initialize the summarization stage.
        
        Args:
            github_client: GitHub API client for fetching file content.
            dynamodb_client: DynamoDB client for storing tree nodes.
            s3_client: S3 client for storing large summaries.
            job_id: Job identifier for progress updates.
            llm_provider: LLM provider for generating summaries (optional).
        """
        self.github = github_client
        self.dynamodb = dynamodb_client
        self.s3 = s3_client
        self.job_id = job_id
        self.llm_provider = llm_provider
        
        # Initialize processors if LLM provider is available
        self.code_processor: Optional[CodeProcessor] = None
        self.folder_processor: Optional[FolderProcessor] = None
        if llm_provider:
            self.code_processor = CodeProcessor(llm_provider)
            self.folder_processor = FolderProcessor(llm_provider)
        
        # Semaphore to limit concurrent GitHub/LLM requests
        self.semaphore = asyncio.Semaphore(20)

    async def execute(
        self,
        repo_id: str,
        branch: str,
        filtered_tree: TreeResult,
        folder_only_mode: bool,
        repo_owner: str,
        repo_name: str,
        commit_sha: str,
    ) -> SummarizeResult:
        """Execute the summarization stage.
        
        Args:
            repo_id: Repository identifier (owner/name).
            branch: Branch name.
            filtered_tree: Filtered tree from previous stage.
            folder_only_mode: Whether to skip file summarization.
            repo_owner: Repository owner.
            repo_name: Repository name.
            commit_sha: Commit SHA for fetching files.
            
        Returns:
            SummarizeResult with processing statistics.
            
        Raises:
            SummarizeError: If summarization fails.
            
        Requirements: 5.6, 5.7
        """
        logger.info(f"Stage: SUMMARIZE - Processing {repo_id}")
        
        repo_info = {
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "commit_sha": commit_sha,
        }
        
        files_processed = 0
        folders_processed = 0
        
        try:
            # Separate files and folders
            files = [item for item in filtered_tree.items if item.type == "blob"]
            folders = [item for item in filtered_tree.items if item.type == "tree"]
            
            # Process files (full mode only)
            if not folder_only_mode:
                files_processed = await self._summarize_files(
                    repo_id, branch, files, repo_info
                )
            else:
                # In folder-only mode, still store file nodes without summaries
                files_processed = await self._store_file_nodes_only(
                    repo_id, branch, files
                )
                logger.info("Skipping file summarization (folder-only mode)")
            
            # Process folders
            folders_processed = await self._summarize_folders(
                repo_id, branch, folders, files, repo_info, folder_only_mode
            )
            
            return SummarizeResult(
                files_processed=files_processed,
                folders_processed=folders_processed,
                folder_only_mode=folder_only_mode,
            )
            
        except Exception as e:
            error_msg = f"Failed during summarization: {e}"
            logger.error(error_msg)
            raise SummarizeError(error_msg) from e

    async def _summarize_files(
        self,
        repo_id: str,
        branch: str,
        files: List[TreeItem],
        repo_info: Dict[str, str],
    ) -> int:
        """Summarize all files in three phases: Fetch, Summarize, Store.
        
        Args:
            repo_id: Repository identifier.
            branch: Branch name.
            files: List of file TreeItems.
            repo_info: Repository info for LLM context.
            
        Returns:
            Number of files processed.
            
        Requirements: 5.6
        """
        total_files = len(files)
        logger.info(f"Stage: SUMMARIZE_FILES - Processing {total_files} files")
        
        # --- PHASE 1: FETCH ALL ---
        await self._update_progress(JobStage.SUMMARIZE_FILES, 0, total_files, "Fetching all files...")
        
        fetch_tasks = []
        for file_item in files:
            fetch_tasks.append(asyncio.create_task(self._fetch_content_safe(repo_info, file_item)))
            
        fetched_data = []
        completed_fetches = 0
        
        for future in asyncio.as_completed(fetch_tasks):
            result = await future
            fetched_data.append(result)
            completed_fetches += 1
            
            if completed_fetches % 5 == 0 or completed_fetches == total_files:
                await self._update_progress(
                    JobStage.SUMMARIZE_FILES,
                    completed_fetches,
                    total_files,
                    f"Fetched {completed_fetches}/{total_files} files",
                )

        # Filter valid fetches
        valid_fetches = [d for d in fetched_data if d[1] is not None]
        
        # --- PHASE 2: SUMMARIZE ALL ---
        await self._update_progress(JobStage.SUMMARIZE_FILES, 0, total_files, "Summarizing all files...")
        
        summary_tasks = []
        for file_item, content in valid_fetches:
            summary_tasks.append(asyncio.create_task(self._generate_summary_safe(content, file_item, repo_info)))
            
        summary_results = []
        completed_summaries = 0
        total_summaries = len(summary_tasks)
        
        t_store_start = time.time()
        nodes_to_store = []
        
        if total_summaries > 0:
            for future in asyncio.as_completed(summary_tasks):
                file_item, summary = await future
                completed_summaries += 1
                
                # --- INCREMENTAL STORAGE ---
                # Determine summary_ref
                summary_ref = None
                if summary:
                    if len(summary) > 4000:
                        # Store in S3 immediately
                        await asyncio.to_thread(
                            self.s3.put_page, repo_id, branch, file_item.path, summary
                        )
                        summary_ref = self.s3.generate_page_key(repo_id, branch, file_item.path)
                    else:
                        summary_ref = summary
                
                # Create node
                parent_path = "/".join(file_item.path.split("/")[:-1])
                node = TreeNode(
                    repo_id=repo_id,
                    branch=branch,
                    path=file_item.path,
                    node_type=NodeType.FILE,
                    parent_path=parent_path,
                    name=file_item.path.split("/")[-1],
                    sha=file_item.sha,
                    size=file_item.size,
                    summary_ref=summary_ref,
                )
                
                # Store node in DynamoDB
                # Note: We still use single put_node here for simplicity in incremental mode, 
                # or we could batch them. Let's batch every 5 for efficiency but still frequent.
                nodes_to_store.append(node)
                if len(nodes_to_store) >= 5 or completed_summaries == total_summaries:
                    await asyncio.to_thread(self.dynamodb.put_nodes_batch, nodes_to_store)
                    nodes_to_store = []
                
                if completed_summaries % 1 == 0: # Update every file for responsiveness
                    msg = f"Summarized {completed_summaries}/{total_summaries} files"
                    logger.info(msg)
                    await self._update_progress(
                        JobStage.SUMMARIZE_FILES,
                        completed_summaries,
                        total_files,
                        msg,
                    )
        
        logger.info(f"File summarization and storage complete: {completed_summaries} files processed")
        return completed_summaries

    async def _fetch_content_safe(self, repo_info, file_item):
        """Helper to fetch content with error handling."""
        async with self.semaphore:
            try:
                t0 = time.time()
                content = await self.github.fetch_file(
                    repo_info["repo_owner"],
                    repo_info["repo_name"],
                    repo_info["commit_sha"],
                    file_item.path,
                )
                logger.debug(f"Fetched {file_item.path} in {time.time() - t0:.2f}s")
                return (file_item, content)
            except Exception as e:
                logger.warning(f"Failed to fetch file {file_item.path}: {e}")
                return (file_item, None)

    async def _generate_summary_safe(self, content, file_item, repo_info):
        """Helper to generate summary with error handling."""
        async with self.semaphore:
            try:
                summary = None
                if self.llm_provider:
                    t0 = time.time()
                    summary = await self._generate_file_summary(
                        content, file_item.path, repo_info
                    )
                    logger.info(f"Summarized {file_item.path} in {time.time() - t0:.2f}s")
                return (file_item, summary)
            except Exception as e:
                logger.warning(f"Failed to summarize file {file_item.path}: {e}")
                return (file_item, None)



    async def _generate_file_summary(
        self,
        content: str,
        path: str,
        repo_info: Dict[str, str],
    ) -> Optional[str]:
        """Generate AI summary for a file.
        
        Args:
            content: File content.
            path: File path.
            repo_info: Repository info for context.
            
        Returns:
            Generated summary or None if failed.
            
        Requirements: 5.6
        """
        if not self.code_processor:
            return None
        
        retries = 0
        char_deduction = 0
        
        while retries < TOKEN_PROCESSING_CONFIG["max_retries"]:
            try:
                slice_size = TOKEN_PROCESSING_CONFIG["character_limit"] - char_deduction
                reduced_content = content[:max(0, slice_size)]
                
                # Create RepoInfo for the processor
                info = RepoInfo(
                    repo_owner=repo_info["repo_owner"],
                    repo_name=repo_info["repo_name"],
                    commit_sha=repo_info["commit_sha"],
                    path=path,
                )
                
                # Generate summary using CodeProcessor
                result: FileSchema = await self.code_processor.generate(reduced_content, info)
                
                # Format the summary with usage header
                summary = f"**{result.usage}**\n\n{result.summary}"
                return summary
                
            except Exception as e:
                logger.warning(f"LLM call failed for {path}: {e}")
            
            retries += 1
            char_deduction += TOKEN_PROCESSING_CONFIG["reduce_char_per_retry"]
        
        return None

    async def _store_file_nodes_only(
        self,
        repo_id: str,
        branch: str,
        files: List[TreeItem],
    ) -> int:
        """Store file nodes without summaries (folder-only mode).
        
        Args:
            repo_id: Repository identifier.
            branch: Branch name.
            files: List of file TreeItems.
            
        Returns:
            Number of files stored.
        """
        logger.info(f"Storing {len(files)} file nodes (folder-only mode)")
        await self._update_progress(
            JobStage.SUMMARIZE_FILES,
            0,
            len(files),
            "Storing file metadata (folder-only mode)...",
        )
        
        nodes = []
        for file_item in files:
            parent_path = "/".join(file_item.path.split("/")[:-1])
            node = TreeNode(
                repo_id=repo_id,
                branch=branch,
                path=file_item.path,
                node_type=NodeType.FILE,
                parent_path=parent_path,
                name=file_item.path.split("/")[-1],
                sha=file_item.sha,
                size=file_item.size,
                summary_ref=None,  # No summary in folder-only mode
            )
            nodes.append(node)
        
        # Batch write nodes
        self.dynamodb.put_nodes_batch(nodes)
        
        await self._update_progress(
            JobStage.SUMMARIZE_FILES,
            len(files),
            len(files),
            f"Stored {len(files)} file nodes",
        )
        
        return len(files)

    async def _summarize_folders(
        self,
        repo_id: str,
        branch: str,
        folders: List[TreeItem],
        files: List[TreeItem],
        repo_info: Dict[str, str],
        folder_only_mode: bool,
    ) -> int:
        """Summarize all folders and store in DynamoDB/S3.
        
        Args:
            repo_id: Repository identifier.
            branch: Branch name.
            folders: List of folder TreeItems.
            files: List of file TreeItems (for building folder contents).
            repo_info: Repository info for LLM context.
            folder_only_mode: Whether in folder-only mode.
            
        Returns:
            Number of folders processed.
            
        Requirements: 5.7
        """
        logger.info(f"Stage: SUMMARIZE_FOLDERS - Processing {len(folders)} folders")
        await self._update_progress(
            JobStage.SUMMARIZE_FOLDERS,
            0,
            len(folders),
            "Summarizing folders...",
        )
        
        # Group folders by depth
        folders_by_depth: Dict[int, List[TreeItem]] = {}
        for folder in folders:
            depth = folder.path.count("/")
            if depth not in folders_by_depth:
                folders_by_depth[depth] = []
            folders_by_depth[depth].append(folder)
            
        # Process from deepest to shallowest
        sorted_depths = sorted(folders_by_depth.keys(), reverse=True)
        
        processed = 0
        
        for depth in sorted_depths:
            depth_folders = folders_by_depth[depth]
            tasks = []
            
            # Create tasks for this depth
            for folder_item in depth_folders:
                tasks.append(
                    self._process_folder(
                        repo_id, branch, folder_item, files, repo_info, folder_only_mode
                    )
                )
            
            # Process tasks concurrently for this depth
            for i, future in enumerate(asyncio.as_completed(tasks)):
                try:
                    await future
                    processed += 1
                except Exception as e:
                    # Log error but continue
                    logger.warning(f"Failed to process folder at depth {depth}: {e}")
                
                # Update progress periodically
                if (processed) % 1 == 0 or processed == len(folders):
                    await self._update_progress(
                        JobStage.SUMMARIZE_FOLDERS,
                        processed,
                        len(folders),
                        f"Processed {processed}/{len(folders)} folders",
                    )
        
        logger.info(f"Folder summarization complete: {processed} folders processed")
        return processed

    async def _process_folder(
        self,
        repo_id: str,
        branch: str,
        folder_item: TreeItem,
        files: List[TreeItem],
        repo_info: Dict[str, str],
        folder_only_mode: bool,
    ) -> None:
        """Process a single folder: gather child summaries, generate summary, store.
        
        Args:
            repo_id: Repository identifier.
            branch: Branch name.
            folder_item: Folder TreeItem.
            files: All file TreeItems.
            repo_info: Repository info for LLM context.
            folder_only_mode: Whether in folder-only mode.
        """
        # Get child file summaries from DynamoDB
        child_summaries = []
        
        if self.llm_provider:
            # Query child nodes (blocking call wrapped)
            child_nodes = await asyncio.to_thread(
                self.dynamodb.query_tree, repo_id, branch, folder_item.path
            )
            
            for child in child_nodes:
                if child.summary_ref:
                    # Fetch summary content
                    if child.summary_ref.startswith("repos/"):
                        # S3 reference (blocking call wrapped)
                        summary_content = await asyncio.to_thread(
                            self.s3.get_page, child.summary_ref
                        )
                    else:
                        # Inline summary
                        summary_content = child.summary_ref
                    
                    if summary_content:
                        child_summaries.append(
                            f"Summary of {child.node_type.value} {child.name}:\n{summary_content}"
                        )
        
        # Generate folder summary using LLM
        summary = None
        if child_summaries and self.llm_provider:
            summary = await self._generate_folder_summary(
                child_summaries, folder_item.path, repo_info
            )
        
        # Determine summary_ref
        summary_ref = None
        if summary:
            if len(summary) > 4000:
                # Store large summary in S3 (blocking call wrapped)
                summary_ref = await asyncio.to_thread(
                    self.s3.put_page, repo_id, branch, folder_item.path, summary
                )
            else:
                summary_ref = summary
        
        # Create and store tree node
        parent_path = "/".join(folder_item.path.split("/")[:-1])
        node = TreeNode(
            repo_id=repo_id,
            branch=branch,
            path=folder_item.path,
            node_type=NodeType.FOLDER,
            parent_path=parent_path,
            name=folder_item.path.split("/")[-1],
            sha=folder_item.sha,
            summary_ref=summary_ref,
        )
        # Store in DynamoDB (blocking call wrapped)
        await asyncio.to_thread(self.dynamodb.put_node, node)

    async def _generate_folder_summary(
        self,
        child_summaries: List[str],
        path: str,
        repo_info: Dict[str, str],
    ) -> Optional[str]:
        """Generate AI summary for a folder.
        
        Args:
            child_summaries: Summaries of child files/folders.
            path: Folder path.
            repo_info: Repository info for context.
            
        Returns:
            Generated summary or None if failed.
            
        Requirements: 5.7
        """
        if not self.folder_processor:
            return None
        
        retries = 0
        char_deduction = 0
        
        while retries < TOKEN_PROCESSING_CONFIG["max_retries"]:
            try:
                # Reduce summaries if needed
                slice_size = TOKEN_PROCESSING_CONFIG["character_limit"] - char_deduction
                combined = "\n\n".join(child_summaries)
                if len(combined) > slice_size:
                    # Truncate individual summaries proportionally
                    max_per_summary = slice_size // max(len(child_summaries), 1)
                    reduced_summaries = [s[:max_per_summary] for s in child_summaries]
                else:
                    reduced_summaries = child_summaries
                
                # Create RepoInfo for the processor
                info = RepoInfo(
                    repo_owner=repo_info["repo_owner"],
                    repo_name=repo_info["repo_name"],
                    commit_sha=repo_info["commit_sha"],
                    path=path,
                )
                
                # Generate summary using FolderProcessor
                result: FolderSchema = await self.folder_processor.generate(reduced_summaries, info)
                
                # Format the summary with usage header and dependency graph
                summary_parts = [f"**{result.usage}**\n\n{result.summary}"]
                
                if result.dependency_graph:
                    summary_parts.append(f"\n\n## Dependency Graph\n\n```mermaid\n{result.dependency_graph}\n```")
                
                return "".join(summary_parts)
                
            except Exception as e:
                logger.warning(f"LLM call failed for folder {path}: {e}")
            
            retries += 1
            char_deduction += TOKEN_PROCESSING_CONFIG["reduce_char_per_retry"]
        
        return None

    async def _update_progress(
        self,
        stage: JobStage,
        processed: int,
        total: int,
        message: str,
    ) -> None:
        """Update job progress in DynamoDB.
        
        Args:
            stage: Current processing stage.
            processed: Number of items processed.
            total: Total number of items.
            message: Progress message.
            
        Requirements: 6.1, 6.2
        """
        try:
            await asyncio.to_thread(
                self.dynamodb.update_job_progress,
                job_id=self.job_id,
                stage=stage,
                processed=processed,
                total=total,
                message=message,
            )
        except Exception as e:
            logger.warning(f"Failed to update job progress: {e}")
