from enum import Enum
from typing import Optional, List

from langchain_core.documents import Document
from langchain_text_splitters import Language

from loguru import logger

def get_language_from_extension(extension: str) -> Optional[Language]:
    """
    Retrieves the programming language associated with a given file extension.

    :param extension: The file extension excluding the dot (e.g., 'js', 'py').
    :return: The corresponding Language enum or None if not supported.
    """
    extension_to_language_map = {
        'py': Language.PYTHON,
        'js': Language.JS,
        'jsx': Language.JS,
        'ts': Language.TS,
        'tsx': Language.TS,
        'mjs': Language.JS,
        'cjs': Language.JS,
        'go': Language.GO,
        'rb': Language.RUBY,
        'rs': Language.RUST,
        'php': Language.PHP,
        'cpp': Language.CPP,
        'cc': Language.CPP,
        'c': Language.C,
        'cxx': Language.CPP,
        'hpp': Language.CPP,
        'hxx': Language.CPP,
        'h': Language.C,
        'java': Language.JAVA,
        'kt': Language.KOTLIN,
        'cs': Language.CSHARP,
        'scala': Language.SCALA,
        'swift': Language.SWIFT,
        'lua': Language.LUA,
        'pl': Language.PERL,
        'hs': Language.HASKELL,
        'lhs': Language.HASKELL,
        'md': Language.MARKDOWN
    }
    return extension_to_language_map.get(extension.lower())


class CodeSplitter:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        """
        Constructor for CodeSplitter.

        :param chunk_size: The size of each chunk in LINES.
        :param chunk_overlap: The number of overlapping LINES between chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_code(self, file_extension: str, code: str) -> Optional[str]:
        """
        Splits the provided code into chunks based on lines.

        :param file_extension: The file extension indicating the programming language.
        :param code: The code content to be split.
        :return: The code with line numbers or None if the language is not supported.
        """
        # We might still want to check language support, but line splitting is generic.
        # Keeping the check for consistency with previous logic.
        language = get_language_from_extension(file_extension)
        if not language:
            logger.warning(f"Unsupported language for extension: {file_extension}")
            return None

        lines = code.split('\n')
        total_lines = len(lines)
        
        chunks = []
        start = 0
        
        while start < total_lines:
            end = min(start + self.chunk_size, total_lines)
            chunk_lines = lines[start:end]
            
            # Create numbered lines for this chunk
            numbered_lines = []
            for i, line in enumerate(chunk_lines):
                current_line_num = start + i + 1 # 1-based indexing
                numbered_lines.append(f"{current_line_num}: {line}")
            
            numbered_content = '\n'.join(numbered_lines)
            chunks.append(f'# Lines {start + 1} - {end}\n{numbered_content}\n\n')
            
            # Move start forward, accounting for overlap
            # If we reached the end, break
            if end == total_lines:
                break
                
            start += self.chunk_size - self.chunk_overlap
            
        return "".join(chunks)