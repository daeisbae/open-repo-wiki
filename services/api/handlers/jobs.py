"""Jobs API Lambda handlers.

Implements:
- POST /jobs - Create new processing job
- GET /jobs/{jobId} - Get job status

Requirements: 4.1, 10.1, 10.2
"""

import json
import os
import re
import uuid
from typing import Any

import boto3
from botocore.config import Config

from shared.models import Job, JobStatus
from shared.storage.dynamodb import DynamoDBClient


# Constants
MAX_CONCURRENT_JOBS = 10
OWNER_REPO_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")


class APIError(Exception):
    """API error with HTTP status code."""
    
    def __init__(self, code: str, message: str, status_code: int):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _get_dynamodb_client() -> DynamoDBClient:
    """Get DynamoDB client with optional LocalStack endpoint."""
    endpoint_url = os.environ.get("DYNAMODB_ENDPOINT_URL")
    return DynamoDBClient(endpoint_url=endpoint_url)


def _get_sfn_client():
    """Get Step Functions client with optional LocalStack endpoint."""
    endpoint_url = os.environ.get("SFN_ENDPOINT_URL")
    config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
    
    client_kwargs = {
        "region_name": os.environ.get("AWS_REGION", "us-east-1"),
        "config": config,
    }
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url
        
    return boto3.client("stepfunctions", **client_kwargs)


def _build_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """Build API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        },
        "body": json.dumps(body),
    }


def _build_error_response(error: APIError) -> dict[str, Any]:
    """Build error response."""
    return _build_response(
        error.status_code,
        {"error": {"code": error.code, "message": error.message}},
    )


def _validate_owner_repo(owner: str, repo: str) -> None:
    """Validate owner and repo names.
    
    Args:
        owner: Repository owner
        repo: Repository name
        
    Raises:
        APIError: If validation fails
    """
    if not owner or not isinstance(owner, str):
        raise APIError("INVALID_INPUT", "Missing or invalid 'owner' field", 400)
    
    if not repo or not isinstance(repo, str):
        raise APIError("INVALID_INPUT", "Missing or invalid 'repo' field", 400)
    
    # Validate format (alphanumeric, hyphens, underscores, dots)
    owner_pattern = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
    repo_pattern = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
    
    if not owner_pattern.match(owner) or len(owner) > 39:
        raise APIError(
            "INVALID_INPUT",
            "Invalid 'owner' format. Must be alphanumeric with hyphens/underscores/dots, max 39 chars",
            400,
        )
    
    if not repo_pattern.match(repo) or len(repo) > 100:
        raise APIError(
            "INVALID_INPUT",
            "Invalid 'repo' format. Must be alphanumeric with hyphens/underscores/dots, max 100 chars",
            400,
        )


def _check_concurrency_limit(ddb_client: DynamoDBClient) -> None:
    """Check if concurrent job limit is exceeded.
    
    Args:
        ddb_client: DynamoDB client
        
    Raises:
        APIError: If limit exceeded
        
    Requirements: 10.1, 10.2
    """
    running_count = ddb_client.count_running_jobs()
    if running_count >= MAX_CONCURRENT_JOBS:
        raise APIError(
            "CONCURRENCY_LIMIT",
            f"Maximum concurrent jobs ({MAX_CONCURRENT_JOBS}) exceeded. Please try again later.",
            429,
        )


def create_job(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Create a new processing job.
    
    POST /jobs
    
    Request body:
        {
            "owner": "string",
            "repo": "string",
            "branch": "string" (optional, defaults to default branch)
        }
    
    Response:
        201: {"jobId": "string"}
        400: {"error": {"code": "INVALID_INPUT", "message": "..."}}
        429: {"error": {"code": "CONCURRENCY_LIMIT", "message": "..."}}
        500: {"error": {"code": "INTERNAL_ERROR", "message": "..."}}
    
    Requirements: 4.1, 10.1, 10.2
    """
    try:
        # Parse request body
        body = event.get("body", "{}")
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                raise APIError("INVALID_INPUT", "Invalid JSON in request body", 400)
        
        owner = body.get("owner", "").strip()
        repo = body.get("repo", "").strip()
        branch = body.get("branch", "").strip() or "main"  # Default to main
        
        # Validate input
        _validate_owner_repo(owner, repo)
        
        # Get clients
        ddb_client = _get_dynamodb_client()
        sfn_client = _get_sfn_client()
        
        # Check for existing running job (Idempotency)
        existing_job = ddb_client.get_running_job_for_repo(owner, repo, branch)
        if existing_job:
            return _build_response(200, {"jobId": existing_job.job_id, "message": "Job already in progress"})

        # Check if repository already has processed data (root node exists)
        # This is more reliable than checking job status
        repo_id = f"{owner}/{repo}"
        root_node = ddb_client.get_node(repo_id, branch, "")  # path="" is root
        if root_node:
            # Repository already processed - return completed status
            return _build_response(200, {"jobId": "completed", "message": "Job already completed"})

        # Check concurrency limit (Requirements: 10.1, 10.2)
        _check_concurrency_limit(ddb_client)
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create job record with PENDING status (Requirements: 4.1)
        job = Job(
            job_id=job_id,
            repo_owner=owner,
            repo_name=repo,
            branch=branch,
            status=JobStatus.PENDING,
        )
        ddb_client.create_job(job)
        
        # Start Step Functions execution (Requirements: 4.2)
        state_machine_arn = os.environ.get("STATE_MACHINE_ARN")
        if state_machine_arn:
            sfn_client.start_execution(
                stateMachineArn=state_machine_arn,
                name=f"job-{job_id}",
                input=json.dumps({
                    "jobId": job_id,
                    "repoOwner": owner,
                    "repoName": repo,
                    "branch": branch,
                }),
            )
        
        return _build_response(201, {"jobId": job_id})
        
    except APIError as e:
        return _build_error_response(e)
    except Exception as e:
        # Log the error for debugging
        print(f"Internal error: {e}")
        return _build_error_response(
            APIError("INTERNAL_ERROR", "An unexpected error occurred", 500)
        )


def get_job(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Get job status.
    
    GET /jobs/{jobId}
    
    Response:
        200: Job object with status, stage, progress
        404: {"error": {"code": "JOB_NOT_FOUND", "message": "..."}}
        500: {"error": {"code": "INTERNAL_ERROR", "message": "..."}}
    
    Requirements: 6.3
    """
    try:
        # Extract job ID from path parameters
        path_params = event.get("pathParameters", {}) or {}
        job_id = path_params.get("jobId", "")
        
        if not job_id:
            raise APIError("INVALID_INPUT", "Missing job ID in path", 400)
        
        # Get job from DynamoDB
        ddb_client = _get_dynamodb_client()
        job = ddb_client.get_job(job_id)
        
        if not job:
            raise APIError("JOB_NOT_FOUND", f"Job '{job_id}' not found", 404)
        
        return _build_response(200, job.to_json())
        
    except APIError as e:
        return _build_error_response(e)
    except Exception as e:
        # Log the error for debugging
        print(f"Internal error: {e}")
        return _build_error_response(
            APIError("INTERNAL_ERROR", "An unexpected error occurred", 500)
        )
