"""Finalize processing stage.

This stage updates the job status to SUCCEEDED and performs
any final cleanup.

Requirements: 5.8
"""

import logging

from botocore.exceptions import ClientError

from shared.models import JobStatus, JobStage
from shared.storage.dynamodb import DynamoDBClient


logger = logging.getLogger(__name__)


class FinalizeError(Exception):
    """Error during finalize stage."""
    pass


class FinalizeStage:
    """Stage for finalizing repository processing.
    
    This stage:
    1. Updates job stage to FINALIZE
    2. Updates job status to SUCCEEDED
    
    Requirements: 5.8
    """

    def __init__(
        self,
        dynamodb_client: DynamoDBClient,
        job_id: str,
    ):
        """Initialize the finalize stage.
        
        Args:
            dynamodb_client: DynamoDB client for updating job status.
            job_id: Job identifier.
        """
        self.dynamodb = dynamodb_client
        self.job_id = job_id

    def execute(self) -> None:
        """Execute the finalize stage.
        
        Updates job stage to FINALIZE and status to SUCCEEDED.
        
        Raises:
            FinalizeError: If updating job status fails.
            
        Requirements: 5.8
        """
        logger.info("Stage: FINALIZE - Finalizing processing")
        
        try:
            # Update job stage to FINALIZE
            self._update_progress("Finalizing...")
            
            # Update job status to SUCCEEDED
            self.dynamodb.update_job_status(
                job_id=self.job_id,
                status=JobStatus.SUCCEEDED,
            )
            
            logger.info("Processing finalized successfully")
            
        except ClientError as e:
            error_msg = f"Failed to finalize job: {e}"
            logger.error(error_msg)
            raise FinalizeError(error_msg) from e

    def _update_progress(self, message: str) -> None:
        """Update job progress in DynamoDB.
        
        Args:
            message: Progress message.
        """
        try:
            self.dynamodb.update_job_progress(
                job_id=self.job_id,
                stage=JobStage.FINALIZE,
                message=message,
            )
        except ClientError as e:
            logger.warning(f"Failed to update job progress: {e}")
