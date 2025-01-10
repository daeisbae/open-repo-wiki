from enum import Enum
from typing import Optional, List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

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


class LineNumberTextSplitter(RecursiveCharacterTextSplitter):
    """
    A custom text splitter that tracks and annotates line numbers for each chunk.
    """

    def create_documents(self, texts: List[str], **kwargs) -> List[Document]:
        documents = []
        current_line = 1  # Initialize the starting line number

        for text in texts:
            # Split the text into chunks using the parent class's method
            chunks = self.split_text(text)
            for chunk in chunks:
                # Calculate the number of lines in the chunk
                num_lines = chunk.count('\n') + 1
                doc = Document(
                    page_content=chunk,
                    metadata={
                        'loc': {
                            'lines': {
                                'from': current_line,
                                'to': current_line + num_lines - 1
                            }
                        }
                    }
                )
                documents.append(doc)
                current_line += num_lines  # Update the current line number

        return documents

class CodeSplitter:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        """
        Constructor for CodeSplitter.

        :param chunk_size: The size of each chunk.
        :param chunk_overlap: The number of overlapping characters between chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_code(self, file_extension: str, code: str) -> Optional[str]:
        """
        Splits the provided code into chunks based on the file extension.

        :param file_extension: The file extension indicating the programming language.
        :param code: The code content to be split.
        :return: The code with line numbers or None if the language is not supported.
        """
        language = get_language_from_extension(file_extension)
        if not language:
            logger.warning(f"Unsupported language for extension: {file_extension}")
            return None

        separators = RecursiveCharacterTextSplitter.get_separators_for_language(language.value)
        splitter = LineNumberTextSplitter(
            separators=separators,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len
        )

        try:
            docs = splitter.create_documents([code])
        except Exception as e:
            logger.critical(f"Error during splitting: {e}")
            return None

        doc_with_metadata = ''
        for doc in docs:
            loc = doc.metadata.get('loc', {})
            lines = loc.get('lines', {})
            from_line = lines.get('from', 'unknown')
            to_line = lines.get('to', 'unknown')
            doc_with_metadata += f'# Lines {from_line} - {to_line}\n{doc.page_content}\n\n'
        return doc_with_metadata