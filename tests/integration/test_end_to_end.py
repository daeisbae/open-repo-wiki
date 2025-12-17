"""End-to-end integration tests for the full processing flow.

Tests the complete workflow:
1. Submit job via API (POST /jobs)
2. Poll until completion (GET /jobs/{jobId})
3. Verify tree retrieval (GET /repos/{repoId}/tree)
4. Verify page retrieval (GET /repos/{repoId}/page)

Requirements: All
"""

import json
import os
import time
import uuid
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest

from services.api.handlers.jobs import create_job, get_job
from services.api.handlers.repos import get_tree, get_page
from shared.models import Job, JobStatus, JobStage, TreeNode, NodeType, Repo, Branch
from shared.storage.dynamodb import DynamoDBClient
from shared.storage.s3 import S3Client


class MockDynamoDBClient:
    """Mock DynamoDB client for integration testing."""
    
    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._nodes: dict[str, TreeNode] = {}
        self._repos: dict[str, Repo] = {}
        self._branches: dict[str, Branch] = {}
    
    def create_job(self, job: Job) -> None:
        """Store a job record."""
        self._jobs[job.job_id] = job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve a job record."""
        return self._jobs.get(job_id)
    
    def count_running_jobs(self) -> int:
        """Count running jobs."""
        return sum(1 for j in self._jobs.values() if j.status == JobStatus.RUNNING)
    
    def update_job_progress(
        self,
        job_id: str,
        stage: Optional[JobStage] = None,
        processed: Optional[int] = None,
        total: Optional[int] = None,
        message: Optional[str] = None,
        status: Optional[JobStatus] = None,
    ) -> None:
        """Update job progress."""
        job = self._jobs.get(job_id)
        if job:
            if stage is not None:
                job.stage = stage
            if processed is not None:
                job.processed = processed
            if total is not None:
                job.total = total
            if message is not None:
                job.message = message
            if status is not None:
                job.status = status
    
    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error: Optional[str] = None,
    ) -> None:
        """Update job status."""
        job = self._jobs.get(job_id)
        if job:
            job.status = status
            if error:
                job.error = error
    
    def put_node(self, node: TreeNode) -> None:
        """Store a tree node."""
        key = f"{node.repo_id}#{node.branch}#{node.path}"
        self._nodes[key] = node
    
    def put_nodes_batch(self, nodes: list[TreeNode]) -> None:
        """Store multiple tree nodes."""
        for node in nodes:
            self.put_node(node)
    
    def query_tree(self, repo_id: str, branch: str, path: str = "") -> list[TreeNode]:
        """Query tree nodes by parent path."""
        results = []
        for node in self._nodes.values():
            if node.repo_id == repo_id and node.branch == branch and node.parent_path == path:
                results.append(node)
        return results
    
    def get_node(self, repo_id: str, branch: str, path: str) -> Optional[TreeNode]:
        """Get a specific tree node."""
        key = f"{repo_id}#{branch}#{path}"
        return self._nodes.get(key)
    
    def put_repo(self, repo: Repo) -> None:
        """Store a repository record."""
        self._repos[repo.repo_id] = repo
    
    def get_repo(self, repo_id: str) -> Optional[Repo]:
        """Retrieve a repository record."""
        return self._repos.get(repo_id)
    
    def put_branch(self, branch: Branch) -> None:
        """Store a branch record."""
        key = f"{branch.repo_id}#{branch.branch_name}"
        self._branches[key] = branch
    
    def get_branch(self, repo_id: str, branch_name: str) -> Optional[Branch]:
        """Retrieve a branch record."""
        key = f"{repo_id}#{branch_name}"
        return self._branches.get(key)


class MockS3Client:
    """Mock S3 client for integration testing."""
    
    def __init__(self):
        self._objects: dict[str, str] = {}
    
    def put_page(self, repo_id: str, branch: str, path: str, content: str) -> str:
        """Store a wiki page."""
        key = S3Client.generate_page_key(repo_id, branch, path)
        self._objects[key] = content
        return key
    
    def get_page(self, key: str) -> Optional[str]:
        """Retrieve a wiki page."""
        return self._objects.get(key)
    
    def put_repo_summary(self, repo_id: str, branch: str, content: str) -> str:
        """Store a repository summary."""
        key = S3Client.generate_repo_summary_key(repo_id, branch)
        self._objects[key] = content
        return key
    
    def get_repo_summary(self, repo_id: str, branch: str) -> Optional[str]:
        """Retrieve a repository summary."""
        key = S3Client.generate_repo_summary_key(repo_id, branch)
        return self.get_page(key)


class MockStepFunctionsClient:
    """Mock Step Functions client for integration testing."""
    
    def __init__(self):
        self.executions: list[dict] = []
    
    def start_execution(self, stateMachineArn: str, name: str, input: str) -> dict:
        """Start a state machine execution."""
        execution = {
            "stateMachineArn": stateMachineArn,
            "name": name,
            "input": input,
            "executionArn": f"{stateMachineArn}:execution:{name}",
        }
        self.executions.append(execution)
        return {"executionArn": execution["executionArn"]}


def _simulate_processing(mock_ddb: MockDynamoDBClient, mock_s3: MockS3Client, job_id: str, repo_id: str, branch: str):
    """Simulate the processor completing a job with sample data."""
    # Update job to RUNNING
    mock_ddb.update_job_status(job_id, JobStatus.RUNNING)
    
    # Simulate processing stages
    mock_ddb.update_job_progress(job_id, stage=JobStage.FETCH_DETAILS, message="Fetching repository details")
    mock_ddb.update_job_progress(job_id, stage=JobStage.FETCH_TREE, message="Fetching repository tree")
    mock_ddb.update_job_progress(job_id, stage=JobStage.FILTER, message="Filtering tree")
    
    # Create sample tree nodes
    nodes = [
        TreeNode(
            repo_id=repo_id,
            branch=branch,
            path="src",
            node_type=NodeType.FOLDER,
            name="src",
            parent_path="",
            summary_ref=f"repos/{repo_id}/branches/{branch}/pages/src.md",
        ),
        TreeNode(
            repo_id=repo_id,
            branch=branch,
            path="src/main.py",
            node_type=NodeType.FILE,
            name="main.py",
            parent_path="src",
            sha="abc123",
            size=1024,
            language="Python",
            summary_ref=f"repos/{repo_id}/branches/{branch}/pages/src/main.py.md",
        ),
        TreeNode(
            repo_id=repo_id,
            branch=branch,
            path="README.md",
            node_type=NodeType.FILE,
            name="README.md",
            parent_path="",
            sha="def456",
            size=512,
            language="Markdown",
            summary_ref=f"repos/{repo_id}/branches/{branch}/pages/README.md.md",
        ),
    ]
    mock_ddb.put_nodes_batch(nodes)
    
    # Create sample page content in S3
    mock_s3.put_page(repo_id, branch, "src", "# src folder\n\nThis folder contains source code.")
    mock_s3.put_page(repo_id, branch, "src/main.py", "# main.py\n\nMain entry point for the application.")
    mock_s3.put_page(repo_id, branch, "README.md", "# README\n\nProject documentation.")
    
    # Update progress
    mock_ddb.update_job_progress(
        job_id,
        stage=JobStage.SUMMARIZE_FILES,
        processed=3,
        total=3,
        message="Summarizing files",
    )
    mock_ddb.update_job_progress(job_id, stage=JobStage.SUMMARIZE_FOLDERS, message="Summarizing folders")
    mock_ddb.update_job_progress(job_id, stage=JobStage.FINALIZE, message="Finalizing")
    
    # Mark job as succeeded
    mock_ddb.update_job_status(job_id, JobStatus.SUCCEEDED)


class TestEndToEndFlow:
    """Integration tests for the complete processing flow."""
    
    def test_full_flow_submit_poll_retrieve(self):
        """
        Test the complete flow:
        1. Submit job via POST /jobs
        2. Poll job status via GET /jobs/{jobId}
        3. Retrieve tree via GET /repos/{repoId}/tree
        4. Retrieve page via GET /repos/{repoId}/page
        
        Requirements: All
        """
        # Setup mocks
        mock_ddb = MockDynamoDBClient()
        mock_s3 = MockS3Client()
        mock_sfn = MockStepFunctionsClient()
        
        owner = "testowner"
        repo = "testrepo"
        branch = "main"
        repo_id = f"{owner}/{repo}"
        
        # Step 1: Submit job via POST /jobs
        create_event = {
            "body": json.dumps({"owner": owner, "repo": repo, "branch": branch}),
        }
        
        with patch("services.api.handlers.jobs._get_dynamodb_client", return_value=mock_ddb):
            with patch("services.api.handlers.jobs._get_sfn_client", return_value=mock_sfn):
                with patch.dict(os.environ, {"STATE_MACHINE_ARN": "arn:aws:states:us-east-1:123456789:stateMachine:test"}):
                    create_response = create_job(create_event, None)
        
        # Verify job creation
        assert create_response["statusCode"] == 201
        create_body = json.loads(create_response["body"])
        assert "jobId" in create_body
        job_id = create_body["jobId"]
        
        # Verify Step Functions was started
        assert len(mock_sfn.executions) == 1
        
        # Step 2: Poll job status (initially PENDING)
        get_job_event = {
            "pathParameters": {"jobId": job_id},
        }
        
        with patch("services.api.handlers.jobs._get_dynamodb_client", return_value=mock_ddb):
            get_response = get_job(get_job_event, None)
        
        assert get_response["statusCode"] == 200
        job_body = json.loads(get_response["body"])
        assert job_body["status"] == "PENDING"
        
        # Simulate processing completion
        _simulate_processing(mock_ddb, mock_s3, job_id, repo_id, branch)
        
        # Poll again - should be SUCCEEDED
        with patch("services.api.handlers.jobs._get_dynamodb_client", return_value=mock_ddb):
            get_response = get_job(get_job_event, None)
        
        assert get_response["statusCode"] == 200
        job_body = json.loads(get_response["body"])
        assert job_body["status"] == "SUCCEEDED"
        assert job_body["stage"] == "FINALIZE"
        
        # Step 3: Retrieve tree via GET /repos/{repoId}/tree
        tree_event = {
            "pathParameters": {"repoId": repo_id},
            "queryStringParameters": {"branch": branch, "path": ""},
        }
        
        with patch("services.api.handlers.repos._get_dynamodb_client", return_value=mock_ddb):
            tree_response = get_tree(tree_event, None)
        
        assert tree_response["statusCode"] == 200
        tree_body = json.loads(tree_response["body"])
        assert "nodes" in tree_body
        
        # Verify root level nodes (src folder and README.md)
        nodes = tree_body["nodes"]
        assert len(nodes) == 2
        node_names = {n["name"] for n in nodes}
        assert "src" in node_names
        assert "README.md" in node_names
        
        # Verify node structure
        for node in nodes:
            assert "type" in node
            assert "name" in node
            assert "path" in node
            assert "hasSummary" in node
            assert node["hasSummary"] is True  # All nodes have summaries
        
        # Query subdirectory
        tree_event_subdir = {
            "pathParameters": {"repoId": repo_id},
            "queryStringParameters": {"branch": branch, "path": "src"},
        }
        
        with patch("services.api.handlers.repos._get_dynamodb_client", return_value=mock_ddb):
            tree_response_subdir = get_tree(tree_event_subdir, None)
        
        assert tree_response_subdir["statusCode"] == 200
        tree_body_subdir = json.loads(tree_response_subdir["body"])
        nodes_subdir = tree_body_subdir["nodes"]
        assert len(nodes_subdir) == 1
        assert nodes_subdir[0]["name"] == "main.py"
        
        # Step 4: Retrieve page via GET /repos/{repoId}/page
        page_event = {
            "pathParameters": {"repoId": repo_id},
            "queryStringParameters": {"branch": branch, "path": "src/main.py"},
        }
        
        with patch("services.api.handlers.repos._get_dynamodb_client", return_value=mock_ddb):
            with patch("services.api.handlers.repos._get_s3_client", return_value=mock_s3):
                page_response = get_page(page_event, None)
        
        assert page_response["statusCode"] == 200
        page_body = json.loads(page_response["body"])
        assert page_body["available"] is True
        assert "main.py" in page_body["content"]
        assert "Main entry point" in page_body["content"]
    
    def test_job_not_found(self):
        """Test GET /jobs/{jobId} returns 404 for non-existent job."""
        mock_ddb = MockDynamoDBClient()
        
        event = {
            "pathParameters": {"jobId": "non-existent-job-id"},
        }
        
        with patch("services.api.handlers.jobs._get_dynamodb_client", return_value=mock_ddb):
            response = get_job(event, None)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"]["code"] == "JOB_NOT_FOUND"
    
    def test_node_not_found(self):
        """Test GET /repos/{repoId}/page returns 404 for non-existent node."""
        mock_ddb = MockDynamoDBClient()
        mock_s3 = MockS3Client()
        
        event = {
            "pathParameters": {"repoId": "owner/repo"},
            "queryStringParameters": {"branch": "main", "path": "nonexistent.py"},
        }
        
        with patch("services.api.handlers.repos._get_dynamodb_client", return_value=mock_ddb):
            with patch("services.api.handlers.repos._get_s3_client", return_value=mock_s3):
                response = get_page(event, None)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"]["code"] == "NODE_NOT_FOUND"
    
    def test_folder_only_mode(self):
        """Test that folder-only mode returns available=False for files without summaries."""
        mock_ddb = MockDynamoDBClient()
        mock_s3 = MockS3Client()
        
        repo_id = "owner/repo"
        branch = "main"
        
        # Create a node without summary_ref (folder-only mode)
        node = TreeNode(
            repo_id=repo_id,
            branch=branch,
            path="src/large_file.py",
            node_type=NodeType.FILE,
            name="large_file.py",
            parent_path="src",
            sha="abc123",
            size=10000,
            language="Python",
            summary_ref=None,  # No summary in folder-only mode
        )
        mock_ddb.put_node(node)
        
        event = {
            "pathParameters": {"repoId": repo_id},
            "queryStringParameters": {"branch": branch, "path": "src/large_file.py"},
        }
        
        with patch("services.api.handlers.repos._get_dynamodb_client", return_value=mock_ddb):
            with patch("services.api.handlers.repos._get_s3_client", return_value=mock_s3):
                response = get_page(event, None)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["available"] is False
        assert body["content"] == ""
    
    def test_invalid_input_validation(self):
        """Test that invalid input is properly rejected."""
        mock_ddb = MockDynamoDBClient()
        mock_sfn = MockStepFunctionsClient()
        
        # Test missing owner
        event = {
            "body": json.dumps({"repo": "testrepo"}),
        }
        
        with patch("services.api.handlers.jobs._get_dynamodb_client", return_value=mock_ddb):
            with patch("services.api.handlers.jobs._get_sfn_client", return_value=mock_sfn):
                response = create_job(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INVALID_INPUT"
        
        # Test missing repo
        event = {
            "body": json.dumps({"owner": "testowner"}),
        }
        
        with patch("services.api.handlers.jobs._get_dynamodb_client", return_value=mock_ddb):
            with patch("services.api.handlers.jobs._get_sfn_client", return_value=mock_sfn):
                response = create_job(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INVALID_INPUT"
    
    def test_tree_empty_result(self):
        """Test GET /repos/{repoId}/tree returns empty nodes for path with no children."""
        mock_ddb = MockDynamoDBClient()
        
        repo_id = "owner/repo"
        branch = "main"
        
        event = {
            "pathParameters": {"repoId": repo_id},
            "queryStringParameters": {"branch": branch, "path": "empty_folder"},
        }
        
        with patch("services.api.handlers.repos._get_dynamodb_client", return_value=mock_ddb):
            response = get_tree(event, None)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["nodes"] == []
    
    def test_concurrency_limit_rejection(self):
        """Test that jobs are rejected when concurrency limit is reached."""
        mock_ddb = MockDynamoDBClient()
        mock_sfn = MockStepFunctionsClient()
        
        # Create 10 running jobs
        for i in range(10):
            job = Job(
                job_id=f"running-job-{i}",
                repo_owner="owner",
                repo_name=f"repo{i}",
                branch="main",
                status=JobStatus.RUNNING,
            )
            mock_ddb._jobs[job.job_id] = job
        
        # Try to create another job
        event = {
            "body": json.dumps({"owner": "testowner", "repo": "testrepo"}),
        }
        
        with patch("services.api.handlers.jobs._get_dynamodb_client", return_value=mock_ddb):
            with patch("services.api.handlers.jobs._get_sfn_client", return_value=mock_sfn):
                with patch.dict(os.environ, {"STATE_MACHINE_ARN": "arn:aws:states:us-east-1:123456789:stateMachine:test"}):
                    response = create_job(event, None)
        
        assert response["statusCode"] == 429
        body = json.loads(response["body"])
        assert body["error"]["code"] == "CONCURRENCY_LIMIT"
    
    def test_job_failure_handling(self):
        """Test that failed jobs are properly reported."""
        mock_ddb = MockDynamoDBClient()
        mock_sfn = MockStepFunctionsClient()
        
        owner = "testowner"
        repo = "testrepo"
        
        # Create job
        event = {
            "body": json.dumps({"owner": owner, "repo": repo}),
        }
        
        with patch("services.api.handlers.jobs._get_dynamodb_client", return_value=mock_ddb):
            with patch("services.api.handlers.jobs._get_sfn_client", return_value=mock_sfn):
                with patch.dict(os.environ, {"STATE_MACHINE_ARN": "arn:aws:states:us-east-1:123456789:stateMachine:test"}):
                    create_response = create_job(event, None)
        
        job_id = json.loads(create_response["body"])["jobId"]
        
        # Simulate job failure
        mock_ddb.update_job_status(job_id, JobStatus.RUNNING)
        mock_ddb.update_job_progress(job_id, stage=JobStage.FETCH_DETAILS)
        mock_ddb.update_job_status(job_id, JobStatus.FAILED, error="GitHub API rate limit exceeded")
        
        # Get job status
        get_event = {
            "pathParameters": {"jobId": job_id},
        }
        
        with patch("services.api.handlers.jobs._get_dynamodb_client", return_value=mock_ddb):
            response = get_job(get_event, None)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["status"] == "FAILED"
        assert body["error"] == "GitHub API rate limit exceeded"
