from typing import List, Optional
from db.utils.connector import AsyncDBConnector

class FolderData:
    def __init__(
            self,
            folder_id: int,
            name: str,
            path: str,
            parent_folder_id: Optional[int],
            ai_summary: Optional[str],
            branch_id: int,
            usage: Optional[str],
    ):
        self.folder_id = folder_id
        self.name = name
        self.path = path
        self.parent_folder_id = parent_folder_id
        self.ai_summary = ai_summary
        self.branch_id = branch_id
        self.usage = usage


class Folder:
    def __init__(self, db: AsyncDBConnector):
        self.db = db

    async def select(self, branch_id: int) -> List[FolderData]:
        query = "SELECT * FROM Folder WHERE branch_id = $1"
        rows = await self.db.query(query, [branch_id])
        results = []
        for row in rows:
            results.append(
                FolderData(
                    folder_id=row["folder_id"],
                    name=row["name"],
                    path=row["path"],
                    parent_folder_id=row["parent_folder_id"],
                    ai_summary=row["ai_summary"],
                    branch_id=row["branch_id"],
                    usage=row["usage"],
                )
            )
        return results

    async def insert(
            self,
            name: str,
            path: str,
            branch_id: int,
            parent_folder_id: Optional[int],
    ) -> FolderData:
        if parent_folder_id is None:
            query = """
                INSERT INTO Folder (name, path, branch_id)
                VALUES ($1, $2, $3)
                ON CONFLICT DO NOTHING
                RETURNING *;
            """
            values = [name, path, branch_id]
        else:
            query = """
                INSERT INTO Folder (name, path, branch_id, parent_folder_id)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT DO NOTHING
                RETURNING *;
            """
            values = [name, path, branch_id, parent_folder_id]

        rows = await self.db.query(query, values)
        if not rows:
            # Fetch existing
            if parent_folder_id is None:
                get_query = "SELECT * FROM Folder WHERE path = $1 AND branch_id = $2"
                get_values = [path, branch_id]
            else:
                get_query = """
                    SELECT * FROM Folder WHERE path = $1 AND branch_id = $2 AND parent_folder_id = $3
                """
                get_values = [path, branch_id, parent_folder_id]

            existing = await self.db.query(get_query, get_values)
            row = existing[0]
        else:
            row = rows[0]

        return FolderData(
            folder_id=row["folder_id"],
            name=row["name"],
            path=row["path"],
            parent_folder_id=row["parent_folder_id"],
            ai_summary=row["ai_summary"],
            branch_id=row["branch_id"],
            usage=row["usage"],
        )

    async def update(self, ai_summary: str, usage: str, folder_id: int) -> FolderData:
        query = """
            UPDATE Folder
            SET ai_summary = $1, usage = $2
            WHERE folder_id = $3
            RETURNING *;
        """
        rows = await self.db.query(query, [ai_summary, usage, folder_id])
        row = rows[0]
        return FolderData(
            folder_id=row["folder_id"],
            name=row["name"],
            path=row["path"],
            parent_folder_id=row["parent_folder_id"],
            ai_summary=row["ai_summary"],
            branch_id=row["branch_id"],
            usage=row["usage"],
        )

    async def delete(self, folder_id: int) -> None:
        query = "DELETE FROM Folder WHERE folder_id = $1"
        await self.db.query(query, [folder_id])