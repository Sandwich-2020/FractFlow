"""
DeepSeek model implementation.

Provides implementation of the BaseModel interface for DeepSeek models.
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
from ..conversation.provider_adapters.deepseek_adapter import DeepSeekHistoryAdapter

logger = logging.getLogger(__name__)
config = ConfigManager()

# Define the tool calling instructions as a constant - this part is required for function calling to work
TOOL_CALLING_INSTRUCTIONS = """When tools are needed, include a JSON-formatted tool call anywhere in your response. You can use code blocks or inline JSON. The tool call should include the tool name and required arguments.

Common formats include:
```json
{"tool_call": {"name": "tool_name", "arguments": {"param1": "value1"}}}
```

For multiple tool calls, you can use:
```json
{"tool_calls": [{"name": "tool1", "arguments": {...}}, {"name": "tool2", "arguments": {...}}]}
```
If no tools are needed, simply provide a direct answer or explanation.

REMEMBER: ONLY USE TOOL THAT ARE AVAILABLE IN THE TOOLS LIST.
"""

# Default personality component that can be customized
DEFAULT_PERSONALITY = "You are an intelligent assistant. When users need specific information, you should use available tools to obtain it."

class DeepSeekToolCallingHelper:
    """
    Helper class for tool calling with DeepSeek models.
    
    Maintains simple context and enforces strict JSON format output.
    Uses DeepSeek's JSON output format capability.
    """
    
    def __init__(self):
        """Initialize the DeepSeek tool calling helper."""
        self.client = OpenAI(
            base_url=config.get('deepseek.base_url', 'https://api.deepseek.com'),
            api_key=config.get('deepseek.api_key')
        )
        self.model = config.get('deepseek.tool_calling_model', 'deepseek-chat')
        
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
        Execute a tool call using DeepSeek models.
        
        Args:
            instruction: The instruction to execute
            tools: List of available tools
            
        Returns:
            Tool call result in OpenAI format or None if failed
        """
        try:
            # Using DeepSeek's JSON output format capability
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
                # Parse the original simple tool call format
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
        Handle API call to DeepSeek.
        
        Args:
            **kwargs: Arguments to pass to the DeepSeek API
            
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

