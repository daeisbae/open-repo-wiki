"""Main processor entry point for ECS Fargate task.

This module contains the RepositoryProcessor class that orchestrates the
complete repository processing pipeline:
1. Fetch repository details from GitHub
2. Fetch repository tree
3. Filter tree using whitelist/blacklist rules
4. Summarize files and folders using LLM
5. Finalize and update job status

The processor receives configuration via environment variables and uses
Step Functions callback pattern to signal completion.

Requirements: 4.4, 4.5, 4.6
"""

import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from shared.models import Job, JobStatus, JobStage, Repo, Branch, TreeNode, NodeType
from shared.storage.dynamodb import DynamoDBClient
from shared.storage.s3 import S3Client
from shared.github.client import GitHubClient, GitHubAPIError, RepoDetails, TreeResult
from shared.github.filter import filter_tree, count_filtered_files

# Import LLM integration
from services.processor.llm import LLMFactory, LLMConfig, LLMProvider
from services.processor.stages.summarize import SummarizeStage, SummarizeError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ProcessorError(Exception):
    """Base exception for processor errors."""

    def __init__(self, stage: str, message: str):
        self.stage = stage
        self.message = message
        super().__init__(f"[{stage}] {message}")


class GitHubFetchError(ProcessorError):
    """GitHub API failures (rate limit, not found, etc.)."""
    pass


class StorageError(ProcessorError):
    """DynamoDB or S3 failures."""
    pass


class LLMError(ProcessorError):
    """LLM provider failures."""
    pass


class FileLimitExceededError(ProcessorError):
    """File count exceeds configured limit for automatic summarization."""
    pass


