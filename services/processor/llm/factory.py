"""LLM factory for creating provider instances.

Ported from src/llm/llm_factory.py for the AWS serverless architecture.

Requirements: 5.6, 5.7
"""

import logging
import os
from typing import Optional

from services.processor.llm.config import LLMConfig, LLMEnvConfig
from services.processor.llm.provider import LLMProvider
from services.processor.llm.providers.deepseek import DeepSeekProvider
from services.processor.llm.providers.openrouter import OpenRouterProvider


logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating LLM provider instances.
    
    Supports creating providers based on environment configuration
    or explicit parameters.
    """

    SUPPORTED_PROVIDERS = {
        "deepseek": DeepSeekProvider,
        "openrouter": OpenRouterProvider,
    }

    @classmethod
    def create_provider(
        cls,
        config: LLMConfig,
        env_config: Optional[LLMEnvConfig] = None,
    ) -> LLMProvider:
        """Create an LLM provider instance.
        
        Args:
            config: LLM generation configuration.
            env_config: Optional environment configuration. If not provided,
                       will attempt to read from environment variables.
                       
        Returns:
            An LLM provider instance.
            
        Raises:
            ValueError: If provider is not specified or not supported.
        """
        if env_config is None:
            env_config = LLMEnvConfig.from_env(os.environ)
        
        if env_config is None:
            raise ValueError(
                "LLM configuration not found. Please set LLM_PROVIDER, "
                "LLM_APIKEY, and LLM_MODELNAME environment variables."
            )
        
        provider_name = env_config.provider.lower()
        
        if provider_name not in cls.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported LLM provider: {provider_name}. "
                f"Supported providers: {list(cls.SUPPORTED_PROVIDERS.keys())}"
            )
        
        provider_class = cls.SUPPORTED_PROVIDERS[provider_name]
        
        logger.info(f"Creating LLM provider: {provider_name} with model {env_config.model_name}")
        
        return provider_class(
            api_key=env_config.api_key,
            model_name=env_config.model_name,
            config=config,
        )

    @classmethod
    def create_from_env(cls, config: Optional[LLMConfig] = None) -> Optional[LLMProvider]:
        """Create an LLM provider from environment variables.
        
        Args:
            config: Optional LLM configuration. Uses defaults if not provided.
            
        Returns:
            An LLM provider instance, or None if environment is not configured.
        """
        env_config = LLMEnvConfig.from_env(os.environ)
        
        if env_config is None:
            logger.warning("LLM environment not configured, skipping LLM provider creation")
            return None
        
        if config is None:
            config = LLMConfig()
        
        try:
            return cls.create_provider(config, env_config)
        except ValueError as e:
            logger.error(f"Failed to create LLM provider: {e}")
            return None
