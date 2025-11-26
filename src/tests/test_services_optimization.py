import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import time

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

async def test_fetch_and_insert_files_optimization():
    print("Testing _fetchAndInsertFiles optimization...")
    
    # Mock LLMProvider
    mock_llm_provider = MagicMock()
    
    # Instantiate Service
    service = InsertRepoService(mock_llm_provider)
    
    # Mock CodeProcessor
    service.codeProcessor = AsyncMock()
    service.codeProcessor.generate.return_value = MagicMock(summary="Summary", usage={})
    
    # Mock repoFileInfo
    service.repoFileInfo = {
        "repo_owner": "owner",
        "repo_name": "repo",
        "commit_sha": "sha"
    }
    
    # Mock folderPathMap
    service.folderPathMap = {"": 1}
    
    # Mock File.objects.abulk_create
    from wiki_app.models import File
    File.objects.abulk_create = AsyncMock()
    
    # Create a dummy tree with one file
    tree = RepoTreeResult(
        path="",
        files=["test.py"],
        subdirectories=[]
    )
    
    # Mock fetch_github_repo_file
    with patch('wiki_app.services.fetch_github_repo_file', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = "print('hello')"
        
        # Mock aiohttp.ClientSession
        # We need to mock the context manager
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await service._fetchAndInsertFiles(tree)
            
            # Verify fetch_github_repo_file called with session
            # args: owner, repo, sha, path, session
            mock_fetch.assert_called()
            args, _ = mock_fetch.call_args
            if args[4] == mock_session:
                print("SUCCESS: Session passed to fetch_github_repo_file.")
            else:
                print("FAILURE: Session NOT passed to fetch_github_repo_file.")
                
    # Verify abulk_create called
    if File.objects.abulk_create.called:
        print("SUCCESS: File.objects.abulk_create called.")
        # Check count
        args, _ = File.objects.abulk_create.call_args
        files_list = args[0]
        if len(files_list) == 1:
             print("SUCCESS: Correct number of files passed to bulk_create.")
        else:
             print(f"FAILURE: Expected 1 file, got {len(files_list)}")
    else:
        print("FAILURE: File.objects.abulk_create NOT called.")

if __name__ == "__main__":
    asyncio.run(test_fetch_and_insert_files_optimization())
