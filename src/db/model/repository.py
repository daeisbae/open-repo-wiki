from typing import List, Optional
from db.utils.connector import AsyncDBConnector


class RepositoryData:
    def __init__(
            self,
            url: str,
            owner: str,
            repo: str,
            language: str,
            descriptions: str,
            default_branch: str,
            stars: int,
            forks: int,
            topics: List[str],
    ):
        self.url = url
        self.owner = owner
        self.repo = repo
        self.language = language
        self.descriptions = descriptions
        self.default_branch = default_branch
        self.stars = stars
        self.forks = forks
        self.topics = topics


class Repository:
    """
    Provides async methods to interact with the `Repository` and related tables.
    """

    def __init__(self, db: AsyncDBConnector):
        self.db = db

    async def select(self, owner: str, repo: str) -> Optional[RepositoryData]:
        query_repo = "SELECT * FROM Repository WHERE owner = $1 AND repo = $2"
        query_topics = "SELECT topic_name FROM RepositoryTopics WHERE repository_url = $1"

        repo_rows = await self.db.query(query_repo, [owner, repo])
        if not repo_rows:
            return None

        repo_row = repo_rows[0]
        topics_rows = await self.db.query(query_topics, [repo_row["url"]])
        topics = [r["topic_name"] for r in topics_rows]

        return RepositoryData(
            url=repo_row["url"],
            owner=repo_row["owner"],
            repo=repo_row["repo"],
            language=repo_row["language"],
            descriptions=repo_row["descriptions"],
            default_branch=repo_row["default_branch"],
            stars=repo_row["stars"],
            forks=repo_row["forks"],
            topics=topics,
        )

    async def select_all(self) -> List[RepositoryData]:
        query_repo = "SELECT * FROM Repository"
        rows = await self.db.query(query_repo)
        results = []
        for row in rows:
            results.append(
                RepositoryData(
                    url=row["url"],
                    owner=row["owner"],
                    repo=row["repo"],
                    language=row["language"],
                    descriptions=row["descriptions"],
                    default_branch=row["default_branch"],
                    stars=row["stars"],
                    forks=row["forks"],
                    topics=[],  # Not fetched here
                )
            )
        return results

    async def insert(
            self,
            url: str,
            owner: str,
            repo: str,
            language: str,
            description: str,
            default_branch: str,
            topics: List[str],
            stars: int,
            forks: int,
    ) -> Optional[RepositoryData]:
        repo_query = """
            INSERT INTO Repository 
                (url, owner, repo, language, descriptions, default_branch, stars, forks)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (url) DO NOTHING
            RETURNING *;
        """
        repo_values = [url, owner, repo, language, description, default_branch, stars, forks]
        insert_result = await self.db.query(repo_query, repo_values)

        # If empty, row might already exist; fetch it
        if not insert_result:
            existing = await self.db.query("SELECT * FROM Repository WHERE url = $1", [url])
            if not existing:
                return None
            insert_result = existing

        # Upsert topics
        topic_insert = """
            INSERT INTO Topics (topic_name)
            VALUES ($1)
            ON CONFLICT (topic_name) DO NOTHING;
        """
        repo_topic_insert = """
            INSERT INTO RepositoryTopics (topic_name, repository_url)
            VALUES ($1, $2)
            ON CONFLICT (topic_name, repository_url) DO NOTHING;
        """

        for t in topics:
            await self.db.query(topic_insert, [t])
        for t in topics:
            await self.db.query(repo_topic_insert, [t, url])

        row = insert_result[0]
        return RepositoryData(
            url=row["url"],
            owner=row["owner"],
            repo=row["repo"],
            language=row["language"],
            descriptions=row["descriptions"],
            default_branch=row["default_branch"],
            stars=row["stars"],
            forks=row["forks"],
            topics=topics,
        )