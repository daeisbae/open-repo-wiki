from typing import List, Optional

from llm.llm_config import LLMConfig
from llm.llm_provider import LLMProvider, HistoryItem

from openai import AsyncOpenAI


class DeepSeekProvider(LLMProvider):
    """
    Concrete class implementing an LLMProvider for a "DeepSeek" model.
    Adjust to suit your actual API endpoint and usage.
    """

    def __init__(self, api_key: str, model_name: str, llm_config: LLMConfig):
        """
        Constructor for DeepSeekProvider (similar to OpenAI usage).

        :param api_key: API key for the DeepSeek or OpenAI service
        :param model_name: Model identifier (e.g. deepseek-chat)
        :param llm_config: Configuration for LLM
        """
        super().__init__(api_key, model_name, llm_config, system_prompt="")
        self.llm = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    async def run(self, user_prompt: str, history: Optional[List[HistoryItem]] = None) -> str:
        """
        Executes the LLM with the given prompt.

        :param user_prompt: User input prompt (The code will go inside here)
        :param history: The history of the conversation (optional)
        :return: The LLM response
        """

        messages = [{"role": "user", "content": user_prompt}]

        # Call the (hypothetical) ChatCompletion create method.
        completion = await self.llm.chat.completions.create(
            model=self.model_name,
            max_tokens=self.llm_config.max_token,
            temperature=self.llm_config.temperature,
            top_p=self.llm_config.top_p,
            messages=messages
        )

        return completion.choices[0].message.content
