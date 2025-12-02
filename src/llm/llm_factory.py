from llm.llm_config import LLMConfig
from llm.llm_provider import LLMProvider
from llm.providers.deepseek import DeepSeekProvider
from llm.providers.openrouter import OpenRouterProvider

import os
import dotenv

dotenv.load_dotenv()

LLMEnvConfig = {
    "provider": os.getenv('LLM_PROVIDER'),
    "apiKey": os.getenv('LLM_APIKEY'),
    "modelName": os.getenv('LLM_MODELNAME')
}


class LLMFactory:
    @staticmethod
    def create_provider(llm_config: LLMConfig) -> LLMProvider:
        if not LLMEnvConfig.get('provider'):
            raise Exception(
                'LLM Provider is not specified. Please set LLM_PROVIDER in the environment\nExample: '
                'LLM_PROVIDER=openrouter, LLM_PROVIDER=deepseek')

        if not LLMEnvConfig.get('modelName'):
            raise Exception('LLM Model name is not specified. Example: LLM_MODELNAME=llama3.3 for llama3.3')

        match LLMEnvConfig.get('provider'):
            case 'deepseek':
                return DeepSeekProvider(api_key=LLMEnvConfig.get('apiKey'), model_name=LLMEnvConfig.get('modelName'),
                                        llm_config=llm_config)
            case 'openrouter':
                return OpenRouterProvider(api_key=LLMEnvConfig.get('apiKey'), model_name=LLMEnvConfig.get('modelName'),
                                          llm_config=llm_config)
            case _:
                raise Exception('Unsupported LLM Provider')
