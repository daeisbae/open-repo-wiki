"""Folder path collapsing logic for repository processing.

This module provides utilities to detect and collapse single-child folder chains
(e.g., java/com/example/) into single entries for more efficient summarization.

Requirements: Scrollable content design
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from shared.github.client import TreeItem, TreeResult


@dataclass
class CollapsedFolder:
    """Represents a collapsed folder path.
    
    Attributes:
        original_path: The leaf folder path (e.g., "java/com/example")
        display_name: Human-readable collapsed name (e.g., "java/com/example")
        collapsed_from: List of intermediate paths that were collapsed
        depth: The depth level in the tree (for sorting/display)
    """
    original_path: str
    display_name: str
    collapsed_from: List[str]
    depth: int


def collapse_single_child_folders(tree_result: TreeResult) -> Tuple[List[CollapsedFolder], Set[str]]:
    """Detect and collapse single-child folder chains.
    
    For folder structures like:
        java/
        java/com/
        java/com/example/
        java/com/example/MyClass.java
    
    This function detects that java/, java/com/ are single-child folders
    and collapses them into "java/com/example" as a single entry.
    
    Args:
        tree_result: The TreeResult from GitHub API.
        
    Returns:
        Tuple of:
        - List of CollapsedFolder objects for display
        - Set of folder paths that should be skipped (intermediate single-child folders)
    """
    # Separate files and folders
    files = [item for item in tree_result.items if item.type == 'blob']
    folders = [item for item in tree_result.items if item.type == 'tree']
    
    if not folders:
        return [], set()
    
    # Build parent -> children mapping
    folder_paths = {f.path for f in folders}
    children_map: Dict[str, List[str]] = defaultdict(list)
    
    # Also count files directly in each folder
    files_in_folder: Dict[str, int] = defaultdict(int)
    for f in files:
        parent = '/'.join(f.path.split('/')[:-1])
        if parent:
            files_in_folder[parent] += 1
    
    # Map each folder to its direct children (folders only)
    for folder_path in folder_paths:
        parts = folder_path.split('/')
        if len(parts) > 1:
            parent = '/'.join(parts[:-1])
            if parent in folder_paths:
                children_map[parent].append(folder_path)
    
    # Find root folders (no parent in the set)
    root_folders = []
    for folder_path in folder_paths:
        parts = folder_path.split('/')
        if len(parts) == 1:
            root_folders.append(folder_path)
        else:
            parent = '/'.join(parts[:-1])
            if parent not in folder_paths:
                root_folders.append(folder_path)
    
    # Collapse single-child chains
    collapsed_folders: List[CollapsedFolder] = []
    skip_folders: Set[str] = set()
    
    def find_collapse_chain(start_path: str, depth: int) -> CollapsedFolder:
        """Follow single-child chain and return collapsed folder."""
        chain = [start_path]
        current = start_path
        
        while True:
            children = children_map.get(current, [])
            direct_files = files_in_folder.get(current, 0)
            
            # Stop if folder has files directly in it, or has multiple children, or no children
            if direct_files > 0 or len(children) != 1:
                break
            
            # Continue down the single-child chain
            current = children[0]
            chain.append(current)
        
        # The leaf of the chain is what we summarize
        leaf_path = chain[-1]
        collapsed_from = chain[:-1]  # All intermediate folders
        
        # Mark intermediate folders to skip
        for intermediate in collapsed_from:
            skip_folders.add(intermediate)
        
        return CollapsedFolder(
            original_path=leaf_path,
            display_name=leaf_path,  # Show full collapsed path
            collapsed_from=collapsed_from,
            depth=depth,
        )
    
    # Process all root folders
    def process_folder(folder_path: str, depth: int):
        """Recursively process folders and handle collapsing."""
        if folder_path in skip_folders:
            return
        
        collapsed = find_collapse_chain(folder_path, depth)
        collapsed_folders.append(collapsed)
        
        # Process children of the collapsed folder
        for child in children_map.get(collapsed.original_path, []):
            process_folder(child, depth + 1)
    
    for root in sorted(root_folders):
        process_folder(root, 0)
    
    # Sort by path for consistent ordering
    collapsed_folders.sort(key=lambda cf: cf.original_path)
    
    return collapsed_folders, skip_folders


def get_folder_display_order(tree_result: TreeResult) -> List[str]:
    """Get folders in display order (depth-first, alphabetical).
    
    This is used for the scrollable content view to determine
    the order in which folder summaries should appear.
    
    Args:
        tree_result: The TreeResult from GitHub API.
        
    Returns:
        List of folder paths in display order.
    """
    collapsed, skip = collapse_single_child_folders(tree_result)
    return [cf.original_path for cf in collapsed]
