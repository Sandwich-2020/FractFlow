"""
QWEN model implementation.

Provides implementation of the BaseModel interface for QWEN models.
"""

import json
import logging
import re
import uuid
from typing import Dict, List, Any, Optional
from openai import OpenAI

from .base_model import BaseModel
from ..infra.config import ConfigManager
from ..infra.error_handling import LLMError, handle_error, create_error_response
from ..conversation.base_history import ConversationHistory
from ..conversation.provider_adapters.qwen_adapter import QwenHistoryAdapter

logger = logging.getLogger(__name__)
config = ConfigManager()

class QwenToolCallingHelper:
    """
    Helper class for tool calling with QWEN models.
    
    Maintains simple context and enforces strict JSON format output.
    Uses QWEN's OpenAI-compatible API.
    """
    
    def __init__(self):
        """Initialize the QWEN tool calling helper."""
        self.client = OpenAI(
            base_url=config.get('qwen.base_url', 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1'),
            api_key=config.get('qwen.api_key')
        )
        self.model = config.get('qwen.tool_calling_model', 'qwen-turbo')
        
    def create_system_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """
        Create a system prompt for JSON tool calling.
        
        Args:
            tools: List of available tools
            
        Returns:
            System prompt for the tool calling model
        """
        tools_description = "\n".join(
            f"- {tool['function']['name']}: {tool['function']['description']}"
            for tool in tools
        )
        
        return f"""You are a tool calling expert. Your task is to generate correct JSON format tool calls.

Available tools:
{tools_description}

You must output strictly in the following JSON format:
{{
    "name": "tool_name",
    "arguments": {{
        "parameter_name": "parameter_value"
    }}
}}

Output JSON only, no other text."""

    async def call_tool(self, instruction: str, tools: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Execute a tool call using QWEN models.
        
        Args:
            instruction: The instruction to execute
            tools: List of available tools
            
        Returns:
            Tool call result or None if failed
        """
        try:
            # Using QWEN's OpenAI-compatible API with JSON output format
            response = await self._create_chat_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.create_system_prompt(tools)},
                    {"role": "user", "content": instruction}
                ],
                response_format={"type": "json_object"}
            )
            
            if not response or not response.choices:
                return None
                
            content = response.choices[0].message.content.strip()
            
            try:
                simple_tool_call = json.loads(content)
                if "name" not in simple_tool_call or "arguments" not in simple_tool_call:
                    logger.error("Invalid tool call format")
                    return None
                
                # Convert to OpenAI format
                call_id = f"call_{str(uuid.uuid4())[:8]}"
                arguments = simple_tool_call["arguments"]
                # Ensure arguments is a JSON string
                if not isinstance(arguments, str):
                    arguments = json.dumps(arguments)
                
                # Create tool call in OpenAI format
                tool_call = {
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": simple_tool_call["name"],
                        "arguments": arguments
                    }
                }
                
                return tool_call
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                return None
                
        except Exception as e:
            error = handle_error(e, {"instruction": instruction})
            logger.error(f"Tool calling error: {error}")
            return None
            
    async def _create_chat_completion(self, **kwargs) -> Any:
        """
        Handle API call to QWEN.
        
        Args:
            **kwargs: Arguments to pass to the QWEN API
            
        Returns:
            The API response or None if failed
        """
        try:
            result = self.client.chat.completions.create(**kwargs)
            return await result if hasattr(result, "__await__") else result
        except Exception as e:
            error = handle_error(e, {"kwargs": kwargs})
            logger.error(f"API call error: {error}")
            return None

class QwenModel(BaseModel):
    """
    Implementation of BaseModel for QWEN models.
    
    Handles user interaction, understands requirements, and generates
    high-quality tool calling instructions using QWEN's models.
    """
    
    def __init__(self, system_prompt: str = ""):
        """
        Initialize the QWEN model.
        
        Args:
            system_prompt: Custom system prompt to use
        """
        self.client = OpenAI(
            base_url=config.get('qwen.base_url', 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1'),
            api_key=config.get('qwen.api_key')
        )
        self.model = config.get('qwen.model', 'qwen-max')
        
        # Create conversation history
        self.history = ConversationHistory(system_prompt or config.get('agent.default_system_prompt', '') or """You are an intelligent assistant. When users need specific information, you should use available tools to obtain it.
Your response should follow one of these formats:

1. If tools are needed:
TOOL_INSTRUCTION
<describe the tool and parameters you need here>
END_INSTRUCTION
<your other explanations or responses>

2. If no tools are needed:
Provide answer or explanation directly

Remember: Only use tools when specific information is truly needed. If you can answer directly, do so.""")
        
        self.history_adapter = QwenHistoryAdapter()
        self.tool_helper = QwenToolCallingHelper()
        self.debug_enabled = False  # Enable debugging

    async def execute(self, tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute the model with the current conversation history.
        
        Args:
            tools: List of tools available to the model
            
        Returns:
            Response with content and optional tool calls
        """
        try:
            # Debug output for raw history
            if self.debug_enabled:
                raw_history = self.history.format_debug_output()
                logger.info(f"Raw conversation history before adaptation:\n{raw_history}")
            
            # Format history for QWEN using the adapter
            formatted_messages = self.history_adapter.format_for_model(
                self.history.get_messages(), tools
            )
            
            # Debug output for formatted history
            if self.debug_enabled:
                adapter_debug = self.history_adapter.format_debug_output(
                    formatted_messages, tools, "QWEN INPUT"
                )
                logger.info(f"Adapter conversion details:\n{adapter_debug}")

            # Get model response
            logger.info(f"Calling QWEN model: {self.model}")
            response = await self._create_chat_completion(
                model=self.model,
                messages=formatted_messages
            )
            
            if not response or not response.choices:
                logger.error("Failed to get response from QWEN model")
                return create_error_response(LLMError("Failed to get response from model"))
                
            content = response.choices[0].message.content
            logger.info(f"Received response from QWEN: {content[:100]}...")
            
            # Check if the response contains a tool instruction
            tool_instruction = self._extract_tool_instruction(content)
            
            if tool_instruction and tools:
                logger.info(f"Extracted tool instruction: {tool_instruction[:100]}...")
                # Call the tool
                tool_call = await self.tool_helper.call_tool(tool_instruction, tools)
                
                if tool_call:
                    logger.info(f"Generated tool call: {json.dumps(tool_call)[:100]}...")
                    
                    return {
                        "choices": [{
                            "message": {
                                "content": content,
                                "tool_calls": [tool_call]
                            }
                        }]
                    }
                else:
                    logger.error("Failed to generate valid tool call")
                    return {
                        "choices": [{
                            "message": {
                                "content": content,
                                "tool_calls": None
                            }
                        }]
                    }
            else:
                # Direct response without tool call
                return {
                    "choices": [{
                        "message": {
                            "content": content,
                            "tool_calls": None
                        }
                    }]
                }
                
        except Exception as e:
            error = handle_error(e)
            logger.error(f"Error in user interaction: {error}")
            return create_error_response(error)

    def _extract_tool_instruction(self, content: str) -> Optional[str]:
        """
        Extract tool calling instruction from content.
        
        Args:
            content: Content to extract tool instruction from
            
        Returns:
            Extracted tool instruction or None if not found
        """
        pattern = r"TOOL_INSTRUCTION\n(.*?)\nEND_INSTRUCTION"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else None

    async def _create_chat_completion(self, **kwargs) -> Any:
        """
        Handle API call to QWEN.
        
        Args:
            **kwargs: Arguments to pass to the API
            
        Returns:
            The API response or None if failed
        """
        try:
            result = self.client.chat.completions.create(**kwargs)
            return await result if hasattr(result, "__await__") else result
        except Exception as e:
            error = handle_error(e, {"kwargs": kwargs})
            logger.error(f"API call error: {error}")
            return None

    def add_user_message(self, message: str) -> None:
        """
        Add a user message to the conversation history.
        
        Args:
            message: The user message content
        """
        self.history.add_user_message(message)
        if self.debug_enabled:
            logger.info(f"Added user message: {message[:50]}...")
        
    def add_assistant_message(self, message: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Add an assistant message to the conversation history.
        
        Args:
            message: The assistant message content
            tool_calls: Optional list of tool calls made by the assistant
        """
        self.history.add_assistant_message(message, tool_calls)
        if self.debug_enabled:
            logger.info(f"Added assistant message: {message[:50]}...")
        
    def add_tool_result(self, tool_name: str, result: str, tool_call_id: Optional[str] = None) -> None:
        """
        Add a tool result to the conversation history.
        
        Args:
            tool_name: Name of the tool that was called
            result: Result returned by the tool
            tool_call_id: Optional ID of the tool call this is responding to
        """
        self.history.add_tool_result(tool_name, result, tool_call_id)
        if self.debug_enabled:
            logger.info(f"Added tool result from {tool_name}: {result[:50]}...") 