class DeepSeekModel(BaseModel):
    """
    Implementation of BaseModel for DeepSeek models.
    
    Handles user interaction, understands requirements, and generates
    high-quality tool calling instructions using DeepSeek's models.
    """
    
    def __init__(self):
        """
        Initialize the DeepSeek model.
        """
        self.client = OpenAI(
            base_url=config.get('deepseek.base_url', 'https://api.deepseek.com'),
            api_key=config.get('deepseek.api_key')
        )
        self.model = config.get('deepseek.model', 'deepseek-reasoner')
        
        # Get system prompt from config, or use default personality
        custom_system_prompt = config.get('agent.custom_system_prompt', DEFAULT_PERSONALITY)
        
        # Combine the custom prompt with the required tool calling instructions
        complete_system_prompt = f"{custom_system_prompt}\n\n{TOOL_CALLING_INSTRUCTIONS}"
        
        # Create conversation history with the complete system prompt
        self.history = ConversationHistory(complete_system_prompt)
        
        self.history_adapter = DeepSeekHistoryAdapter()
        self.tool_helper = DeepSeekToolCallingHelper()
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
            
            # Format history for DeepSeek using the adapter
            formatted_messages = self.history_adapter.format_for_model(
                self.history.get_messages(), tools
            )
            
            # Debug output for formatted history
            if self.debug_enabled:
                adapter_debug = self.history_adapter.format_debug_output(
                    formatted_messages, tools, "DEEPSEEK INPUT"
                )
                logger.info(f"Adapter conversion details:\n{adapter_debug}")

            # Get model response
            logger.info(f"Calling DeepSeek model: {self.model}")
            response = await self._create_chat_completion(
                model=self.model,
                messages=formatted_messages
            )
            
            if not response or not response.choices:
                logger.error("Failed to get response from DeepSeek model")
                return create_error_response(LLMError("Failed to get response from model"))
                
            content = response.choices[0].message.content
            logger.info(f"Received response from DeepSeek: {content[:100]}...")
            
            # 获取和记录reasoning_content
            reasoning_content = None
            if hasattr(response.choices[0].message, 'reasoning_content'):
                reasoning_content = response.choices[0].message.reasoning_content
                logger.info(f"Reasoning content from DeepSeek: {reasoning_content}")
            else:
                reasoning_content = None
                
            # Check if the response contains direct JSON tool calls
            tool_calls = self._extract_json_tool_calls(content) 
            
            # Legacy support: check for TOOL_INSTRUCTION format if no JSON tool calls found
            if not tool_calls:
                tool_instructions = self._extract_tool_instructions(content)
                
                if tool_instructions and tools:
                    logger.info(f"Extracted {len(tool_instructions)} tool instructions (legacy format)")
                    
                    # Process all tool instructions and generate multiple tool calls
                    tool_calls = []
                    for instruction in tool_instructions:
                        logger.info(f"Processing tool instruction: {instruction[:100]}...")
                        # Call the tool - this returns OpenAI-formatted tool calls
                        tool_call = await self.tool_helper.call_tool(instruction, tools)
                        if tool_call:
                            tool_calls.append(tool_call)
                            logger.info(f"Generated tool call: {json.dumps(tool_call)[:100]}...")
            
            if tool_calls:
                logger.info(f"Using {len(tool_calls)} tool calls")
                return {
                    "choices": [{
                        "message": {
                            "content": content,
                            "tool_calls": tool_calls,
                            "reasoning_content": reasoning_content
                        }
                    }]
                }
            else:
                # Direct response without tool call
                return {
                    "choices": [{
                        "message": {
                            "content": content,
                            "tool_calls": None, 
                            "reasoning_content": reasoning_content
                        }
                    }]
                }
                
        except Exception as e:
            error = handle_error(e)
            logger.error(f"Error in user interaction: {error}")
            return create_error_response(error)

    def _extract_json_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract JSON-formatted tool calls from content.
        
        Args:
            content: Content to extract tool calls from
            
        Returns:
            List of extracted tool calls in OpenAI format
        """
        tool_calls = []
        
        # First try to extract code blocks with json marker
        json_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", content, re.DOTALL)
        
        # If no code blocks found, try to extract any JSON-like structures
        if not json_blocks:
            # Look for potential JSON objects anywhere in the content
            potential_jsons = re.findall(r"\{[\s\S]*?\}", content, re.DOTALL)
            json_blocks.extend(potential_jsons)
        
        # Process all extracted blocks
        for block in json_blocks:
            try:
                # Clean up the block (remove leading/trailing whitespace)
                block = block.strip()
                
                # Parse the JSON
                parsed_json = json.loads(block)
                
                # Extract tool calls using different strategies
                extracted_calls = self._extract_tool_calls_from_json(parsed_json)
                if extracted_calls:
                    tool_calls.extend(extracted_calls)
                    
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from content block: {block[:50]}...")
                continue
        
        return tool_calls
    
    def _extract_tool_calls_from_json(self, json_obj: Any) -> List[Dict[str, Any]]:
        """
        Extract tool calls from parsed JSON using multiple strategies.
        Supports various JSON structures that might contain tool calls.
        
        Args:
            json_obj: Parsed JSON object (could be dict, list, or other structure)
            
        Returns:
            List of extracted tool calls in OpenAI format
        """
        extracted_calls = []
        
        # Strategy 1: Standard format with "tool_call" at root
        if isinstance(json_obj, dict) and "tool_call" in json_obj:
            tool_call = self._convert_to_openai_format(json_obj["tool_call"])
            if tool_call:
                extracted_calls.append(tool_call)
                
        # Strategy 2: Array format with "tool_calls" at root
        elif isinstance(json_obj, dict) and "tool_calls" in json_obj and isinstance(json_obj["tool_calls"], list):
            for item in json_obj["tool_calls"]:
                if isinstance(item, dict):
                    # Case 2.1: Nested tool_call format
                    if "tool_call" in item:
                        tool_call = self._convert_to_openai_format(item["tool_call"])
                    # Case 2.2: Direct tool call format
                    else:
                        tool_call = self._convert_to_openai_format(item)
                        
                    if tool_call:
                        extracted_calls.append(tool_call)
        
        # Strategy 3: Direct array of tool calls
        elif isinstance(json_obj, list):
            for item in json_obj:
                if isinstance(item, dict):
                    # Try both as a container or direct tool call
                    if "tool_call" in item:
                        tool_call = self._convert_to_openai_format(item["tool_call"])
                    else:
                        tool_call = self._convert_to_openai_format(item)
                        
                    if tool_call:
                        extracted_calls.append(tool_call)
        
        # Strategy 4: Check for any format with required fields
        elif isinstance(json_obj, dict) and "name" in json_obj and "arguments" in json_obj:
            tool_call = self._convert_to_openai_format(json_obj)
            if tool_call:
                extracted_calls.append(tool_call)
                
        return extracted_calls
    
    def _convert_to_openai_format(self, tool_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a tool call object to the OpenAI format.
        
        Args:
            tool_info: Tool information containing at least name and arguments
            
        Returns:
            Tool call in OpenAI format or None if invalid
        """
        if not isinstance(tool_info, dict) or "name" not in tool_info or "arguments" not in tool_info:
            return None
            
        try:
            # Generate a unique ID for this call
            call_id = f"call_{str(uuid.uuid4())[:8]}"
            
            # Extract function name
            name = tool_info["name"]
            
            # Extract and process arguments
            arguments = tool_info["arguments"]
            
            # Ensure arguments is a JSON string
            if not isinstance(arguments, str):
                arguments = json.dumps(arguments)
            
            # Create tool call in OpenAI format
            tool_call = {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": arguments
                }
            }
            
            logger.info(f"Extracted tool call: {name}")
            return tool_call
            
        except Exception as e:
            logger.warning(f"Failed to convert tool info to OpenAI format: {str(e)}")
            return None

    def _extract_tool_instructions(self, content: str) -> List[str]:
        """
        Extract all tool calling instructions from content.
        
        Args:
            content: Content to extract tool instructions from
            
        Returns:
            List of extracted tool instructions
        """
        pattern = r"TOOL_INSTRUCTION\n(.*?)\nEND_INSTRUCTION"
        matches = re.findall(pattern, content, re.DOTALL)
        return [match.strip() for match in matches] if matches else []

    def _extract_tool_instruction(self, content: str) -> Optional[str]:
        """
        Extract first tool calling instruction from content (legacy support).
        
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
        Handle API call to DeepSeek.
        
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