"""Job data model for DynamoDB Jobs table.

DynamoDB Schema:
- PK: JOB#<jobId>
- SK: META
- Attributes: repo_owner, repo_name, branch, status, stage, processed, total,
              message, started_at, updated_at, finished_at, error
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class JobStatus(str, Enum):
    """Valid job status values."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class JobStage(str, Enum):
    """Valid job stage values."""
    FETCH_DETAILS = "FETCH_DETAILS"
    FETCH_TREE = "FETCH_TREE"
    FILTER = "FILTER"
    SUMMARIZE_FILES = "SUMMARIZE_FILES"
    SUMMARIZE_FOLDERS = "SUMMARIZE_FOLDERS"
    FINALIZE = "FINALIZE"


@dataclass
class Job:
    """Job record for tracking repository processing progress.
    
    Validates: Requirements 2.5, 2.6
    """
    job_id: str
    repo_owner: str
    repo_name: str
    branch: str
    status: JobStatus = JobStatus.PENDING
    stage: Optional[JobStage] = None
    processed: int = 0
    total: int = 0
    message: str = ""
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None

    @staticmethod
    def generate_pk(job_id: str) -> str:
        """Generate DynamoDB partition key for a job."""
        return f"JOB#{job_id}"

    @staticmethod
    def generate_sk() -> str:
        """Generate DynamoDB sort key for a job."""
        return "META"

    def to_dynamodb_item(self) -> dict[str, Any]:
        """Serialize to DynamoDB item format."""
        item = {
            "PK": self.generate_pk(self.job_id),
            "SK": self.generate_sk(),
            "job_id": self.job_id,
            "repo_owner": self.repo_owner,
            "repo_name": self.repo_name,
            "branch": self.branch,
            "status": self.status.value,
            "processed": self.processed,
            "total": self.total,
            "message": self.message,
        }
        if self.stage is not None:
            item["stage"] = self.stage.value
        if self.started_at is not None:
            item["started_at"] = self.started_at
        if self.updated_at is not None:
            item["updated_at"] = self.updated_at
        if self.finished_at is not None:
            item["finished_at"] = self.finished_at
        if self.error is not None:
            item["error"] = self.error
        return item

    @classmethod
    def from_dynamodb_item(cls, item: dict[str, Any]) -> "Job":
        """Deserialize from DynamoDB item format."""
        # Convert Decimal to int for numeric fields
        processed = item.get("processed", 0)
        total = item.get("total", 0)
        if hasattr(processed, "__int__"):
            processed = int(processed)
        if hasattr(total, "__int__"):
            total = int(total)
            
        return cls(
            job_id=item["job_id"],
            repo_owner=item["repo_owner"],
            repo_name=item["repo_name"],
            branch=item["branch"],
            status=JobStatus(item["status"]),
            stage=JobStage(item["stage"]) if item.get("stage") else None,
            processed=processed,
            total=total,
            message=item.get("message", ""),
            started_at=item.get("started_at"),
            updated_at=item.get("updated_at"),
            finished_at=item.get("finished_at"),
            error=item.get("error"),
        )

    def to_json(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict for API responses."""
        result = {
            "jobId": self.job_id,
            "repoOwner": self.repo_owner,
            "repoName": self.repo_name,
            "branch": self.branch,
            "status": self.status.value,
            "processed": self.processed,
            "total": self.total,
            "message": self.message,
        }
        if self.stage is not None:
            result["stage"] = self.stage.value
        if self.started_at is not None:
            result["startedAt"] = self.started_at
        if self.updated_at is not None:
            result["updatedAt"] = self.updated_at
        if self.finished_at is not None:
            result["finishedAt"] = self.finished_at
        if self.error is not None:
            result["error"] = self.error
        return result

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Job":
        """Deserialize from JSON dict."""
        return cls(
            job_id=data["jobId"],
            repo_owner=data["repoOwner"],
            repo_name=data["repoName"],
            branch=data["branch"],
            status=JobStatus(data["status"]),
            stage=JobStage(data["stage"]) if data.get("stage") else None,
            processed=data.get("processed", 0),
            total=data.get("total", 0),
            message=data.get("message", ""),
            started_at=data.get("startedAt"),
            updated_at=data.get("updatedAt"),
            finished_at=data.get("finishedAt"),
            error=data.get("error"),
        )
