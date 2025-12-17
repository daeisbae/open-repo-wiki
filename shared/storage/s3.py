"""S3 client for async operations on the artifacts bucket.

Implements operations for:
- Wiki pages (put_page, get_page)
- Repository summaries (put_repo_summary, get_repo_summary)

S3 Key Patterns:
- Wiki pages: repos/<repoId>/branches/<branch>/pages/<path>.md
- Repository summaries: repos/<repoId>/branches/<branch>/summaries/repo.md

Requirements: 3.2, 3.3
"""

import os
from typing import Any, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class S3Client:
    """S3 operations for the artifacts bucket.
    
    This client provides methods for storing and retrieving wiki pages
    and repository summaries with consistent key patterns.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        """Initialize S3 client.
        
        Args:
            bucket_name: Name of the S3 bucket (defaults to env var S3_BUCKET)
            region_name: AWS region (defaults to env var AWS_REGION or us-east-1)
            endpoint_url: Optional endpoint URL for local testing (e.g., LocalStack)
        """
        self.bucket_name = bucket_name or os.environ.get(
            "S3_BUCKET", "openrepowiki-artifacts"
        )
        self.region_name = region_name or os.environ.get("AWS_REGION", "us-east-1")
        
        config = Config(
            retries={"max_attempts": 3, "mode": "adaptive"}
        )
        
        client_kwargs: dict[str, Any] = {
            "region_name": self.region_name,
            "config": config,
        }
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
            
        self._s3 = boto3.client("s3", **client_kwargs)

    @staticmethod
    def generate_page_key(repo_id: str, branch: str, path: str) -> str:
        """Generate S3 key for a wiki page.
        
        Args:
            repo_id: Repository identifier (owner/name)
            branch: Branch name
            path: File or folder path within the repository
            
        Returns:
            S3 key in format: repos/<repoId>/branches/<branch>/pages/<path>.md
            
        Requirements: 3.2
        """
        # Normalize path - remove leading/trailing slashes
        normalized_path = path.strip("/")
        
        # Handle empty path (root)
        if not normalized_path:
            normalized_path = "_root"
            
        return f"repos/{repo_id}/branches/{branch}/pages/{normalized_path}.md"

    @staticmethod
    def generate_repo_summary_key(repo_id: str, branch: str) -> str:
        """Generate S3 key for a repository summary.
        
        Args:
            repo_id: Repository identifier (owner/name)
            branch: Branch name
            
        Returns:
            S3 key in format: repos/<repoId>/branches/<branch>/summaries/repo.md
            
        Requirements: 3.3
        """
        return f"repos/{repo_id}/branches/{branch}/summaries/repo.md"

    def put_page(
        self,
        repo_id: str,
        branch: str,
        path: str,
        content: str,
    ) -> str:
        """Store a wiki page in S3.
        
        Args:
            repo_id: Repository identifier (owner/name)
            branch: Branch name
            path: File or folder path within the repository
            content: Markdown content to store (UTF-8 encoded)
            
        Returns:
            The S3 key where the content was stored
            
        Requirements: 3.2
        """
        key = self.generate_page_key(repo_id, branch, path)
        
        self._s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content.encode("utf-8"),
            ContentType="text/markdown; charset=utf-8",
        )
        
        return key

    def get_page(self, key: str) -> Optional[str]:
        """Retrieve a wiki page from S3.
        
        Args:
            key: S3 key of the page to retrieve
            
        Returns:
            Markdown content as string, or None if not found
            
        Requirements: 3.2
        """
        try:
            response = self._s3.get_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            content = response["Body"].read().decode("utf-8")
            return content
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise

    def put_repo_summary(
        self,
        repo_id: str,
        branch: str,
        content: str,
    ) -> str:
        """Store a repository summary in S3.
        
        Args:
            repo_id: Repository identifier (owner/name)
            branch: Branch name
            content: Markdown content to store (UTF-8 encoded)
            
        Returns:
            The S3 key where the content was stored
            
        Requirements: 3.3
        """
        key = self.generate_repo_summary_key(repo_id, branch)
        
        self._s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content.encode("utf-8"),
            ContentType="text/markdown; charset=utf-8",
        )
        
        return key

    def get_repo_summary(self, repo_id: str, branch: str) -> Optional[str]:
        """Retrieve a repository summary from S3.
        
        Args:
            repo_id: Repository identifier (owner/name)
            branch: Branch name
            
        Returns:
            Markdown content as string, or None if not found
            
        Requirements: 3.3
        """
        key = self.generate_repo_summary_key(repo_id, branch)
        return self.get_page(key)

    def delete_page(self, key: str) -> None:
        """Delete a page from S3.
        
        Args:
            key: S3 key of the page to delete
        """
        self._s3.delete_object(
            Bucket=self.bucket_name,
            Key=key,
        )

    def page_exists(self, key: str) -> bool:
        """Check if a page exists in S3.
        
        Args:
            key: S3 key to check
            
        Returns:
            True if the object exists, False otherwise
        """
        try:
            self._s3.head_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise
