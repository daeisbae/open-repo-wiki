"""Fetch repository tree stage.

This stage fetches the complete file tree from GitHub.

Requirements: 5.3
"""

import logging
from dataclasses import dataclass

from botocore.exceptions import ClientError

from shared.models import JobStage
from shared.storage.dynamodb import DynamoDBClient
from shared.github.client import GitHubClient, GitHubAPIError, TreeResult


logger = logging.getLogger(__name__)


class FetchTreeError(Exception):
    """Error during fetch tree stage."""
    pass


@dataclass
class FetchTreeResult:
    """Result of the fetch tree stage."""
    tree: TreeResult
    total_items: int
    truncated: bool


class FetchTreeStage:
    """Stage for fetching the repository file tree from GitHub.
    
    This stage:
    1. Fetches the complete file tree from GitHub API
    2. Updates job stage to FETCH_TREE
    
    Requirements: 5.3
    """

    def __init__(
        self,
        github_client: GitHubClient,
        dynamodb_client: DynamoDBClient,
        job_id: str,
    ):
        """Initialize the fetch tree stage.
        
        Args:
            github_client: GitHub API client for fetching tree.
            dynamodb_client: DynamoDB client for progress updates.
            job_id: Job identifier for progress updates.
        """
        self.github = github_client
        self.dynamodb = dynamodb_client
        self.job_id = job_id

    async def execute(
        self,
        repo_owner: str,
        repo_name: str,
        sha: str,
    ) -> FetchTreeResult:
        """Execute the fetch tree stage.
        
        Fetches the complete repository tree from GitHub.
        
        Args:
            repo_owner: Repository owner (user or organization).
            repo_name: Repository name.
            sha: Commit or tree SHA to fetch.
            
        Returns:
            FetchTreeResult with the tree data.
            
        Raises:
            FetchTreeError: If fetching fails.
            
        Requirements: 5.3
        """
        repo_id = f"{repo_owner}/{repo_name}"
        logger.info(f"Stage: FETCH_TREE - Fetching repository tree for {repo_id}")
        
        # Update job progress
        self._update_progress("Fetching repository tree...")
        
        try:
            # Fetch the complete tree from GitHub
            tree_result = await self.github.fetch_repo_tree(
                repo_owner,
                repo_name,
                sha,
                recursive=True,
            )
            
            total_items = len(tree_result.items)
            logger.info(
                f"Tree fetched: {total_items} items, truncated={tree_result.truncated}"
            )
            
            if tree_result.truncated:
                logger.warning(
                    "Tree was truncated by GitHub API - some files may be missing"
                )
            
            return FetchTreeResult(
                tree=tree_result,
                total_items=total_items,
                truncated=tree_result.truncated,
            )
            
        except GitHubAPIError as e:
            error_msg = f"Failed to fetch repository tree: {e.message}"
            logger.error(error_msg)
            raise FetchTreeError(error_msg) from e

    def _update_progress(self, message: str) -> None:
        """Update job progress in DynamoDB.
        
        Args:
            message: Progress message.
        """
        try:
            self.dynamodb.update_job_progress(
                job_id=self.job_id,
                stage=JobStage.FETCH_TREE,
                message=message,
            )
        except ClientError as e:
            logger.warning(f"Failed to update job progress: {e}")
