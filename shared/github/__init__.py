"""GitHub API client and tree filtering for async operations.

This module provides an async GitHub client for fetching repository
details, trees, and file contents, as well as tree filtering utilities.
"""

from shared.github.client import (
    GitHubClient,
    GitHubAPIError,
    RepoDetails,
    TreeItem,
    TreeResult,
)
from shared.github.filter import (
    filter_tree,
    filter_files_whitelist,
    filter_files_blacklist,
    filter_folders_blacklist,
    count_filtered_files,
    WHITELISTED_FILE_PATTERNS,
    BLACKLISTED_FILE_PATTERNS,
    BLACKLISTED_FOLDER_PATTERNS,
)
from shared.github.collapse import (
    collapse_single_child_folders,
    get_folder_display_order,
    CollapsedFolder,
)

__all__ = [
    # Client
    "GitHubClient",
    "GitHubAPIError",
    "RepoDetails",
    "TreeItem",
    "TreeResult",
    # Filter
    "filter_tree",
    "filter_files_whitelist",
    "filter_files_blacklist",
    "filter_folders_blacklist",
    "count_filtered_files",
    "WHITELISTED_FILE_PATTERNS",
    "BLACKLISTED_FILE_PATTERNS",
    "BLACKLISTED_FOLDER_PATTERNS",
    # Collapse
    "collapse_single_child_folders",
    "get_folder_display_order",
    "CollapsedFolder",
]

