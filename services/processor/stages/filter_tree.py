"""Filter repository tree stage.

This stage applies whitelist/blacklist filters to the tree and
determines if folder-only mode should be used.

Requirements: 5.4, 5.5
"""

import logging
from dataclasses import dataclass

from botocore.exceptions import ClientError

from shared.models import JobStage
from shared.storage.dynamodb import DynamoDBClient
from shared.github.client import TreeResult
from shared.github.filter import filter_tree, count_filtered_files


logger = logging.getLogger(__name__)


class FilterTreeError(Exception):
    """Error during filter tree stage."""
    pass


@dataclass
class FilterTreeResult:
    """Result of the filter tree stage."""
    filtered_tree: TreeResult
    file_count: int
    folder_only_mode: bool


class FilterTreeStage:
    """Stage for filtering the repository tree.
    
    This stage:
    1. Applies whitelist/blacklist filters to the tree
    2. Counts filtered files
    3. Determines if folder-only mode should be used
    4. Updates job stage to FILTER
    
    Requirements: 5.4, 5.5
    """

    def __init__(
        self,
        dynamodb_client: DynamoDBClient,
        job_id: str,
        max_files_for_full_summary: int = 100,
    ):
        """Initialize the filter tree stage.
        
        Args:
            dynamodb_client: DynamoDB client for progress updates.
            job_id: Job identifier for progress updates.
            max_files_for_full_summary: Threshold for folder-only mode.
        """
        self.dynamodb = dynamodb_client
        self.job_id = job_id
        self.max_files_for_full_summary = max_files_for_full_summary

    def execute(self, tree: TreeResult) -> FilterTreeResult:
        """Execute the filter tree stage.
        
        Applies whitelist/blacklist filters and determines processing mode.
        
        Args:
            tree: The TreeResult from GitHub API.
            
        Returns:
            FilterTreeResult with filtered tree and mode information.
            
        Raises:
            FilterTreeError: If filtering fails.
            
        Requirements: 5.4, 5.5
        """
        logger.info("Stage: FILTER - Filtering repository tree")
        
        # Update job progress
        self._update_progress("Filtering repository tree...")
        
        try:
            # Apply whitelist/blacklist filters
            filtered_tree = filter_tree(tree)
            
            # Count filtered files
            file_count = count_filtered_files(filtered_tree)
            
            # Determine processing mode based on file count
            folder_only_mode = file_count > self.max_files_for_full_summary
            
            mode_str = "folder-only" if folder_only_mode else "full"
            logger.info(f"Filtering complete: {file_count} files, mode={mode_str}")
            
            # Update job with total count and mode info
            self._update_progress_with_total(
                file_count,
                f"Found {file_count} files to process ({mode_str} mode)",
            )
            
            return FilterTreeResult(
                filtered_tree=filtered_tree,
                file_count=file_count,
                folder_only_mode=folder_only_mode,
            )
            
        except Exception as e:
            error_msg = f"Failed to filter tree: {e}"
            logger.error(error_msg)
            raise FilterTreeError(error_msg) from e

    def _update_progress(self, message: str) -> None:
        """Update job progress in DynamoDB.
        
        Args:
            message: Progress message.
        """
        try:
            self.dynamodb.update_job_progress(
                job_id=self.job_id,
                stage=JobStage.FILTER,
                message=message,
            )
        except ClientError as e:
            logger.warning(f"Failed to update job progress: {e}")

    def _update_progress_with_total(self, total: int, message: str) -> None:
        """Update job progress with total count.
        
        Args:
            total: Total number of files to process.
            message: Progress message.
        """
        try:
            self.dynamodb.update_job_progress(
                job_id=self.job_id,
                stage=JobStage.FILTER,
                total=total,
                message=message,
            )
        except ClientError as e:
            logger.warning(f"Failed to update job progress: {e}")
