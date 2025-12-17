"""API Lambda handlers package.

This package contains Lambda handlers for the OpenRepoWiki API.

Lambda Entry Points:
- services.api.lambda_handler.jobs_handler: POST/GET /jobs endpoints
- services.api.lambda_handler.repos_handler: GET /repos endpoints

Handler Functions:
- create_job: POST /jobs - Create new processing job
- get_job: GET /jobs/{jobId} - Get job status
- get_tree: GET /repos/{repoId}/tree - List folder contents
- get_page: GET /repos/{repoId}/page - Get page content
"""

from services.api.lambda_handler import jobs_handler, repos_handler
from services.api.handlers import create_job, get_job, get_tree, get_page

__all__ = [
    # Lambda entry points
    "jobs_handler",
    "repos_handler",
    # Individual handlers
    "create_job",
    "get_job",
    "get_tree",
    "get_page",
]
