from typing import Optional
from db.utils.connector import AsyncDBConnector

class BranchData:
    def __init__(
            self,
            branch_id: int,
            last_commit_sha: str,
            name: str,
            repository_url: str,
            commit_at,
            created_at,
            ai_summary: Optional[str],
    ):
        self.branch_id = branch_id
        self.last_commit_sha = last_commit_sha
        self.name = name
        self.repository_url = repository_url
        self.commit_at = commit_at
        self.created_at = created_at
        self.ai_summary = ai_summary


class Branch:
    def __init__(self, db: AsyncDBConnector):
        self.db = db

    async def select(self, repository_url: str) -> Optional[BranchData]:
        query = "SELECT * FROM Branch WHERE repository_url = $1"
        rows = await self.db.query(query, [repository_url])
        if not rows:
            return None
        row = rows[0]
        return BranchData(
            branch_id=row["branch_id"],
            last_commit_sha=row["last_commit_sha"],
            name=row["name"],
            repository_url=row["repository_url"],
            commit_at=row["commit_at"],
            created_at=row["created_at"],
            ai_summary=row["ai_summary"],
        )

    async def insert(
            self,
            sha: str,
            name: str,
            repository_url: str,
            commit_at,
    ) -> BranchData:
        query = """
            INSERT INTO Branch (last_commit_sha, name, repository_url, commit_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT DO NOTHING
            RETURNING *;
        """
        rows = await self.db.query(query, [sha, name, repository_url, commit_at])

        if not rows:
            # Must already exist; fetch it
            get_query = """
                SELECT * FROM Branch
                WHERE repository_url = $1 AND last_commit_sha = $2
            """
            existing = await self.db.query(get_query, [repository_url, sha])
            row = existing[0]
        else:
            row = rows[0]

        return BranchData(
            branch_id=row["branch_id"],
            last_commit_sha=row["last_commit_sha"],
            name=row["name"],
            repository_url=row["repository_url"],
            commit_at=row["commit_at"],
            created_at=row["created_at"],
            ai_summary=row["ai_summary"],
        )

    async def update(self, ai_summary: str, branch_id: int) -> BranchData:
        query = """
            UPDATE Branch
            SET ai_summary = $1
            WHERE branch_id = $2
            RETURNING *;
        """
        rows = await self.db.query(query, [ai_summary, branch_id])
        row = rows[0]
        return BranchData(
            branch_id=row["branch_id"],
            last_commit_sha=row["last_commit_sha"],
            name=row["name"],
            repository_url=row["repository_url"],
            commit_at=row["commit_at"],
            created_at=row["created_at"],
            ai_summary=row["ai_summary"],
        )