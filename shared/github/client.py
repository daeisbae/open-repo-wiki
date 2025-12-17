"""Async GitHub API client.

This module provides an async client for interacting with the GitHub API
to fetch repository details, file trees, and file contents.

Ported from src/github/fetch_repo.py with async aiohttp support.

Requirements: 5.2, 5.3
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional
import os

import aiohttp


class GitHubAPIError(Exception):
    """Exception raised for GitHub API errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"GitHub API Error ({status_code}): {message}")


@dataclass
class RepoDetails:
    """Repository details fetched from GitHub API.
    
    Validates: Requirements 5.2
    """
    owner: str
    name: str
    url: str
    topics: List[str]
    language: Optional[str]
    description: Optional[str]
    stars: int
    forks: int
    default_branch: str
    sha: str
    commit_at: datetime


@dataclass
class TreeItem:
    """A single item in the repository tree."""
    path: str
    type: str  # 'blob' for files, 'tree' for directories
    sha: str
    size: Optional[int] = None  # Only present for blobs


@dataclass
class TreeResult:
    """Result of fetching a repository tree.
    
    Validates: Requirements 5.3
    """
    sha: str
    items: List[TreeItem]
    truncated: bool = False


class GitHubClient:
    """Async GitHub API client.
    
    This client provides methods for fetching repository details,
    file trees, and file contents using aiohttp for async HTTP requests.
    
    Usage:
        async with GitHubClient(token="your_token") as client:
            details = await client.fetch_repo_details("owner", "repo")
            tree = await client.fetch_repo_tree("owner", "repo", "sha")
            content = await client.fetch_file("owner", "repo", "sha", "path/to/file")
    
    Or without context manager:
        client = GitHubClient(token="your_token")
        details = await client.fetch_repo_details("owner", "repo")
        await client.close()
    """

    BASE_URL = "https://api.github.com"
    RAW_URL = "https://raw.githubusercontent.com"

    def __init__(self, token: Optional[str] = None):
        """Initialize the GitHub client.
        
        Args:
            token: GitHub personal access token. If not provided,
                   will attempt to read from GITHUB_TOKEN environment variable.
        """
        self._token = token or os.getenv("GITHUB_TOKEN")
        self._session: Optional[aiohttp.ClientSession] = None
        self._owns_session = False

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self._get_headers())
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        """Close the HTTP session if we own it."""
        if self._session and self._owns_session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "GitHubClient":
        """Async context manager entry."""
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def _request(self, url: str, raw: bool = False) -> Any:
        """Make an HTTP GET request.
        
        Args:
            url: The URL to request.
            raw: If True, return raw text instead of JSON.
            
        Returns:
            JSON response or raw text.
            
        Raises:
            GitHubAPIError: If the request fails.
        """
        session = await self._get_session()
        async with session.get(url, ssl=False) as response:
            if response.status != 200:
                error_text = await response.text()
                raise GitHubAPIError(response.status, error_text)
            if raw:
                return await response.text()
            return await response.json()


    async def fetch_repo_details(self, owner: str, repo: str) -> RepoDetails:
        """Fetch repository details from GitHub.
        
        Retrieves repository metadata including owner, name, default branch,
        stars, forks, language, and the latest commit SHA.
        
        Args:
            owner: Repository owner (user or organization).
            repo: Repository name.
            
        Returns:
            RepoDetails with repository metadata.
            
        Raises:
            GitHubAPIError: If the API request fails.
            
        Validates: Requirements 5.2
        """
        # Fetch repository metadata
        repo_url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        repo_data = await self._request(repo_url)

        # Fetch the tree SHA for the default branch
        default_branch = repo_data["default_branch"]
        tree_url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/{default_branch}"
        tree_data = await self._request(tree_url)

        # Parse commit timestamp
        pushed_at = repo_data.get("pushed_at")
        commit_at = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ") if pushed_at else datetime.utcnow()

        return RepoDetails(
            owner=repo_data["owner"]["login"],
            name=repo_data["name"],
            url=repo_data["html_url"],
            topics=repo_data.get("topics", []),
            language=repo_data.get("language"),
            description=repo_data.get("description"),
            stars=repo_data["stargazers_count"],
            forks=repo_data["forks_count"],
            default_branch=default_branch,
            sha=tree_data["sha"],
            commit_at=commit_at,
        )

    async def fetch_repo_tree(
        self, owner: str, repo: str, sha: str, recursive: bool = True
    ) -> TreeResult:
        """Fetch the repository file tree from GitHub.
        
        Retrieves the complete file tree for a given commit SHA.
        
        Args:
            owner: Repository owner (user or organization).
            repo: Repository name.
            sha: Commit or tree SHA to fetch.
            recursive: If True, fetch the entire tree recursively.
            
        Returns:
            TreeResult containing all tree items.
            
        Raises:
            GitHubAPIError: If the API request fails.
            
        Validates: Requirements 5.3
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/{sha}"
        if recursive:
            url += "?recursive=1"

        data = await self._request(url)

        items = []
        for item in data.get("tree", []):
            tree_item = TreeItem(
                path=item["path"],
                type=item["type"],
                sha=item["sha"],
                size=item.get("size"),
            )
            items.append(tree_item)

        return TreeResult(
            sha=data["sha"],
            items=items,
            truncated=data.get("truncated", False),
        )

    async def fetch_file(
        self,
        owner: str,
        repo: str,
        sha: str,
        path: str,
    ) -> str:
        """Fetch a file's content from GitHub.
        
        Retrieves the raw content of a file at a specific commit.
        
        Args:
            owner: Repository owner (user or organization).
            repo: Repository name.
            sha: Commit SHA or branch name.
            path: Path to the file within the repository.
            
        Returns:
            The file content as a string.
            
        Raises:
            GitHubAPIError: If the request fails.
        """
        url = f"{self.RAW_URL}/{owner}/{repo}/{sha}/{path}"
        return await self._request(url, raw=True)

    async def check_rate_limit(self) -> dict[str, Any]:
        """Check the current GitHub API rate limit status.
        
        Returns:
            Dictionary with rate limit information including:
            - limit: Maximum requests per hour
            - remaining: Requests remaining
            - reset: Unix timestamp when the limit resets
            - used: Requests used in current window
        """
        url = f"{self.BASE_URL}/rate_limit"
        data = await self._request(url)
        return data["resources"]["core"]
