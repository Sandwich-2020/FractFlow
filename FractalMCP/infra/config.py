"""
Configuration management for the agent system.

Provides a unified interface for loading and accessing configuration
from various sources, including environment variables and config files.
"""

import os
import json
from typing import Any, Dict, Optional
from dotenv import load_dotenv

class ConfigManager:
    """
    Manages configuration settings for the agent system.
    
    Loads configuration from environment variables and/or config files,
    providing a unified interface for accessing configuration values.
    """
    
    _instance = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the config manager if not already initialized."""
        if getattr(self, '_initialized', False):
            return
            
        # Load environment variables from .env file
        load_dotenv()
        
        # Initialize configuration dictionary
        self._config = {}
        self._load_from_env()
        
        self._initialized = True
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # OpenAI Provider settings
        self._config['openai'] = {
            'api_key': os.getenv('COMPLETION_API_KEY'),
            'base_url': os.getenv('COMPLETION_BASE_URL'),
            'model': os.getenv('COMPLETION_MODEL_NAME', 'gpt-4'),
            'tool_calling_model': os.getenv('TOOL_CALLING_MODEL', 'gpt-3.5-turbo'),
        }
        
        # DeepSeek Provider settings
        self._config['deepseek'] = {
            'api_key': os.getenv('DEEPSEEK_API_KEY'),
            'base_url': os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
            'model': os.getenv('DEEPSEEK_MODEL_NAME', 'deepseek-reasoner'),
            'tool_calling_model': os.getenv('DEEPSEEK_TOOL_CALLING_MODEL', 'deepseek-chat'),
        }
        
        # QWEN Provider settings
        self._config['qwen'] = {
            'api_key': os.getenv('QWEN_API_KEY'),
            'base_url': os.getenv('QWEN_BASE_URL', 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1'),
            'model': os.getenv('QWEN_MODEL_NAME', 'qwen-max'),
            'tool_calling_model': os.getenv('QWEN_TOOL_CALLING_MODEL', 'qwen-turbo'),
        }
        print(self._config)
        
        # Agent settings
        self._config['agent'] = {
            'max_iterations': int(os.getenv('MAX_ITERATIONS', '10')),
            'default_system_prompt': os.getenv('DEFAULT_SYSTEM_PROMPT', ''),
            'provider': os.getenv('AI_PROVIDER', 'openai'),  # Default provider
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Dot-separated path to the configuration value (e.g. 'openai.api_key')
            default: Default value to return if the key is not found
            
        Returns:
            The configuration value, or the default if not found
        """
        parts = key.split('.')
        value = self._config
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
                
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Dot-separated path to the configuration value (e.g. 'openai.api_key')
            value: The value to set
        """
        parts = key.split('.')
        config = self._config
        
        for i, part in enumerate(parts[:-1]):
            if part not in config:
                config[part] = {}
            config = config[part]
            
        config[parts[-1]] = value
    
    def load_from_file(self, file_path: str) -> None:
        """
        Load configuration from a JSON file.
        
        Args:
            file_path: Path to the JSON configuration file
        """
        try:
            with open(file_path, 'r') as f:
                file_config = json.load(f)
                
            # Merge with existing configuration
            self._deep_merge(self._config, file_config)
        except Exception as e:
            print(f"Error loading configuration from {file_path}: {e}")
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Deep merge two dictionaries.
        
        Args:
            target: The target dictionary to merge into
            source: The source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value 