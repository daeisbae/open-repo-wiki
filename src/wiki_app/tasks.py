from celery import shared_task
from asgiref.sync import async_to_sync
from .services import InsertRepoService
from llm.llm_factory import LLMFactory
from llm.llm_config import LLMConfig

@shared_task
def process_repository_task(owner, repo):
    llm_config = LLMConfig(1, 0.95, 0, 8192)
    service = InsertRepoService(LLMFactory.create_provider(llm_config=llm_config))
    async_to_sync(service.insertRepository)(owner, repo)
