"""
Configuration management for the agent system.

Provides a unified interface for loading and accessing configuration
from various sources, including environment variables and config files.
"""

import os
import json
from typing import Any, Dict, Optional

class ConfigManager:
    """
    Manages configuration settings for the agent system.
    
    Provides a unified interface for accessing configuration values,
    allowing configuration to be set from various sources.
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
            
        # Initialize with default configuration
        self._config = self._get_default_config()
        self._initialized = True
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'openai': {
                'api_key': None,
                'base_url': None,
                'model': 'gpt-4',
                'tool_calling_model': 'gpt-3.5-turbo',
            },
            'deepseek': {
                'api_key': None,
                'base_url': 'https://api.deepseek.com',
                'model': 'deepseek-reasoner',
                'tool_calling_model': 'deepseek-chat',
            },
            'qwen': {
                'api_key': None,
                'base_url': 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1',
                'model': 'qwen-max',
                'tool_calling_model': 'qwen-turbo',
            },
            'agent': {
                'max_iterations': 10,
                'default_system_prompt': '',
                'provider': 'deepseek',  # Default provider is deepseek
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the complete configuration.
        
        Returns:
            A copy of the current configuration dictionary
        """
        # Return a deep copy to avoid modification of internal state
        return {
            'openai': dict(self._config.get('openai', {})),
            'deepseek': dict(self._config.get('deepseek', {})),
            'qwen': dict(self._config.get('qwen', {})),
            'agent': dict(self._config.get('agent', {})),
        }
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        Set multiple configuration values at once.
        
        Args:
            config: Configuration dictionary to set
        """
        # Process each section in the config
        for section, values in config.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    if value is not None:  # Skip None values
                        self.set(f"{section}.{key}", value)
            elif values is not None:  # Handle direct values like 'provider'
                self.set(section, values)
    
    def load_from_env(self, env_vars: Optional[Dict[str, str]] = None) -> None:
        """
        Load configuration from environment variables.
        
        Args:
            env_vars: Optional dictionary of environment variables.
                     If not provided, will use os.environ.
        """
        # Use provided env_vars or os.environ
        env = env_vars or os.environ
        
        # OpenAI Provider settings
        self.set('openai.api_key', env.get('COMPLETION_API_KEY'))
        self.set('openai.base_url', env.get('COMPLETION_BASE_URL'))
        self.set('openai.model', env.get('COMPLETION_MODEL_NAME', self.get('openai.model')))
        self.set('openai.tool_calling_model', env.get('TOOL_CALLING_MODEL', self.get('openai.tool_calling_model')))
        
        # DeepSeek Provider settings
        self.set('deepseek.api_key', env.get('DEEPSEEK_API_KEY'))
        self.set('deepseek.base_url', env.get('DEEPSEEK_BASE_URL', self.get('deepseek.base_url')))
        self.set('deepseek.model', env.get('DEEPSEEK_MODEL_NAME', self.get('deepseek.model')))
        self.set('deepseek.tool_calling_model', env.get('DEEPSEEK_TOOL_CALLING_MODEL', self.get('deepseek.tool_calling_model')))
        
        # QWEN Provider settings
        self.set('qwen.api_key', env.get('QWEN_API_KEY'))
        self.set('qwen.base_url', env.get('QWEN_BASE_URL', self.get('qwen.base_url')))
        self.set('qwen.model', env.get('QWEN_MODEL_NAME', self.get('qwen.model')))
        self.set('qwen.tool_calling_model', env.get('QWEN_TOOL_CALLING_MODEL', self.get('qwen.tool_calling_model')))
        
        # Agent settings
        max_iterations = env.get('MAX_ITERATIONS')
        if max_iterations is not None:
            try:
                self.set('agent.max_iterations', int(max_iterations))
            except ValueError:
                pass  # Use default if conversion fails
                
        self.set('agent.default_system_prompt', env.get('DEFAULT_SYSTEM_PROMPT', self.get('agent.default_system_prompt')))
        self.set('agent.provider', env.get('AI_PROVIDER', self.get('agent.provider')))
    
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
        # Skip None values to prevent overriding defaults
        if value is None:
            return
            
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
                
            # Instead of deep merging manually, use the set_config method
            self.set_config(file_config)
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
                if value is not None:  # Only set non-None values
                    target[key] = value 