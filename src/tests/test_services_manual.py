import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Add src directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock Django setup
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[
            'wiki_app',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        }
    )
    django.setup()

from wiki_app.services import InsertRepoService
from github.fetch_repo import RepoTreeResult

async def test_summarize_folders():
    print("Testing _summarizeFolders...")
    
    # Mock LLMProvider
    mock_llm_provider = MagicMock()
    
    # Instantiate Service
    service = InsertRepoService(mock_llm_provider)
    
    # Mock Processors
    service.folderProcessor = AsyncMock()
    service.folderProcessor.generate.return_value = MagicMock(summary="Summary", usage={})
    
    # Mock DB calls
    service.folderPathMap = {"": 1, "/src": 2, "/src/utils": 3}
    
    # Mock Async Iterator
    class AsyncIterator:
        def __init__(self, items):
            self.items = iter(items)

        def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                return next(self.items)
            except StopIteration:
                raise StopAsyncIteration

    from wiki_app.models import Folder, File
    Folder.objects.filter = MagicMock(return_value=MagicMock(aupdate=AsyncMock()))
    
    # Mock File object
    mock_file = MagicMock()
    mock_file.name = "test.py"
    mock_file.ai_summary = "File Summary"
    
    # Make filter return a list containing the mock file
    File.objects.filter = MagicMock(return_value=AsyncIterator([mock_file]))

    # Create a dummy tree
    # /
    #   src/
    #     utils/
    tree = RepoTreeResult(
        path="",
        files=[],
        subdirectories=[
            RepoTreeResult(
                path="/src",
                files=[],
                subdirectories=[
                    RepoTreeResult(
                        path="/src/utils",
                        files=[],
                        subdirectories=[]
                    )
                ]
            )
        ]
    )
    
    # Mock update_status
    status_updates = []
    async def update_status(msg):
        print(f"Status Update: {msg}")
        status_updates.append(msg)
        
    # Run _summarizeFolders
    folder_progress = [0]
    await service._summarizeFolders(tree, update_status, folder_progress)
    
    print("\nVerification Results:")
    print(f"Total folders summarized: {folder_progress[0]}")
    print(f"Status updates: {status_updates}")
    
    if folder_progress[0] == 3:
        print("SUCCESS: Summarized 3 folders.")
    else:
        print(f"FAILURE: Expected 3 folders, got {folder_progress[0]}")

    if any("Summarized 1 folders..." in msg for msg in status_updates) and \
       any("Summarized 3 folders..." in msg for msg in status_updates):
        print("SUCCESS: Progress updates received.")
    else:
        print("FAILURE: Missing progress updates.")



if __name__ == "__main__":
    asyncio.run(test_summarize_folders())
