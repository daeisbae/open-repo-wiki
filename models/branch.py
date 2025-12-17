"""Branch data model for DynamoDB Main table.

DynamoDB Schema:
- PK: REPO#<repoId>
- SK: BRANCH#<branchName>
- Attributes: last_commit_sha, commit_at, ai_summary_ref
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Branch:
    """Branch record for a repository.
    
    Validates: Requirements 2.3
    """
    repo_id: str
    branch_name: str
    last_commit_sha: str
    commit_at: Optional[str] = None
    ai_summary_ref: Optional[str] = None

    @staticmethod
    def generate_pk(repo_id: str) -> str:
        """Generate DynamoDB partition key for a branch."""
        return f"REPO#{repo_id}"

    @staticmethod
    def generate_sk(branch_name: str) -> str:
        """Generate DynamoDB sort key for a branch."""
        return f"BRANCH#{branch_name}"

    def to_dynamodb_item(self) -> dict[str, Any]:
        """Serialize to DynamoDB item format."""
        item = {
            "PK": self.generate_pk(self.repo_id),
            "SK": self.generate_sk(self.branch_name),
            "repo_id": self.repo_id,
            "branch_name": self.branch_name,
            "last_commit_sha": self.last_commit_sha,
        }
        if self.commit_at is not None:
            item["commit_at"] = self.commit_at
        if self.ai_summary_ref is not None:
            item["ai_summary_ref"] = self.ai_summary_ref
        return item

    @classmethod
    def from_dynamodb_item(cls, item: dict[str, Any]) -> "Branch":
        """Deserialize from DynamoDB item format."""
        return cls(
            repo_id=item["repo_id"],
            branch_name=item["branch_name"],
            last_commit_sha=item["last_commit_sha"],
            commit_at=item.get("commit_at"),
            ai_summary_ref=item.get("ai_summary_ref"),
        )

    def to_json(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict for API responses."""
        result = {
            "repoId": self.repo_id,
            "branchName": self.branch_name,
            "lastCommitSha": self.last_commit_sha,
        }
        if self.commit_at is not None:
            result["commitAt"] = self.commit_at
        if self.ai_summary_ref is not None:
            result["aiSummaryRef"] = self.ai_summary_ref
        return result

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Branch":
        """Deserialize from JSON dict."""
        return cls(
            repo_id=data["repoId"],
            branch_name=data["branchName"],
            last_commit_sha=data["lastCommitSha"],
            commit_at=data.get("commitAt"),
            ai_summary_ref=data.get("aiSummaryRef"),
        )
