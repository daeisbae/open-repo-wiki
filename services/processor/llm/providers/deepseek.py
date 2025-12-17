"""DeepSeek LLM provider implementation.

Ported from src/llm/providers/deepseek.py for the AWS serverless architecture.

Requirements: 5.6, 5.7
"""

import logging
from typing import List, Optional

import httpx
from openai import AsyncOpenAI

from services.processor.llm.config import LLMConfig
from services.processor.llm.provider import LLMProvider, HistoryItem


logger = logging.getLogger(__name__)


class DeepSeekProvider(LLMProvider):
    """LLM provider for DeepSeek models.
    
    Uses the OpenAI-compatible API endpoint for DeepSeek.
    """

    DEEPSEEK_BASE_URL = "https://api.deepseek.com"

    def __init__(
        self,
        api_key: str,
        model_name: str,
        config: LLMConfig,
        system_prompt: Optional[str] = None,
    ):
        """Initialize the DeepSeek provider.
        
        Args:
            api_key: API key for DeepSeek service.
            model_name: Model identifier (e.g., 'deepseek-chat').
            config: LLM configuration parameters.
            system_prompt: Optional system prompt.
        """
        super().__init__(api_key, model_name, config, system_prompt)
        
        # Configure custom HTTP client with higher concurrency limits
        http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
            timeout=60.0
        )
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.DEEPSEEK_BASE_URL,
            http_client=http_client
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

        import time
        t0 = time.time()
        logger.info(f"Calling DeepSeek API with model {self.model_name} (async call start)")
        
        completion = await self.client.chat.completions.create(
            model=self.model_name,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            messages=messages,
        )

        response = completion.choices[0].message.content
        duration = time.time() - t0
        logger.info(f"DeepSeek response received in {duration:.2f}s: {len(response)} chars")
        
        return response
