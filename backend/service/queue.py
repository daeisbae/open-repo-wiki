import asyncio
import aiohttp
from typing import List, Optional
from datetime import datetime, timezone

from github.ratelimit import check_rate_limit
from llm.llm_config import LLMConfig
from llm.llm_factory import LLMFactory
from service.insert_service import InsertRepoService, RepositoryData
from db.utils.connector import AsyncDBConnector
from llm.llm_provider import LLMProvider
from db.model.repository import Repository
from service.allowed_languages import ALLOWED_LANGUAGES

from loguru import logger

class InsertItem:
    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo


class AddRepositoryQueueResult:
    def __init__(self, success: bool, error: Optional[str] = None, message: Optional[str] = None):
        self.success = success
        self.error = error
        self.message = message


class InsertQueue:
    _instance: Optional["InsertQueue"] = None

    def __init__(self, db: AsyncDBConnector):
        self._db = db
        self._queue: List[InsertItem] = []
        self._isProcessing = False
        self._processingItem: Optional[InsertItem] = None
        self._processingTime: Optional[str] = None
        self._rateLimitBeforeStop: int = 500
        self._maxQueueSize: int = 25
        self.llm_config = LLMConfig(1, 0.95, 0, 8192)
        self._repoService = InsertRepoService(db, LLMFactory.create_provider(llm_config=self.llm_config))
        self._repository = Repository(db)

    @classmethod
    def getInstance(cls, db: AsyncDBConnector) -> "InsertQueue":
        if cls._instance is None:
            cls._instance = InsertQueue(db)
        return cls._instance

    @property
    def queue(self) -> List[InsertItem]:
        return self._queue

    @property
    def processingItem(self) -> Optional[InsertItem]:
        return self._processingItem

    @property
    def processingTime(self) -> Optional[str]:
        return self._processingTime

    async def add(self, item: InsertItem) -> AddRepositoryQueueResult:
        # Check if item is already in queue
        if any(i.owner == item.owner and i.repo == item.repo for i in self._queue):
            return AddRepositoryQueueResult(False, "Item already in queue")

        # Check if the repository is in DB (already exists)
        existing_repo = await self._repository.select(item.owner, item.repo)
        if existing_repo:
            return AddRepositoryQueueResult(False, "Item already in database")

        # Check queue size
        if len(self._queue) >= self._maxQueueSize:
            return AddRepositoryQueueResult(False, "Queue is full")

        # Check if the repository actually exists on GitHub
        logger.info(f"Asking GitHub if {item.owner}/{item.repo} exists...")
        github_api = f"https://api.github.com/repos/{item.owner}/{item.repo}"
        async with aiohttp.ClientSession() as session:
            async with session.get(github_api, ssl=False) as resp:
                if resp.status != 200:
                    return AddRepositoryQueueResult(False, "Repository does not exist")
                data = await resp.json()
                repo_language = data.get("language")
                if repo_language and repo_language not in ALLOWED_LANGUAGES:
                    return AddRepositoryQueueResult(
                        False,
                        f"Sorry, {repo_language} Language is not supported for analysis"
                    )

        self._queue.append(item)
        if not self._isProcessing:
            asyncio.create_task(self._processQueue())
        return AddRepositoryQueueResult(
            True,
            message=f"Repository {item.owner}/{item.repo} added to queue"
        )

    async def _processQueue(self):
        self._isProcessing = True
        while self._queue:
            rateLimit = await check_rate_limit()
            if rateLimit and rateLimit["remaining"] < self._rateLimitBeforeStop:
                logger.info("Rate limit reached. Stopping queue processing.")
                waitTime = (rateLimit["reset"] - int(datetime().now().timestamp())) * 1000
                if waitTime < 0:
                    waitTime = 0
                logger.info(f"Waiting for {waitTime / 1000} seconds")
                await asyncio.sleep(waitTime / 1000 + 1)
                continue

            item = self._queue.pop(0)
            await self._processItem(item)

        self._isProcessing = False

    async def _processItem(self, item: InsertItem) -> Optional[RepositoryData]:
        logger.info(f"Processing item: {item.owner}/{item.repo}")
        self._processingTime = datetime.now(timezone.utc)
        self._processingItem = item
        result = None
        try:
            result = await self._repoService.insertRepository(item.owner, item.repo)
        except Exception as e:
            logger.error(f"Failed to process item: {item.owner}/{item.repo}, error: {e}")
        self._processingItem = None
        self._processingTime = None
        return result
