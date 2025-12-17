"""Repository data model for DynamoDB Main table.

DynamoDB Schema:
- PK: REPO#<repoId>
- SK: META
- Attributes: owner, name, default_branch, stars, forks, language, github_url, created_at
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Repo:
    """Repository metadata record.
    
    Validates: Requirements 2.2
    """
    repo_id: str
    owner: str
    name: str
    default_branch: str
    stars: int = 0
    forks: int = 0
    language: Optional[str] = None
    github_url: Optional[str] = None
    created_at: Optional[str] = None

    @staticmethod
    def generate_repo_id(owner: str, name: str) -> str:
        """Generate a unique repo ID from owner and name."""
        return f"{owner}/{name}"

    @staticmethod
    def generate_pk(repo_id: str) -> str:
        """Generate DynamoDB partition key for a repository."""
        return f"REPO#{repo_id}"

    @staticmethod
    def generate_sk() -> str:
        """Generate DynamoDB sort key for a repository."""
        return "META"

    def to_dynamodb_item(self) -> dict[str, Any]:
        """Serialize to DynamoDB item format."""
        item = {
            "PK": self.generate_pk(self.repo_id),
            "SK": self.generate_sk(),
            "repo_id": self.repo_id,
            "owner": self.owner,
            "name": self.name,
            "default_branch": self.default_branch,
            "stars": self.stars,
            "forks": self.forks,
        }
        if self.language is not None:
            item["language"] = self.language
        if self.github_url is not None:
            item["github_url"] = self.github_url
        if self.created_at is not None:
            item["created_at"] = self.created_at
        return item

    @classmethod
    def from_dynamodb_item(cls, item: dict[str, Any]) -> "Repo":
        """Deserialize from DynamoDB item format."""
        return cls(
            repo_id=item["repo_id"],
            owner=item["owner"],
            name=item["name"],
            default_branch=item["default_branch"],
            stars=item.get("stars", 0),
            forks=item.get("forks", 0),
            language=item.get("language"),
            github_url=item.get("github_url"),
            created_at=item.get("created_at"),
        )

    def to_json(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict for API responses."""
        result = {
            "repoId": self.repo_id,
            "owner": self.owner,
            "name": self.name,
            "defaultBranch": self.default_branch,
            "stars": self.stars,
            "forks": self.forks,
        }
        if self.language is not None:
            result["language"] = self.language
        if self.github_url is not None:
            result["githubUrl"] = self.github_url
        if self.created_at is not None:
            result["createdAt"] = self.created_at
        return result

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Repo":
        """Deserialize from JSON dict."""
        return cls(
            repo_id=data["repoId"],
            owner=data["owner"],
            name=data["name"],
            default_branch=data["defaultBranch"],
            stars=data.get("stars", 0),
            forks=data.get("forks", 0),
            language=data.get("language"),
            github_url=data.get("githubUrl"),
            created_at=data.get("createdAt"),
        )
