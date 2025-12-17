"""TreeNode data model for DynamoDB Main table.

DynamoDB Schema:
- PK: REPO#<repoId>#BRANCH#<branchName>
- SK: NODE#<path>
- Attributes: type, parent_path, name, sha, size, language, summary_ref
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class NodeType(str, Enum):
    """Valid tree node types."""
    FOLDER = "folder"
    FILE = "file"


@dataclass
class TreeNode:
    """Tree node record for repository file/folder structure.
    
    Validates: Requirements 2.4
    """
    repo_id: str
    branch: str
    path: str
    node_type: NodeType
    name: str
    parent_path: str
    sha: Optional[str] = None
    size: Optional[int] = None
    language: Optional[str] = None
    summary_ref: Optional[str] = None

    @staticmethod
    def generate_pk(repo_id: str, branch: str) -> str:
        """Generate DynamoDB partition key for a tree node."""
        return f"REPO#{repo_id}#BRANCH#{branch}"

    @staticmethod
    def generate_sk(path: str) -> str:
        """Generate DynamoDB sort key for a tree node."""
        return f"NODE#{path}"

    def to_dynamodb_item(self) -> dict[str, Any]:
        """Serialize to DynamoDB item format."""
        item = {
            "PK": self.generate_pk(self.repo_id, self.branch),
            "SK": self.generate_sk(self.path),
            "repo_id": self.repo_id,
            "branch": self.branch,
            "path": self.path,
            "type": self.node_type.value,
            "name": self.name,
            "parent_path": self.parent_path,
        }
        if self.sha is not None:
            item["sha"] = self.sha
        if self.size is not None:
            item["size"] = self.size
        if self.language is not None:
            item["language"] = self.language
        if self.summary_ref is not None:
            item["summary_ref"] = self.summary_ref
        return item

    @classmethod
    def from_dynamodb_item(cls, item: dict[str, Any]) -> "TreeNode":
        """Deserialize from DynamoDB item format."""
        # Convert Decimal to int for size field
        size = item.get("size")
        if size is not None and hasattr(size, "__int__"):
            size = int(size)
            
        return cls(
            repo_id=item["repo_id"],
            branch=item["branch"],
            path=item["path"],
            node_type=NodeType(item["type"]),
            name=item["name"],
            parent_path=item["parent_path"],
            sha=item.get("sha"),
            size=size,
            language=item.get("language"),
            summary_ref=item.get("summary_ref"),
        )

    def to_json(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict for API responses."""
        result = {
            "type": self.node_type.value,
            "name": self.name,
            "path": self.path,
            "parentPath": self.parent_path,
            "hasSummary": self.summary_ref is not None and self.summary_ref != "",
        }
        if self.sha is not None:
            result["sha"] = self.sha
        if self.size is not None:
            result["size"] = self.size
        if self.language is not None:
            result["language"] = self.language
        return result

    @classmethod
    def from_json(cls, data: dict[str, Any], repo_id: str, branch: str) -> "TreeNode":
        """Deserialize from JSON dict.
        
        Note: repo_id and branch must be provided separately as they're not
        typically included in API responses.
        """
        return cls(
            repo_id=repo_id,
            branch=branch,
            path=data["path"],
            node_type=NodeType(data["type"]),
            name=data["name"],
            parent_path=data["parentPath"],
            sha=data.get("sha"),
            size=data.get("size"),
            language=data.get("language"),
            summary_ref=None,  # Not exposed in API responses
        )
