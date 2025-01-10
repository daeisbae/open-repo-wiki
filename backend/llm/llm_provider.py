from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional

from llm.llm_config import LLMConfig


@dataclass
class HistoryItem:
    """
    Represents a single message in the conversation history.
    """
    role: str
    parts: List[Dict[str, str]]


class LLMProvider(ABC):
    """
    Abstract class for LLM providers (e.g. OpenAI, Gemini, etc.)
    """

    def __init__(
            self,
            api_key: str,
            model_name: str,
            llm_config: LLMConfig,
            system_prompt: Optional[str] = None
    ):
        """
        Constructor for LLMProvider

        :param api_key: API key for the LLM service (your secret key)
        :param model_name: Model identifier (e.g. gemini-1.5-pro)
        :param llm_config: Configuration for LLM
        :param system_prompt: System prompt for the LLM
        """
        self.api_key = api_key
        self.model_name = model_name
        self.llm_config = llm_config
        self.system_prompt = system_prompt

    @abstractmethod
    async def run(self, user_prompt: str, history: Optional[List[HistoryItem]] = None) -> str:
        """
        Executes the LLM with given prompt.

        :param user_prompt: User input prompt (The code will go inside here)
        :param history: The history of the conversation
        :raises NotImplementedError: When not implemented by child class
        :return: The LLM response
        """
        raise NotImplementedError("The LLM chat method run() must be implemented")
