from typing import List, Optional

from llm.llm_config import LLMConfig
from llm.llm_provider import LLMProvider, HistoryItem

from openai import AsyncOpenAI


class OpenRouterProvider(LLMProvider):
    """
    LLM provider using the OpenRouter-compatible OpenAI client.
    """

    def __init__(self, api_key: str, model_name: str, llm_config: LLMConfig):
        super().__init__(api_key, model_name, llm_config, system_prompt="")
        self.llm = AsyncOpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

    async def run(self, user_prompt: str, history: Optional[List[HistoryItem]] = None) -> str:
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        completion = await self.llm.chat.completions.create(
            model=self.model_name,
            max_tokens=self.llm_config.max_token,
            temperature=self.llm_config.temperature,
            top_p=self.llm_config.top_p,
            messages=messages
        )

        return completion.choices[0].message.content
