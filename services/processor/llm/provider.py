"""LLM provider abstraction.

Ported from src/llm/llm_provider.py for the AWS serverless architecture.

Requirements: 5.6, 5.7
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from services.processor.llm.config import LLMConfig


@dataclass
class HistoryItem:
    """Represents a single message in the conversation history.
    
    Attributes:
        role: The role of the message sender (e.g., 'user', 'assistant').
        parts: List of message parts with content.
    """
    role: str
    parts: List[Dict[str, str]] = field(default_factory=list)


class LLMProvider(ABC):
    """Abstract base class for LLM providers.
    
    Provides a common interface for different LLM services
    (e.g., OpenAI, DeepSeek, OpenRouter).
    
    Attributes:
        api_key: API key for the LLM service.
        model_name: Model identifier.
        config: LLM configuration parameters.
        system_prompt: Optional system prompt for the LLM.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str,
        config: LLMConfig,
        system_prompt: Optional[str] = None,
    ):
        """Initialize the LLM provider.
        
        Args:
            api_key: API key for the LLM service.
            model_name: Model identifier (e.g., 'deepseek-chat').
            config: Configuration for LLM generation parameters.
            system_prompt: Optional system prompt for the LLM.
        """
        self.api_key = api_key
        self.model_name = model_name
        self.config = config
        self.system_prompt = system_prompt

    @abstractmethod
    async def run(
        self,
        user_prompt: str,
        history: Optional[List[HistoryItem]] = None,
    ) -> str:
        """Execute the LLM with the given prompt.
        
        Args:
            user_prompt: User input prompt.
            history: Optional conversation history.
            
        Returns:
            The LLM response text.
            
        Raises:
            NotImplementedError: When not implemented by child class.
        """
        raise NotImplementedError("The LLM run() method must be implemented")
