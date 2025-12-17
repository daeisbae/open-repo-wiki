"""Fetch repository details stage.

This stage fetches repository metadata from GitHub and stores
repo and branch records in DynamoDB.

Requirements: 5.1, 5.2
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from botocore.exceptions import ClientError

from shared.models import Repo, Branch, JobStage
from shared.storage.dynamodb import DynamoDBClient
from shared.github.client import GitHubClient, GitHubAPIError, RepoDetails


logger = logging.getLogger(__name__)


class FetchDetailsError(Exception):
    """Error during fetch details stage."""
    pass


@dataclass
class FetchDetailsResult:
    """Result of the fetch details stage."""
    repo_details: RepoDetails
    branch: str
    repo_id: str


class FetchDetailsStage:
    """Stage for fetching repository details from GitHub.
    
    This stage:
    1. Fetches repository metadata from GitHub API
    2. Stores repository record in DynamoDB
    3. Stores branch record in DynamoDB
    4. Updates job stage to FETCH_DETAILS
    
    Requirements: 5.1, 5.2
    """

    def __init__(
        self,
        github_client: GitHubClient,
        dynamodb_client: DynamoDBClient,
        job_id: str,
    ):
        """Initialize the fetch details stage.
        
        Args:
            github_client: GitHub API client for fetching repo details.
            dynamodb_client: DynamoDB client for storing records.
            job_id: Job identifier for progress updates.
        """
        self.github = github_client
        self.dynamodb = dynamodb_client
        self.job_id = job_id

    async def execute(
        self,
        repo_owner: str,
        repo_name: str,
        branch: Optional[str] = None,
    ) -> FetchDetailsResult:
        """Execute the fetch details stage.
        
        Fetches repository metadata from GitHub and stores repo/branch
        records in DynamoDB.
        
        Args:
            repo_owner: Repository owner (user or organization).
            repo_name: Repository name.
            branch: Optional branch name. If not provided, uses default branch.
            
        Returns:
            FetchDetailsResult with repo details and resolved branch name.
            
        Raises:
            FetchDetailsError: If fetching or storing fails.
            
        Requirements: 5.1, 5.2
        """
        repo_id = f"{repo_owner}/{repo_name}"
        logger.info(f"Stage: FETCH_DETAILS - Fetching repository details for {repo_id}")
        
        # Update job progress
        self._update_progress("Fetching repository details...")
        
        try:
            # Fetch repository details from GitHub
            repo_details = await self.github.fetch_repo_details(repo_owner, repo_name)
            
            # Use configured branch or default branch
            resolved_branch = branch or repo_details.default_branch
            
            logger.info(
                f"Repository details fetched: {repo_details.name}, "
                f"branch={resolved_branch}, stars={repo_details.stars}"
            )
            
            # Store repository record in DynamoDB
            await asyncio.to_thread(self._store_repo, repo_id, repo_details)
            
            # Store branch record in DynamoDB
            await asyncio.to_thread(self._store_branch, repo_id, resolved_branch, repo_details)
            
            return FetchDetailsResult(
                repo_details=repo_details,
                branch=resolved_branch,
                repo_id=repo_id,
            )
            
        except GitHubAPIError as e:
            error_msg = f"Failed to fetch repository details: {e.message}"
            logger.error(error_msg)
            raise FetchDetailsError(error_msg) from e
        except ClientError as e:
            error_msg = f"Failed to store repository data in DynamoDB: {e}"
            logger.error(error_msg)
            raise FetchDetailsError(error_msg) from e

    def _store_repo(self, repo_id: str, repo_details: RepoDetails) -> None:
        """Store repository record in DynamoDB.
        
        Args:
            repo_id: Repository identifier (owner/name).
            repo_details: Repository details from GitHub.
            
        Requirements: 2.2
        """
        repo = Repo(
            repo_id=repo_id,
            owner=repo_details.owner,
            name=repo_details.name,
            default_branch=repo_details.default_branch,
            stars=repo_details.stars,
            forks=repo_details.forks,
            language=repo_details.language,
            github_url=repo_details.url,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.dynamodb.put_repo(repo)
        logger.debug(f"Stored repository record: {repo_id}")

    def _store_branch(
        self,
        repo_id: str,
        branch_name: str,
        repo_details: RepoDetails,
    ) -> None:
        """Store branch record in DynamoDB.
        
        Args:
            repo_id: Repository identifier (owner/name).
            branch_name: Branch name.
            repo_details: Repository details containing commit info.
            
        Requirements: 2.3
        """
        branch = Branch(
            repo_id=repo_id,
            branch_name=branch_name,
            last_commit_sha=repo_details.sha,
            commit_at=repo_details.commit_at.isoformat(),
        )
        self.dynamodb.put_branch(branch)
        logger.debug(f"Stored branch record: {repo_id}/{branch_name}")

    def _update_progress(self, message: str) -> None:
        """Update job progress in DynamoDB.
        
        Args:
            message: Progress message.
        """
        try:
            self.dynamodb.update_job_progress(
                job_id=self.job_id,
                stage=JobStage.FETCH_DETAILS,
                message=message,
            )
        except ClientError as e:
            logger.warning(f"Failed to update job progress: {e}")
