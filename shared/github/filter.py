"""Tree filtering logic for repository processing.

This module provides whitelist and blacklist filtering for repository trees,
determining which files and folders should be processed for summarization.

Ported from src/github/filterfile.py for the AWS serverless architecture.

Requirements: 5.4
"""

import re
from typing import List

from shared.github.client import TreeItem, TreeResult


# Whitelist patterns for files to include (matched against file path, case-insensitive)
WHITELISTED_FILE_PATTERNS = [
    r'\.py$',
    r'\.js$',
    r'\.ts$',
    r'\.java$',
    r'\.scala$',
    # Removed readme.md - redundant with folder summaries
    r'\.cpp$',
    r'\.cc$',
    r'\.cxx$',
    r'\.hpp$',
    r'\.hxx$',
    r'\.h$',
    r'\.go$',
    r'\.rb$',
    r'\.rs$',
    r'\.php$',
]

# Blacklist patterns for files to exclude (matched against file path)
BLACKLISTED_FILE_PATTERNS = [
    r'(^|/)\.[^/]+($|/)',  # File starting with a dot
    r'__\w+',  # __init__.py, __main__.py, etc.
    r'setup',  # setup.py, setup.js
    r'd\.ts',  # *.d.ts
    r'build',
    r'demo',
    r'entrypoint',
    r'example',
    r'sponsor',  # sponsors.js
    r'contrib',  # contributors.js
    r'gulpfile',
    r'webpack',
    r'\.min\.js',
    r'\.spec',  # *.spec.js, *.spec.ts
    r'types',
    # Skip documentation/config files - redundant with folder summaries
    r'readme\.md$',
    r'license',
    r'changelog',
    r'contributing',
    r'code_of_conduct',
    r'package\.json$',
    r'package-lock\.json$',
    r'tsconfig',
    r'eslint',
    r'prettier',
    r'\.config\.',
    r'makefile$',
    r'dockerfile$',
    r'docker-compose',
    r'requirements\.txt$',
    r'go\.mod$',
    r'go\.sum$',
    r'cargo\.toml$',
    r'cargo\.lock$',
    r'gemfile',
    r'yarn\.lock$',
]

# Blacklist patterns for folders to exclude (matched against folder path)
BLACKLISTED_FOLDER_PATTERNS = [
    r'(^|/)\.[^/]+($|/)',  # Folder starting with a dot
    r'__\w+',  # __pycache__, etc.
    r'appimage',
    r'appearance',
    r'art',
    r'assets',
    r'audio',
    r'bench',
    r'build',
    r'cache',
    r'changelog',
    r'ci',
    r'cmake',
    r'contrib',
    r'debug',
    r'demo',
    r'developer',
    r'docker',
    r'doc',
    r'e2e',
    r'example',
    r'extra',
    r'esm',
    r'guide',
    r'html',
    r'image',
    r'img',
    r'node_modules',
    r'output',
    r'public',
    r'picture',
    r'release',
    r'requirement',
    r'sample',
    r'script',
    r'setup',
    r'static',
    r'support',
    r'screenshot',
    r'target',
    r'temp',
    r'theme',
    r'third_party',
    r'tmp',
    r'vendor',
    r'video',
    r'workflows',
    r'locale',
    r'tutorial',
]


def _compile_patterns(patterns: List[str]) -> List[re.Pattern]:
    """Compile a list of regex pattern strings into Pattern objects."""
    return [re.compile(pattern) for pattern in patterns]


def _matches_any_pattern(text: str, patterns: List[re.Pattern]) -> bool:
    """Check if text matches any of the compiled patterns (case-insensitive)."""
    text_lower = text.lower()
    return any(pattern.search(text_lower) for pattern in patterns)


def filter_files_whitelist(paths: List[str], patterns: List[str]) -> List[str]:
    """Filter file paths to only include those matching whitelist patterns.
    
    Args:
        paths: List of file paths to filter.
        patterns: List of regex patterns for whitelisting.
        
    Returns:
        List of paths that match at least one whitelist pattern.
    """
    compiled_patterns = _compile_patterns(patterns)
    return [path for path in paths if _matches_any_pattern(path, compiled_patterns)]


def filter_files_blacklist(paths: List[str], patterns: List[str]) -> List[str]:
    """Filter file paths to exclude those matching blacklist patterns.
    
    Args:
        paths: List of file paths to filter.
        patterns: List of regex patterns for blacklisting.
        
    Returns:
        List of paths that don't match any blacklist pattern.
    """
    compiled_patterns = _compile_patterns(patterns)
    return [path for path in paths if not _matches_any_pattern(path, compiled_patterns)]


