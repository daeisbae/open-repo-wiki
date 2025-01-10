from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the GITHUB_TOKEN environment variable
github_token = os.getenv('GITHUB_TOKEN')

# Construct the headers
github_auth_config = {
    'Authorization': f'Bearer {github_token}',
    'X-GitHub-Api-Version': '2022-11-28',
    'Accept': 'application/vnd.github+json'
}