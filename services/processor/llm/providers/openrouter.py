"""OpenRouter LLM provider implementation.

Ported from src/llm/providers/openrouter.py for the AWS serverless architecture.

Requirements: 5.6, 5.7
"""

import logging
from typing import List, Optional

from openai import AsyncOpenAI

from services.processor.llm.config import LLMConfig
from services.processor.llm.provider import LLMProvider, HistoryItem


logger = logging.getLogger(__name__)


class OpenRouterProvider(LLMProvider):
    """LLM provider for OpenRouter.
    
    Uses the OpenAI-compatible API endpoint for OpenRouter,
    which provides access to multiple LLM models.
    """

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str,
        model_name: str,
        config: LLMConfig,
        system_prompt: Optional[str] = None,
    ):
        """Initialize the OpenRouter provider.
        
        Args:
            api_key: API key for OpenRouter service.
            model_name: Model identifier (e.g., 'anthropic/claude-3-opus').
            config: LLM configuration parameters.
            system_prompt: Optional system prompt.
        """
        super().__init__(api_key, model_name, config, system_prompt)
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.OPENROUTER_BASE_URL,
        )

    async def run(
        self,
        user_prompt: str,
        history: Optional[List[HistoryItem]] = None,
    ) -> str:
        """Execute the LLM with the given prompt.
        
        Args:
            user_prompt: User input prompt.
            history: Optional conversation history (not used currently).
            
        Returns:
            The LLM response text.
            
        Raises:
            Exception: If the API call fails.
        """
        messages = []
        
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        messages.append({"role": "user", "content": user_prompt})

        logger.debug(f"Calling OpenRouter API with model {self.model_name}")
        
        completion = await self.client.chat.completions.create(
            model=self.model_name,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            messages=messages,
        )

        response = completion.choices[0].message.content
        logger.debug(f"OpenRouter response received: {len(response)} chars")
        
        return response
