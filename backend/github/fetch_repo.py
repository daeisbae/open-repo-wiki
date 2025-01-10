from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

import aiohttp
import asyncio

from github.config import github_auth_config


@dataclass
class RepoDetails:
    repo_owner: str
    repo_name: str
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
class RepoTreeResult:
    path: str
    files: List[str]
    subdirectories: List['RepoTreeResult']


async def fetch_github_repo_details(owner: str, repo: str) -> RepoDetails:
    repo_url = f'https://api.github.com/repos/{owner}/{repo}'

    async with aiohttp.ClientSession() as session:
        async with session.get(repo_url, headers=github_auth_config, ssl=False) as repo_resp:
            if repo_resp.status != 200:
                raise Exception(f'GitHub API Error: {repo_resp.status}')
            repo_data = await repo_resp.json()

        tree_url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/{repo_data["default_branch"]}'
        async with session.get(tree_url, ssl=False) as tree_resp:
            if tree_resp.status != 200:
                raise Exception(f'GitHub API Error: {tree_resp.status}')
            tree_data = await tree_resp.json()

        return RepoDetails(
            repo_owner=repo_data['owner']['login'],
            repo_name=repo_data['name'],
            url=repo_data['html_url'],
            topics=repo_data.get('topics', []),
            language=repo_data.get('language'),
            description=repo_data.get('description'),
            stars=repo_data['stargazers_count'],
            forks=repo_data['forks_count'],
            default_branch=repo_data['default_branch'],
            sha=tree_data['sha'],
            commit_at=datetime.strptime(repo_data['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')
        )


async def fetch_github_repo_tree(owner: str, repo: str, commit_sha: str) -> RepoTreeResult:
    tree_url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/{commit_sha}?recursive=1'

    async with aiohttp.ClientSession() as session:
        async with session.get(tree_url, headers=github_auth_config, ssl=False) as resp:
            if resp.status != 200:
                raise Exception(f'GitHub API Error: {resp.status}')
            data = await resp.json()

        tree = data['tree']
        root_result = RepoTreeResult(path='', files=[], subdirectories=[])
        path_map = {'': root_result}

        for item in tree:
            path_map[item['path']] = RepoTreeResult(path=item['path'], files=[], subdirectories=[])

        for item in tree:
            current = path_map[item['path']]
            parent_path = item['path'].rpartition('/')[0]

            parent = path_map.get(parent_path)
            if parent is None:
                continue

            if item['type'] == 'blob':
                parent.files.append(item['path'])
            elif item['type'] == 'tree':
                parent.subdirectories.append(current)

        return root_result


async def fetch_github_repo_file(owner: str, repo: str, sha: str, path: str) -> str:
    code_url = f'https://raw.githubusercontent.com/{owner}/{repo}/{sha}/{path}'

    async with aiohttp.ClientSession() as session:
        async with session.get(code_url,headers=github_auth_config, ssl=False) as resp:
            if resp.status != 200:
                raise Exception(f'Failed to fetch file: {resp.status}')
            return await resp.text()
