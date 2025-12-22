"""DynamoDB client for async operations on Main and Jobs tables.

Implements operations for:
- Repository metadata (put_repo)
- Branch records (put_branch)
- Tree nodes (put_node, query_tree)
- Job tracking (update_job_progress, get_job, count_running_jobs)

Requirements: 2.1, 2.5, 6.2, 7.1
"""

import os
from datetime import datetime, timezone
from typing import Any, Optional

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.config import Config

from shared.models import (
    Job,
    JobStatus,
    JobStage,
    Repo,
    Branch,
    TreeNode,
)


class DynamoDBClient:
    """DynamoDB operations for Main and Jobs tables.
    
    This client provides methods for storing and retrieving repository metadata,
    branches, tree nodes, and job progress tracking.
    """

    def __init__(
        self,
        main_table_name: Optional[str] = None,
        jobs_table_name: Optional[str] = None,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        """Initialize DynamoDB client.
        
        Args:
            main_table_name: Name of the main table (defaults to env var DDB_MAIN_TABLE)
            jobs_table_name: Name of the jobs table (defaults to env var DDB_JOBS_TABLE)
            region_name: AWS region (defaults to env var AWS_REGION or us-east-1)
            endpoint_url: Optional endpoint URL for local testing
        """
        self.main_table_name = main_table_name or os.environ.get(
            "DDB_MAIN_TABLE", "OpenRepoWikiMain"
        )
        self.jobs_table_name = jobs_table_name or os.environ.get(
            "DDB_JOBS_TABLE", "OpenRepoWikiJobs"
        )
        self.region_name = region_name or os.environ.get("AWS_REGION", "us-east-1")
        self.endpoint_url = endpoint_url
        
        self.config = Config(
            retries={"max_attempts": 5, "mode": "adaptive"}
        )
        
        # We'll create resources lazily or per-thread to ensure safety
        self._local_session = None

    def _get_table(self, table_name: str):
        """Get a DynamoDB Table resource, ensuring thread safety."""
        # For simplicity in this environment, we'll create a new resource if needed.
        # Boto3 resources are not thread-safe, so we must be careful when using with asyncio.to_thread
        session = boto3.Session()
        db = session.resource(
            "dynamodb", 
            region_name=self.region_name, 
            endpoint_url=self.endpoint_url,
            config=self.config
        )
        return db.Table(table_name)

    @property
    def _main_table(self):
        return self._get_table(self.main_table_name)

    @property
    def _jobs_table(self):
        return self._get_table(self.jobs_table_name)

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

    # Repository operations

    def put_repo(self, repo: Repo) -> None:
        """Store a repository record in the Main table.
        
        Args:
            repo: Repository data to store
            
        Requirements: 2.2
        """
        item = repo.to_dynamodb_item()
        self._main_table.put_item(Item=item)

    def get_repo(self, repo_id: str) -> Optional[Repo]:
        """Retrieve a repository record from the Main table.
        
        Args:
            repo_id: Repository identifier (owner/name)
            
        Returns:
            Repo object if found, None otherwise
        """
        response = self._main_table.get_item(
            Key={
                "PK": Repo.generate_pk(repo_id),
                "SK": Repo.generate_sk(),
            }
        )
        item = response.get("Item")
        if item:
            return Repo.from_dynamodb_item(item)
        return None

    # Branch operations

    def put_branch(self, branch: Branch) -> None:
        """Store a branch record in the Main table.
        
        Args:
            branch: Branch data to store
            
        Requirements: 2.3
        """
        item = branch.to_dynamodb_item()
        self._main_table.put_item(Item=item)

    def get_branch(self, repo_id: str, branch_name: str) -> Optional[Branch]:
        """Retrieve a branch record from the Main table.
        
        Args:
            repo_id: Repository identifier
            branch_name: Branch name
            
        Returns:
            Branch object if found, None otherwise
        """
        response = self._main_table.get_item(
            Key={
                "PK": Branch.generate_pk(repo_id),
                "SK": Branch.generate_sk(branch_name),
            }
        )
        item = response.get("Item")
        if item:
            return Branch.from_dynamodb_item(item)
        return None

    # Tree node operations

    def put_node(self, node: TreeNode) -> None:
        """Store a tree node record in the Main table.
        
        Args:
            node: Tree node data to store
            
        Requirements: 2.4
        """
        # Handle empty parent_path for GSI compatibility
        if not node.parent_path:
            node.parent_path = "/"
            
        item = node.to_dynamodb_item()
        self._main_table.put_item(Item=item)

    def put_nodes_batch(self, nodes: list[TreeNode]) -> None:
        """Store multiple tree nodes in batch.
        
        Args:
            nodes: List of tree nodes to store
            
        Note: DynamoDB batch_write_item has a limit of 25 items per batch.
        """
        with self._main_table.batch_writer() as batch:
            for node in nodes:
                # Handle empty parent_path for GSI compatibility
                if not node.parent_path:
                    node.parent_path = "/"
                batch.put_item(Item=node.to_dynamodb_item())

    def query_tree(
        self,
        repo_id: str,
        branch: str,
        path: str = "",
    ) -> list[TreeNode]:
        """Query tree nodes for a repository branch at a given path.
        
        Returns immediate children of the specified path (not recursive).
        
        Args:
            repo_id: Repository identifier
            branch: Branch name
            path: Parent path to query children for (empty string for root)
            
        Returns:
            List of TreeNode objects that are direct children of the path
            
        Requirements: 7.1
        """
        pk = TreeNode.generate_pk(repo_id, branch)
        
        # Query tree nodes using GSI (Requirements: 7.1)
        # Using GSI allows efficient lookup by parent_path without scanning
        # Use "/" as sentinel for empty parent_path (GSI keys cannot be empty)
        query_path = path if path else "/"
        
        try:
            response = self._main_table.query(
                IndexName="ParentPathIndex",
                KeyConditionExpression=Key("PK").eq(pk) & Key("parent_path").eq(query_path),
            )
        except Exception as e:
            # Fallback for environments without GSI (e.g., LocalStack)
            # Use filter expression instead (less efficient but works)
            if "Index not found" in str(e) or "ResourceNotFoundException" in str(e):
                response = self._main_table.query(
                    KeyConditionExpression=Key("PK").eq(pk),
                    FilterExpression=Attr("parent_path").eq(path),
                )
            else:
                raise
        
        nodes = [TreeNode.from_dynamodb_item(item) for item in response.get("Items", [])]
        
        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = self._main_table.query(
                KeyConditionExpression=Key("PK").eq(pk),
                FilterExpression=Attr("parent_path").eq(path),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            nodes.extend(
                TreeNode.from_dynamodb_item(item) for item in response.get("Items", [])
            )
        
        return nodes

    def get_node(self, repo_id: str, branch: str, path: str) -> Optional[TreeNode]:
        """Retrieve a specific tree node.
        
        Args:
            repo_id: Repository identifier
            branch: Branch name
            path: Node path
            
        Returns:
            TreeNode object if found, None otherwise
        """
        response = self._main_table.get_item(
            Key={
                "PK": TreeNode.generate_pk(repo_id, branch),
                "SK": TreeNode.generate_sk(path),
            }
        )
        item = response.get("Item")
        if item:
            return TreeNode.from_dynamodb_item(item)
        return None

    # Job operations

    def create_job(self, job: Job) -> None:
        """Create a new job record in the Jobs table.
        
        Args:
            job: Job data to store
            
        Requirements: 2.5
        """
        job.started_at = self._get_timestamp()
        job.updated_at = job.started_at
        item = job.to_dynamodb_item()
        self._jobs_table.put_item(Item=item)

    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve a job record from the Jobs table.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job object if found, None otherwise
            
        Requirements: 6.3
        """
        response = self._jobs_table.get_item(
            Key={
                "PK": Job.generate_pk(job_id),
                "SK": Job.generate_sk(),
            }
        )
        item = response.get("Item")
        if item:
            return Job.from_dynamodb_item(item)
        return None

    def update_job_progress(
        self,
        job_id: str,
        stage: Optional[JobStage] = None,
        processed: Optional[int] = None,
        total: Optional[int] = None,
        message: Optional[str] = None,
        status: Optional[JobStatus] = None,
    ) -> None:
        """Update job progress in the Jobs table.
        
        Args:
            job_id: Job identifier
            stage: Current processing stage
            processed: Number of items processed
            total: Total number of items to process
            message: Progress message
            status: Job status (optional, for status transitions)
            
        Requirements: 6.2
        """
        update_expr_parts = ["#updated_at = :updated_at"]
        expr_attr_names: dict[str, str] = {"#updated_at": "updated_at"}
        expr_attr_values: dict[str, Any] = {":updated_at": self._get_timestamp()}
        
        if stage is not None:
            update_expr_parts.append("#stage = :stage")
            expr_attr_names["#stage"] = "stage"
            expr_attr_values[":stage"] = stage.value
            
        if processed is not None:
            update_expr_parts.append("#processed = :processed")
            expr_attr_names["#processed"] = "processed"
            expr_attr_values[":processed"] = processed
            
        if total is not None:
            update_expr_parts.append("#total = :total")
            expr_attr_names["#total"] = "total"
            expr_attr_values[":total"] = total
            
        if message is not None:
            update_expr_parts.append("#message = :message")
            expr_attr_names["#message"] = "message"
            expr_attr_values[":message"] = message
            
        if status is not None:
            update_expr_parts.append("#status = :status")
            expr_attr_names["#status"] = "status"
            expr_attr_values[":status"] = status.value
            
        update_expression = "SET " + ", ".join(update_expr_parts)
        
        self._jobs_table.update_item(
            Key={
                "PK": Job.generate_pk(job_id),
                "SK": Job.generate_sk(),
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
        )

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error: Optional[str] = None,
    ) -> None:
        """Update job status, optionally marking as finished.
        
        Args:
            job_id: Job identifier
            status: New job status
            error: Error message (for FAILED status)
        """
        timestamp = self._get_timestamp()
        
        update_expr_parts = [
            "#status = :status",
            "#updated_at = :updated_at",
        ]
        expr_attr_names: dict[str, str] = {
            "#status": "status",
            "#updated_at": "updated_at",
        }
        expr_attr_values: dict[str, Any] = {
            ":status": status.value,
            ":updated_at": timestamp,
        }
        
        # Set finished_at for terminal states
        if status in (JobStatus.SUCCEEDED, JobStatus.FAILED):
            update_expr_parts.append("#finished_at = :finished_at")
            expr_attr_names["#finished_at"] = "finished_at"
            expr_attr_values[":finished_at"] = timestamp
            
        if error is not None:
            update_expr_parts.append("#error = :error")
            expr_attr_names["#error"] = "error"
            expr_attr_values[":error"] = error
            
        update_expression = "SET " + ", ".join(update_expr_parts)
        
        self._jobs_table.update_item(
            Key={
                "PK": Job.generate_pk(job_id),
                "SK": Job.generate_sk(),
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
        )

    def get_running_job_for_repo(
        self,
        repo_owner: str,
        repo_name: str,
        branch: str
    ) -> Optional[Job]:
        """Check if there is already a running job for this repo/branch.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            branch: Branch name
            
        Returns:
            Job object if a running job exists, None otherwise
        """
        response = self._jobs_table.query(
            IndexName="StatusIndex",
            KeyConditionExpression=Key("status").eq(JobStatus.RUNNING.value),
            FilterExpression=Attr("repo_owner").eq(repo_owner) & 
                             Attr("repo_name").eq(repo_name) & 
                             Attr("branch").eq(branch)
        )
        
        items = response.get("Items", [])
        if items:
            return Job.from_dynamodb_item(items[0])
        return None

    def get_completed_job_for_repo(
        self,
        repo_owner: str,
        repo_name: str,
        branch: str
    ) -> Optional[Job]:
        """Check if there is a completed job for this repo/branch.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            branch: Branch name
            
        Returns:
            Job object if a completed job exists, None otherwise
        """
        # Note: Ideally we would sort by timestamp, but for now retrieving any successful job works
        # to redirect the user to the result page.
        response = self._jobs_table.query(
            IndexName="StatusIndex",
            KeyConditionExpression=Key("status").eq(JobStatus.SUCCEEDED.value),
            FilterExpression=Attr("repo_owner").eq(repo_owner) & 
                             Attr("repo_name").eq(repo_name) & 
                             Attr("branch").eq(branch),
            Limit=1
        )
        
        items = response.get("Items", [])
        if items:
            return Job.from_dynamodb_item(items[0])
        return None

    def count_running_jobs(self) -> int:
        """Count the number of jobs with RUNNING status.
        
        Returns:
            Number of running jobs
            
        Requirements: 10.1, 10.2
        """
        # Scan the jobs table filtering by status = RUNNING
        # Note: For production with high volume, consider using a GSI
        response = self._jobs_table.scan(
            FilterExpression=Attr("status").eq(JobStatus.RUNNING.value),
            Select="COUNT",
        )
        
        count = response.get("Count", 0)
        
        # Handle pagination for large tables
        while "LastEvaluatedKey" in response:
            response = self._jobs_table.scan(
                FilterExpression=Attr("status").eq(JobStatus.RUNNING.value),
                Select="COUNT",
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            count += response.get("Count", 0)
            
        return count
