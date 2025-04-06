"""
Model factory.

Factory for creating model implementations based on provider type.
"""

from typing import Optional
from .base_model import BaseModel
from ..infra.config import ConfigManager

config = ConfigManager()

def create_model(system_prompt: Optional[str] = None, provider: Optional[str] = None) -> BaseModel:
    """
    Factory function to create an appropriate model based on the provider.
    
    Args:
        system_prompt: Optional system prompt to use
        provider: The AI provider to use (e.g., 'openai', 'deepseek')
        
    Returns:
        An instance of BaseModel
        
    Raises:
        ImportError: If the specified provider module cannot be loaded
        ValueError: If the specified provider is not supported
    """
    # Use provider from args, or from config, or default to openai
    provider = provider or config.get('agent.provider', 'openai')
    
    if provider == 'deepseek':
        from .deepseek_model import DeepSeekModel
        return DeepSeekModel(system_prompt)
    elif provider == 'openai':
        # Import here to avoid circular dependencies
        # Note: OpenAI model not implemented yet - this is a placeholder
        from .openai_model import OpenAIModel
        return OpenAIModel(system_prompt)
    else:
        raise ValueError(f"Unsupported AI provider: {provider}") 