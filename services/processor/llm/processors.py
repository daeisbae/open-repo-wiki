"""Code and folder processors for LLM summarization.

Ported from src/agent/index.py for the AWS serverless architecture.

Requirements: 5.6, 5.7
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from services.processor.llm.provider import LLMProvider
from services.processor.llm.schema import FileSchema, FolderSchema, SchemaParser
from services.processor.llm.code_splitter import CodeSplitter
from services.processor.llm.prompts import (
    CODE_PROMPT,
    FOLDER_PROMPT,
    FILE_PROMPT_TEMPLATE,
    FOLDER_PROMPT_TEMPLATE,
)


logger = logging.getLogger(__name__)


@dataclass
class RepoInfo:
    """Repository information for LLM context.
    
    Attributes:
        repo_owner: Repository owner (e.g., 'octocat').
        repo_name: Repository name (e.g., 'hello-world').
        commit_sha: Commit SHA for linking.
        path: File or folder path.
    """
    repo_owner: str
    repo_name: str
    commit_sha: str
    path: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "repo_owner": self.repo_owner,
            "repo_name": self.repo_name,
            "commit_sha": self.commit_sha,
            "path": self.path,
        }


class BaseProcessor:
    """Base class for LLM processors.
    
    Provides common functionality for code and folder processors.
    """

    def __init__(self, llm: LLMProvider):
        """Initialize the processor.
        
        Args:
            llm: LLM provider instance.
        """
        self.llm = llm
        self.schema_parser: Optional[SchemaParser] = None

    async def _process(self, prompt: str) -> Union[FileSchema, FolderSchema]:
        """Process a prompt through the LLM.
        
        Args:
            prompt: The formatted prompt to send to the LLM.
            
        Returns:
            Parsed schema from LLM response.
            
        Raises:
            ValueError: If parsing fails.
        """
        response = await self.llm.run(prompt)
        return self.schema_parser.parse(response)


class CodeProcessor(BaseProcessor):
    """Processor for generating file summaries.
    
    Takes code content and generates a structured summary using LLM.
    
    Requirements: 5.6
    """

    def __init__(self, llm: LLMProvider, chunk_size: int = 50, chunk_overlap: int = 10):
        """Initialize the code processor.
        
        Args:
            llm: LLM provider instance.
            chunk_size: Lines per chunk for code splitting.
            chunk_overlap: Overlapping lines between chunks.
        """
        super().__init__(llm)
        self.code_splitter = CodeSplitter(chunk_size, chunk_overlap)
        self.schema_parser = SchemaParser(FileSchema)

    async def generate(
        self,
        code: str,
        repo_info: Union[RepoInfo, Dict[str, str]],
    ) -> FileSchema:
        """Generate a summary for a code file.
        
        Args:
            code: The code content to summarize.
            repo_info: Repository information for context.
            
        Returns:
            FileSchema with usage and summary.
            
        Raises:
            ValueError: If code processing fails.
        """
        if isinstance(repo_info, dict):
            repo_info = RepoInfo(**repo_info)
        
        # Get file extension from path
        extension = repo_info.path.split(".")[-1] if "." in repo_info.path else ""
        
        # Split code into numbered chunks
        split_code = self.code_splitter.split_code(extension, code)
        if split_code is None:
            # Fallback to simple line numbering for unsupported languages
            split_code = self.code_splitter.split_code_simple(code)
        
        # Build the prompt
        prompt = FILE_PROMPT_TEMPLATE.format(
            requirements=CODE_PROMPT,
            format_instructions=self.schema_parser.format_instructions,
            repo_owner=repo_info.repo_owner,
            repo_name=repo_info.repo_name,
            commit_sha=repo_info.commit_sha,
            path=repo_info.path,
            code=split_code,
        )
        
        logger.debug(f"Generating summary for file: {repo_info.path}")
        return await self._process(prompt)


class FolderProcessor(BaseProcessor):
    """Processor for generating folder summaries.
    
    Takes child summaries and generates a folder-level summary using LLM.
    
    Requirements: 5.7
    """

    def __init__(self, llm: LLMProvider):
        """Initialize the folder processor.
        
        Args:
            llm: LLM provider instance.
        """
        super().__init__(llm)
        self.schema_parser = SchemaParser(FolderSchema)

    async def generate(
        self,
        ai_summaries: List[str],
        repo_info: Union[RepoInfo, Dict[str, str]],
    ) -> FolderSchema:
        """Generate a summary for a folder.
        
        Args:
            ai_summaries: List of child file/folder summaries.
            repo_info: Repository information for context.
            
        Returns:
            FolderSchema with usage, summary, and dependency graph.
            
        Raises:
            ValueError: If folder processing fails.
        """
        if isinstance(repo_info, dict):
            repo_info = RepoInfo(**repo_info)
        
        # Combine child summaries
        combined_summaries = "\n\n".join(ai_summaries)
        
        # Build the prompt
        prompt = FOLDER_PROMPT_TEMPLATE.format(
            requirements=FOLDER_PROMPT,
            format_instructions=self.schema_parser.format_instructions,
            repo_owner=repo_info.repo_owner,
            repo_name=repo_info.repo_name,
            commit_sha=repo_info.commit_sha,
            path=repo_info.path,
            ai_summaries=combined_summaries,
        )
        
        logger.debug(f"Generating summary for folder: {repo_info.path}")
        return await self._process(prompt)