def filter_folders_blacklist(items: List[TreeItem], patterns: List[str]) -> List[TreeItem]:
    """Filter folder TreeItems to exclude those matching blacklist patterns.
    
    Args:
        items: List of TreeItem objects representing folders.
        patterns: List of regex patterns for blacklisting.
        
    Returns:
        List of TreeItems that don't match any blacklist pattern.
    """
    compiled_patterns = _compile_patterns(patterns)
    return [item for item in items if not _matches_any_pattern(item.path, compiled_patterns)]


def _is_path_under_blacklisted_folder(path: str, blacklisted_folders: set) -> bool:
    """Check if a path is under any blacklisted folder.
    
    Args:
        path: The file or folder path to check.
        blacklisted_folders: Set of blacklisted folder paths.
        
    Returns:
        True if the path is under a blacklisted folder.
    """
    parts = path.split('/')
    # Check all parent paths
    for i in range(len(parts)):
        parent_path = '/'.join(parts[:i + 1])
        if parent_path in blacklisted_folders:
            return True
    return False


def filter_tree(tree_result: TreeResult) -> TreeResult:
    """Filter a repository tree using whitelist and blacklist rules.
    
    This function applies the following filtering logic:
    1. Remove folders matching blacklist patterns
    2. Remove files under blacklisted folders
    3. Keep only files matching whitelist patterns
    4. Remove files matching file blacklist patterns
    
    The filtered tree is guaranteed to be a subset of the original tree
    (no new paths introduced, all paths in output exist in input).
    
    Args:
        tree_result: The TreeResult from GitHub API containing all tree items.
        
    Returns:
        A new TreeResult with filtered items.
        
    Validates: Requirements 5.4
    """
    # Separate files and folders
    files = [item for item in tree_result.items if item.type == 'blob']
    folders = [item for item in tree_result.items if item.type == 'tree']
    
    # Step 1: Filter folders using blacklist
    filtered_folders = filter_folders_blacklist(folders, BLACKLISTED_FOLDER_PATTERNS)
    
    # Build set of blacklisted folder paths for efficient lookup
    all_folder_paths = {folder.path for folder in folders}
    filtered_folder_paths = {folder.path for folder in filtered_folders}
    blacklisted_folder_paths = all_folder_paths - filtered_folder_paths
    
    # Step 2: Filter files - remove those under blacklisted folders
    files_not_under_blacklisted = [
        f for f in files 
        if not _is_path_under_blacklisted_folder(f.path, blacklisted_folder_paths)
    ]
    
    # Step 3: Apply whitelist to files
    file_paths = [f.path for f in files_not_under_blacklisted]
    whitelisted_paths = set(filter_files_whitelist(file_paths, WHITELISTED_FILE_PATTERNS))
    files_after_whitelist = [f for f in files_not_under_blacklisted if f.path in whitelisted_paths]
    
    # Step 4: Apply file blacklist
    file_paths_after_whitelist = [f.path for f in files_after_whitelist]
    final_file_paths = set(filter_files_blacklist(file_paths_after_whitelist, BLACKLISTED_FILE_PATTERNS))
    final_files = [f for f in files_after_whitelist if f.path in final_file_paths]
    
    # Step 5: Keep only folders that contain filtered files (or are ancestors of such folders)
    # Build set of all parent paths for filtered files
    needed_folder_paths = set()
    for file_item in final_files:
        parts = file_item.path.split('/')
        for i in range(len(parts) - 1):  # Exclude the file itself
            parent_path = '/'.join(parts[:i + 1])
            needed_folder_paths.add(parent_path)
    
    # Keep folders that are needed and weren't blacklisted
    final_folders = [f for f in filtered_folders if f.path in needed_folder_paths]
    
    # Combine and return
    filtered_items = final_folders + final_files
    
    return TreeResult(
        sha=tree_result.sha,
        items=filtered_items,
        truncated=tree_result.truncated,
    )


def count_filtered_files(tree_result: TreeResult) -> int:
    """Count the number of files in a filtered tree result.
    
    Args:
        tree_result: A TreeResult (typically after filtering).
        
    Returns:
        The count of file items (blobs) in the tree.
    """
    return sum(1 for item in tree_result.items if item.type == 'blob')
