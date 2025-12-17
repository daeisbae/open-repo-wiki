"""Code splitting utility for processing large files.

Ported from src/agent/code_splitter.py for the AWS serverless architecture.

Requirements: 5.6
"""

import logging
from typing import Optional


logger = logging.getLogger(__name__)


# Mapping of file extensions to language names
EXTENSION_TO_LANGUAGE = {
    "py": "python",
    "js": "javascript",
    "jsx": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
    "mjs": "javascript",
    "cjs": "javascript",
    "go": "go",
    "rb": "ruby",
    "rs": "rust",
    "php": "php",
    "cpp": "cpp",
    "cc": "cpp",
    "c": "c",
    "cxx": "cpp",
    "hpp": "cpp",
    "hxx": "cpp",
    "h": "c",
    "java": "java",
    "kt": "kotlin",
    "cs": "csharp",
    "scala": "scala",
    "swift": "swift",
    "lua": "lua",
    "pl": "perl",
    "hs": "haskell",
    "lhs": "haskell",
    "md": "markdown",
}


def get_language_from_extension(extension: str) -> Optional[str]:
    """Get the programming language for a file extension.
    
    Args:
        extension: File extension without the dot (e.g., 'py', 'js').
        
    Returns:
        Language name or None if not supported.
    """
    return EXTENSION_TO_LANGUAGE.get(extension.lower())


class CodeSplitter:
    """Splits code into numbered chunks for LLM processing.
    
    This helps the LLM understand line numbers and handle large files
    by splitting them into manageable chunks with overlap.
    
    Attributes:
        chunk_size: Number of lines per chunk.
        chunk_overlap: Number of overlapping lines between chunks.
    """

    def __init__(self, chunk_size: int = 50, chunk_overlap: int = 10):
        """Initialize the code splitter.
        
        Args:
            chunk_size: Number of lines per chunk.
            chunk_overlap: Number of overlapping lines between chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_code(self, file_extension: str, code: str) -> Optional[str]:
        """Split code into numbered chunks.
        
        Args:
            file_extension: File extension (e.g., 'py', 'js').
            code: The code content to split.
            
        Returns:
            Code with line numbers and chunk markers, or None if unsupported.
        """
        language = get_language_from_extension(file_extension)
        if not language:
            logger.warning(f"Unsupported language for extension: {file_extension}")
            return None

        lines = code.split("\n")
        total_lines = len(lines)
        
        if total_lines == 0:
            return ""
        
        chunks = []
        start = 0
        
        while start < total_lines:
            end = min(start + self.chunk_size, total_lines)
            chunk_lines = lines[start:end]
            
            # Create numbered lines for this chunk
            numbered_lines = []
            for i, line in enumerate(chunk_lines):
                current_line_num = start + i + 1  # 1-based indexing
                numbered_lines.append(f"{current_line_num}: {line}")
            
            numbered_content = "\n".join(numbered_lines)
            chunks.append(f"# Lines {start + 1} - {end}\n{numbered_content}\n\n")
            
            # If we reached the end, break
            if end == total_lines:
                break
            
            # Move start forward, accounting for overlap
            start += self.chunk_size - self.chunk_overlap
        
        return "".join(chunks)

    def split_code_simple(self, code: str) -> str:
        """Split code with line numbers without language check.
        
        Args:
            code: The code content to split.
            
        Returns:
            Code with line numbers.
        """
        lines = code.split("\n")
        numbered_lines = [f"{i + 1}: {line}" for i, line in enumerate(lines)]
        return "\n".join(numbered_lines)