@dataclass
class ProcessorConfig:
    """Configuration for the repository processor.
    
    All values are read from environment variables passed by ECS task definition.
    
    Requirements: 4.4
    """
    repo_owner: str
    repo_name: str
    branch: Optional[str]
    job_id: str
    task_token: str
    ddb_main_table: str
    ddb_jobs_table: str
    s3_bucket: str
    github_token: str
    aws_region: str
    max_file_limit: int

    @classmethod
    def from_environment(cls) -> "ProcessorConfig":
        """Create configuration from environment variables.
        
        Required environment variables:
        - REPO_OWNER: Repository owner (user or organization)
        - REPO_NAME: Repository name
        - JOB_ID: Unique job identifier
        - TASK_TOKEN: Step Functions callback token
        - DDB_MAIN_TABLE: DynamoDB main table name
        - DDB_JOBS_TABLE: DynamoDB jobs table name
        - S3_BUCKET: S3 artifacts bucket name
        - GITHUB_TOKEN: GitHub personal access token
        
        Optional environment variables:
        - BRANCH: Branch to process (defaults to repo's default branch)
        - AWS_REGION: AWS region (default: us-east-1)
        
        Raises:
            ValueError: If required environment variables are missing.
        """
        required_vars = [
            "REPO_OWNER",
            "REPO_NAME", 
            "JOB_ID",
            "TASK_TOKEN",
            "DDB_MAIN_TABLE",
            "DDB_JOBS_TABLE",
            "S3_BUCKET",
            "GITHUB_TOKEN",
        ]
        
        missing = [var for var in required_vars if not os.environ.get(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return cls(
            repo_owner=os.environ["REPO_OWNER"],
            repo_name=os.environ["REPO_NAME"],
            branch=os.environ.get("BRANCH"),
            job_id=os.environ["JOB_ID"],
            task_token=os.environ["TASK_TOKEN"],
            ddb_main_table=os.environ["DDB_MAIN_TABLE"],
            ddb_jobs_table=os.environ["DDB_JOBS_TABLE"],
            s3_bucket=os.environ["S3_BUCKET"],
            github_token=os.environ["GITHUB_TOKEN"],
            aws_region=os.environ.get("AWS_REGION", "us-east-1"),
            max_file_limit=int(os.environ.get("MAX_FILE_LIMIT", "1000")),
        )


class RepositoryProcessor:
    """Main processor orchestrating the repository processing pipeline.
    
    This class coordinates all stages of repository processing:
    1. FETCH_DETAILS: Fetch repository metadata from GitHub
    2. FETCH_TREE: Fetch complete file tree from GitHub
    3. FILTER: Apply whitelist/blacklist filters
    4. SUMMARIZE_FILES: Generate file summaries (full mode only)
    5. SUMMARIZE_FOLDERS: Generate folder summaries
    6. FINALIZE: Update job status to SUCCEEDED
    
    The processor uses Step Functions callback pattern to signal completion
    via SendTaskSuccess or SendTaskFailure.
    
    Requirements: 4.4, 4.5, 4.6
    """

    def __init__(self, config: ProcessorConfig):
        """Initialize the processor with configuration.
        
        Args:
            config: ProcessorConfig with all required settings.
        """
        self.config = config
        self.repo_id = f"{config.repo_owner}/{config.repo_name}"
        
        # Initialize clients
        self.dynamodb = DynamoDBClient(
            main_table_name=config.ddb_main_table,
            jobs_table_name=config.ddb_jobs_table,
            region_name=config.aws_region,
        )
        self.s3 = S3Client(
            bucket_name=config.s3_bucket,
            region_name=config.aws_region,
        )
        self.github = GitHubClient(token=config.github_token)
        
        # Step Functions client for callback
        self.sfn_client = boto3.client(
            "stepfunctions",
            region_name=config.aws_region,
        )
        
        # Initialize LLM provider (optional - may not be configured)
        self.llm_provider: Optional[LLMProvider] = self._init_llm_provider()
        
        # Processing state
        self.repo_details: Optional[RepoDetails] = None
        self.tree_result: Optional[TreeResult] = None
        self.filtered_tree: Optional[TreeResult] = None
        self.branch: Optional[str] = None

    def _init_llm_provider(self) -> Optional[LLMProvider]:
        """Initialize the LLM provider from environment variables.
        
        Returns:
            LLMProvider instance if configured, None otherwise.
        """
        try:
            llm_config = LLMConfig(
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                max_tokens=4096,
            )
            provider = LLMFactory.create_from_env(llm_config)
            if provider:
                logger.info(f"LLM provider initialized: {type(provider).__name__}")
            else:
                logger.warning("LLM provider not configured - summaries will be skipped")
            return provider
        except Exception as e:
            logger.warning(f"Failed to initialize LLM provider: {e}")
            return None

    async def run(self) -> None:
        """Execute the full processing pipeline.
        
        This method orchestrates all processing stages and handles
        success/failure signaling to Step Functions.
        
        Requirements: 4.5, 4.6
        """
        try:
            logger.info(f"Starting processing for {self.repo_id}, job_id={self.config.job_id}")
            
            # Update job status to RUNNING
            self._update_job_status(JobStatus.RUNNING)
            
            # Execute pipeline stages
            await self._fetch_details()
            await self._fetch_tree()
            await self._filter_tree()
            await self._summarize()
            await self._finalize()
            
            # Signal success to Step Functions
            self._send_task_success()
            logger.info(f"Processing completed successfully for {self.repo_id}")
            
        except ProcessorError as e:
            logger.error(f"Processing failed at stage {e.stage}: {e.message}")
            self._update_job_failed(str(e))
            self._send_task_failure(e.stage, str(e))
            
        except Exception as e:
            logger.exception(f"Unexpected error during processing: {e}")
            self._update_job_failed(str(e))
            self._send_task_failure("UNKNOWN", str(e))
            
        finally:
            # Clean up GitHub client
            await self.github.close()

    async def _fetch_details(self) -> None:
        """Fetch repository details from GitHub.
        
        Updates job stage to FETCH_DETAILS and retrieves repository metadata
        including owner, name, default_branch, stars, forks, language, and github_url.
        
        Requirements: 5.1, 5.2
        """
        logger.info(f"Stage: FETCH_DETAILS - Fetching repository details for {self.repo_id}")
        self._update_job_progress(JobStage.FETCH_DETAILS, message="Fetching repository details...")
        
        try:
            self.repo_details = await self.github.fetch_repo_details(
                self.config.repo_owner,
                self.config.repo_name,
            )
            
            # Use configured branch or default branch
            self.branch = self.config.branch or self.repo_details.default_branch
            
            # Store repository record in DynamoDB
            repo = Repo(
                repo_id=self.repo_id,
                owner=self.repo_details.owner,
                name=self.repo_details.name,
                default_branch=self.repo_details.default_branch,
                stars=self.repo_details.stars,
                forks=self.repo_details.forks,
                language=self.repo_details.language,
                github_url=self.repo_details.url,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            self.dynamodb.put_repo(repo)
            
            # Store branch record
            branch = Branch(
                repo_id=self.repo_id,
                branch_name=self.branch,
                last_commit_sha=self.repo_details.sha,
                commit_at=self.repo_details.commit_at.isoformat(),
            )
            self.dynamodb.put_branch(branch)
            
            logger.info(f"Repository details fetched: {self.repo_details.name}, branch={self.branch}")
            
        except GitHubAPIError as e:
            raise GitHubFetchError("FETCH_DETAILS", f"Failed to fetch repository: {e.message}")
        except ClientError as e:
            raise StorageError("FETCH_DETAILS", f"Failed to store repository data: {e}")

    async def _fetch_tree(self) -> None:
        """Fetch the complete repository tree from GitHub.
        
        Updates job stage to FETCH_TREE and retrieves the full file tree.
        
        Requirements: 5.3
        """
        logger.info(f"Stage: FETCH_TREE - Fetching repository tree for {self.repo_id}")
        self._update_job_progress(JobStage.FETCH_TREE, message="Fetching repository tree...")
        
        try:
            self.tree_result = await self.github.fetch_repo_tree(
                self.config.repo_owner,
                self.config.repo_name,
                self.repo_details.sha,
                recursive=True,
            )
            
            total_items = len(self.tree_result.items)
            logger.info(f"Tree fetched: {total_items} items, truncated={self.tree_result.truncated}")
            
            if self.tree_result.truncated:
                logger.warning("Tree was truncated by GitHub API - some files may be missing")
                
        except GitHubAPIError as e:
            raise GitHubFetchError("FETCH_TREE", f"Failed to fetch tree: {e.message}")

    async def _filter_tree(self) -> None:
        """Apply whitelist/blacklist filters to the tree.
        
        Updates job stage to FILTER and applies filtering rules.
        Determines if folder-only mode should be used based on file count.
        
        Requirements: 5.4, 5.5
        """
        logger.info(f"Stage: FILTER - Filtering repository tree for {self.repo_id}")
        self._update_job_progress(JobStage.FILTER, message="Filtering repository tree...")
        
        # Apply filters
        self.filtered_tree = filter_tree(self.tree_result)
        
        # Count filtered files
        file_count = count_filtered_files(self.filtered_tree)
        
        # Check file limit before starting summarization
        if file_count > self.config.max_file_limit:
            error_msg = (
                f"Repository has {file_count} files which exceeds the limit of "
                f"{self.config.max_file_limit}. Huge repository summarization is "
                f"only done through manual request for now."
            )
            logger.warning(error_msg)
            raise FileLimitExceededError("FILTER", error_msg)
        
        logger.info(f"Filtering complete: {file_count} files")
        
        # Update job with total count
        self._update_job_progress(
            JobStage.FILTER,
            total=file_count,
            message=f"Found {file_count} files to process",
        )

    async def _summarize(self) -> None:
        """Generate summaries for files and folders.
        
        Uses the SummarizeStage to process files and folders with LLM.
        Always summarizes all files first, then folders.
        
        Requirements: 5.6, 5.7
        """
        logger.info(f"Stage: SUMMARIZE - Starting summarization for {self.repo_id}")
        
        # Create the summarize stage
        summarize_stage = SummarizeStage(
            github_client=self.github,
            dynamodb_client=self.dynamodb,
            s3_client=self.s3,
            job_id=self.config.job_id,
            llm_provider=self.llm_provider,
        )
        
        try:
            # Execute summarization
            result = await summarize_stage.execute(
                repo_id=self.repo_id,
                branch=self.branch,
                filtered_tree=self.filtered_tree,
                repo_owner=self.config.repo_owner,
                repo_name=self.config.repo_name,
                commit_sha=self.repo_details.sha,
            )
            
            logger.info(
                f"Summarization complete: {result.files_processed} files, "
                f"{result.folders_processed} folders"
            )
            
        except SummarizeError as e:
            raise LLMError("SUMMARIZE", str(e))

    async def _finalize(self) -> None:
        """Finalize processing and update job status.
        
        Updates job stage to FINALIZE and sets status to SUCCEEDED.
        
        Requirements: 5.8
        """
        logger.info(f"Stage: FINALIZE - Finalizing processing for {self.repo_id}")
        self._update_job_progress(JobStage.FINALIZE, message="Finalizing...")
        
        # Update job status to SUCCEEDED
        self._update_job_status(JobStatus.SUCCEEDED)
        
        logger.info(f"Processing finalized for {self.repo_id}")

    def _update_job_progress(
        self,
        stage: JobStage,
        processed: Optional[int] = None,
        total: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        """Update job progress in DynamoDB.
        
        Args:
            stage: Current processing stage.
            processed: Number of items processed.
            total: Total number of items to process.
            message: Progress message.
            
        Requirements: 6.1, 6.2
        """
        try:
            self.dynamodb.update_job_progress(
                job_id=self.config.job_id,
                stage=stage,
                processed=processed,
                total=total,
                message=message,
            )
        except ClientError as e:
            logger.warning(f"Failed to update job progress: {e}")

    def _update_job_status(self, status: JobStatus) -> None:
        """Update job status in DynamoDB.
        
        Args:
            status: New job status.
        """
        try:
            self.dynamodb.update_job_status(
                job_id=self.config.job_id,
                status=status,
            )
        except ClientError as e:
            logger.warning(f"Failed to update job status: {e}")

    def _update_job_failed(self, error: str) -> None:
        """Update job status to FAILED with error message.
        
        Args:
            error: Error message describing the failure.
        """
        try:
            self.dynamodb.update_job_status(
                job_id=self.config.job_id,
                status=JobStatus.FAILED,
                error=error,
            )
        except ClientError as e:
            logger.warning(f"Failed to update job failure status: {e}")

    def _send_task_success(self) -> None:
        """Signal successful completion to Step Functions.
        
        Calls SendTaskSuccess with the task token to indicate
        the ECS task completed successfully.
        
        Requirements: 4.5
        """
        try:
            self.sfn_client.send_task_success(
                taskToken=self.config.task_token,
                output='{"status": "SUCCEEDED"}',
            )
            logger.info("SendTaskSuccess called successfully")
        except ClientError as e:
            logger.error(f"Failed to send task success: {e}")
            raise StorageError("FINALIZE", f"Failed to signal task success: {e}")

    def _send_task_failure(self, stage: str, error: str) -> None:
        """Signal failure to Step Functions.
        
        Calls SendTaskFailure with error details to indicate
        the ECS task failed.
        
        Args:
            stage: The stage where the failure occurred.
            error: Error message describing the failure.
            
        Requirements: 4.6
        """
        try:
            self.sfn_client.send_task_failure(
                taskToken=self.config.task_token,
                error=stage,
                cause=error[:256],  # Truncate to max allowed length
            )
            logger.info(f"SendTaskFailure called: stage={stage}")
        except ClientError as e:
            logger.error(f"Failed to send task failure: {e}")


async def main() -> int:
    """Main entry point for the processor.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Load configuration from environment
        config = ProcessorConfig.from_environment()
        
        # Create and run processor
        processor = RepositoryProcessor(config)
        await processor.run()
        
        return 0
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
