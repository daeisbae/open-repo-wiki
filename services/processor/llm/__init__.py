"""LLM integration for the processor service.

This module provides LLM provider abstraction and processors for generating
AI summaries of code files and folders.

Ported from src/llm/ and src/agent/ for the AWS serverless architecture.

Requirements: 5.6, 5.7
"""

from services.processor.llm.config import LLMConfig, LLMEnvConfig
from services.processor.llm.provider import LLMProvider, HistoryItem
from services.processor.llm.factory import LLMFactory
from services.processor.llm.processors import CodeProcessor, FolderProcessor, RepoInfo
from services.processor.llm.schema import FileSchema, FolderSchema, SchemaParser
from services.processor.llm.code_splitter import CodeSplitter, get_language_from_extension
from services.processor.llm.prompts import CODE_PROMPT, FOLDER_PROMPT

__all__ = [
    # Config
    "LLMConfig",
    "LLMEnvConfig",
    # Provider
    "LLMProvider",
    "HistoryItem",
    "LLMFactory",
    # Processors
    "CodeProcessor",
    "FolderProcessor",
    "RepoInfo",
    # Schema
    "FileSchema",
    "FolderSchema",
    "SchemaParser",
    # Utilities
    "CodeSplitter",
    "get_language_from_extension",
    # Prompts
    "CODE_PROMPT",
    "FOLDER_PROMPT",
]
