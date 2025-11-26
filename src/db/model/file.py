from typing import List, Optional
from db.utils.connector import AsyncDBConnector

class FileData:
    def __init__(
            self,
            file_id: int,
            name: str,
            language: Optional[str],
            folder_id: int,
            content: str,
            ai_summary: Optional[str],
            usage: Optional[str],
    ):
        self.file_id = file_id
        self.name = name
        self.language = language
        self.folder_id = folder_id
        self.content = content
        self.ai_summary = ai_summary
        self.usage = usage


class File:
    def __init__(self, db: AsyncDBConnector):
        self.db = db

    async def select(self, folder_id: int) -> List[FileData]:
        query = "SELECT * FROM File WHERE folder_id = $1"
        rows = await self.db.query(query, [folder_id])
        results = []
        for row in rows:
            results.append(
                FileData(
                    file_id=row["file_id"],
                    name=row["name"],
                    language=row["language"],
                    folder_id=row["folder_id"],
                    content=row["content"],
                    ai_summary=row["ai_summary"],
                    usage=row["usage"],
                )
            )
        return results

    async def insert(
            self,
            name: str,
            folder_id: int,
            content: str,
            ai_summary: str,
            usage: str,
    ) -> Optional[FileData]:
        query = """
            INSERT INTO File (name, folder_id, content, ai_summary, usage)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT DO NOTHING
            RETURNING *;
        """
        rows = await self.db.query(query, [name, folder_id, content, ai_summary, usage])

        if not rows:
            # Possibly the row already exists; fetch it
            get_query = """
                SELECT * FROM File
                WHERE name = $1 AND folder_id = $2
            """
            existing = await self.db.query(get_query, [name, folder_id])
            if not existing:
                return None
            row = existing[0]
        else:
            row = rows[0]

        return FileData(
            file_id=row["file_id"],
            name=row["name"],
            language=row["language"],
            folder_id=row["folder_id"],
            content=row["content"],
            ai_summary=row["ai_summary"],
            usage=row["usage"],
        )