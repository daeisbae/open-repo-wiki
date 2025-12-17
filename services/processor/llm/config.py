"""LLM configuration module.

Ported from src/llm/llm_config.py for the AWS serverless architecture.

Requirements: 5.6, 5.7
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """Configuration class for LLM generation parameters.
    
    Attributes:
        temperature: Controls randomness in the output (0.0 to 2.0).
        top_p: Controls diversity via nucleus sampling (0.0 to 1.0).
        top_k: Controls diversity by limiting to K most likely tokens.
        max_tokens: Controls the max number of output tokens.
    """
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 4096

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if not (0.0 <= self.top_p <= 1.0):
            raise ValueError("Top-p must be between 0.0 and 1.0")
        if self.top_k < 1:
            raise ValueError("Top-k must be at least 1")
        if self.max_tokens < 1:
            raise ValueError("Max tokens must be at least 1")


@dataclass
class LLMEnvConfig:
    """Environment-based LLM configuration.
    
    Attributes:
        provider: LLM provider name (e.g., 'deepseek', 'openrouter').
        api_key: API key for the LLM service.
        model_name: Model identifier (e.g., 'deepseek-chat').
    """
    provider: str
    api_key: str
    model_name: str

    @classmethod
    def from_env(cls, env: dict) -> Optional["LLMEnvConfig"]:
        """Create config from environment variables.
        
        Args:
            env: Dictionary of environment variables.
            
        Returns:
            LLMEnvConfig if all required variables are present, None otherwise.
        """
        provider = env.get("LLM_PROVIDER")
        api_key = env.get("LLM_APIKEY")
        model_name = env.get("LLM_MODELNAME")
        
        if not all([provider, api_key, model_name]):
            return None
        
        return cls(
            provider=provider,
            api_key=api_key,
            model_name=model_name,
        )
