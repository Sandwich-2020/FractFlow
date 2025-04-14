"""
Model factory.

Factory for creating model implementations based on provider type.
"""

from typing import Optional
from .base_model import BaseModel
from ..infra.config import ConfigManager

config = ConfigManager()

def create_model(provider: Optional[str] = None) -> BaseModel:
    """
    Factory function to create an appropriate model based on the provider.
    
    Args:
        provider: The AI provider to use (e.g., 'openai', 'deepseek', 'qwen')
        
    Returns:
        An instance of BaseModel
        
    Raises:
        ImportError: If the specified provider module cannot be loaded
        ValueError: If the specified provider is not supported
    """
    # Use provider from args, or from config, or default to openai
    provider = provider or config.get('agent.provider', 'openai')
    
    if provider == 'deepseek':
        if config.get('deepseek.model') == 'deepseek-reasoner':
            from .deepseek_model_reasoner import DeepSeekModel
        else:
            from .deepseek_model import DeepSeekModel
        return DeepSeekModel()
    elif provider == 'qwen':
        from .qwen_model import QwenModel
        return QwenModel()
    elif provider == 'openai':
        # Note: This part would be properly implemented when OpenAIModel is created
        # For now, raising an error to indicate it's not implemented yet
        raise NotImplementedError("OpenAI provider support is not yet implemented")
    else:
        raise ValueError(f"Unsupported AI provider: {provider}") 