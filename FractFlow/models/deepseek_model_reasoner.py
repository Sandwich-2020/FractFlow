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

# Instructions for the main reasoner model on how to request a tool call
TOOL_REQUEST_INSTRUCTIONS = """When you determine that a tool is needed to answer the user's request or perform an action, you MUST issue a tool request instruction. 
Do NOT attempt to generate the final tool call JSON yourself.

To request a tool call, include the following tag anywhere in your response, containing the specific instruction for the tool:
<tool_request>Instruction text for the tool call expert here.</tool_request>

For example:
User: What's the weather in London?
Assistant: Okay, I can find that for you.
<tool_request>Get the current weather for London, UK.</tool_request>

If no tool is needed, simply provide a direct answer or explanation without the <tool_request> tag."""

# Default personality component that can be customized
DEFAULT_PERSONALITY = "You are an intelligent assistant. You carefully analyze user requests and determine if external tools are needed."

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
        self.max_retries = 5  # Maximum number of retries for tool calls
        
    def create_system_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """
        Create a system prompt for JSON tool calling.
        
        Args:
            tools: List of available tools
            
        Returns:
            System prompt for the tool calling model
        """
        # List all available tools with names and descriptions
        tool_details = []
        for tool in tools:
            tool_name = tool['function']['name']
            description = tool['function'].get('description', 'No description available')
            
            # List all parameters for this tool
            params = tool['function'].get('parameters', {}).get('properties', {})
            param_list = ", ".join(params.keys()) if params else "No parameters"
            
            tool_details.append(f"- {tool_name}: {description}\n  Parameters: {param_list}")
        
        tools_text = "\n".join(tool_details)
        
        return f"""You are a tool calling expert. Your task is to generate correct JSON format tool calls based ONLY on the tools that are available.

AVAILABLE TOOLS (ONLY USE THESE - DO NOT INVENT NEW ONES):
{tools_text}

IMPORTANT RULES:
1. ONLY use tool names from the list above - never invent new tool names
2. ONLY use parameter names that are listed for each tool - never invent new parameters
3. If a requested tool doesn't exactly match any available tool, use the closest matching one

You must output strictly in the following JSON format:
{{
    "function": {{
        "name": "tool_name",
        "arguments": "{{\\\"parameter_name\\\": \\\"parameter_value\\\"}}",
    }}
}}

Output JSON only, no other text. The arguments must be a valid JSON string (with escaped quotes)."""

    async def call_tool(self, instruction: str, tools: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Execute a tool call using DeepSeek models with retry mechanism.
        
        Args:
            instruction: The instruction to execute
            tools: List of available tools
            
        Returns:
            Tool call result in OpenAI format or None if all retries failed
        """
        available_tools = [tool['function']['name'] for tool in tools]
        
        # Try multiple times to get a valid tool call
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Tool call attempt {attempt+1}/{self.max_retries}")
                
                # Call the internal method to get a tool call
                tool_call = await self._internal_call_tool(instruction, tools)
                
                # Skip if no response was received
                if not tool_call:
                    logger.warning(f"No response from model on attempt {attempt+1}")
                    continue
                
                # Validate the tool call
                if not self._validate_tool_call(tool_call, available_tools):
                    logger.warning(f"Invalid tool call on attempt {attempt+1}: {tool_call}")
                    continue
                
                # If we got here, the tool call is valid
                logger.debug(f"Valid tool call generated on attempt {attempt+1}")
                return tool_call
                
            except Exception as e:
                error = handle_error(e, {"instruction": instruction, "attempt": attempt+1})
                logger.error(f"Error on tool call attempt {attempt+1}: {error}")
                # Continue to the next attempt rather than failing immediately
        
        # If we exhausted all retries without success
        logger.error(f"Failed to generate valid tool call after {self.max_retries} attempts")
        return None
    
    async def _internal_call_tool(self, instruction: str, tools: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Internal method to call the DeepSeek model and get a tool call response.
        
        Args:
            instruction: The instruction to execute
            tools: List of available tools
            
        Returns:
            Raw tool call from the model or None if failed
        """
        try:
            # Call DeepSeek with JSON output format
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
            
            # Parse the JSON response
            try:
                model_response = json.loads(content)
                
                # Add the ID and type fields if the model didn't provide them
                call_id = f"call_{str(uuid.uuid4())[:8]}"
                tool_call = {
                    "id": call_id,
                    "type": "function",
                    "function": model_response.get("function", {})
                }
                
                return tool_call
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}\nContent: {content[:100]}...")
                return None
                
        except Exception as e:
            error = handle_error(e, {"instruction": instruction})
            logger.error(f"Internal tool calling error: {error}")
            return None
    
    def _validate_tool_call(self, tool_call: Dict[str, Any], available_tools: List[str]) -> bool:
        """
        Validate that a tool call has the correct format and references an available tool.
        
        Args:
            tool_call: The tool call to validate
            available_tools: List of available tool names
            
        Returns:
            True if the tool call is valid, False otherwise
        """
        # Check that the required fields are present
        if not isinstance(tool_call, dict):
            logger.error("Tool call is not a dictionary")
            return False
            
        if "type" not in tool_call or tool_call["type"] != "function":
            logger.error("Tool call is not a function call")
            return False
            
        if "function" not in tool_call or not isinstance(tool_call["function"], dict):
            logger.error("Tool call has no function object")
            return False
            
        function = tool_call["function"]
        if "name" not in function or "arguments" not in function:
            logger.error("Function object missing name or arguments")
            return False
            
        # Verify that the tool exists
        tool_name = function["name"]
        if tool_name not in available_tools:
            logger.error(f"Tool '{tool_name}' not in available tools: {available_tools}")
            return False
            
        # Verify that the arguments is a valid JSON string
        arguments = function["arguments"]
        if not isinstance(arguments, str):
            logger.error("Arguments must be a string")
            return False
            
        try:
            # Attempt to parse the arguments as JSON
            json.loads(arguments)
        except json.JSONDecodeError:
            logger.error(f"Arguments is not valid JSON: {arguments[:100]}...")
            return False
            
        # Everything looks good
        return True
            
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
        complete_system_prompt = f"{custom_system_prompt}\n\n{TOOL_REQUEST_INSTRUCTIONS}"
        
        # Create conversation history with the complete system prompt
        self.history = ConversationHistory(complete_system_prompt)
        
        self.history_adapter = DeepSeekHistoryAdapter()
        self.tool_helper = DeepSeekToolCallingHelper()
        self.debug_enabled = False  # Enable debugging

    async def execute(self, tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute the model with the current conversation history.
        The model decides if a tool is needed and provides an instruction.
        If an instruction is found, it's passed to the tool_helper for robust generation.
        
        Args:
            tools: List of tools available to the model
            
        Returns:
            Response with content and optional tool calls
        """
        try:
            # Debug output for raw history
            if self.debug_enabled:
                raw_history = self.history.format_debug_output()
                logger.debug(f"Raw conversation history before adaptation:\n{raw_history}")
            
            # Format history for DeepSeek using the adapter
            # Pass tools=None here, as the main model only generates instructions, not calls
            formatted_messages = self.history_adapter.format_for_model(
                self.history.get_messages(), tools=None  
            )
            
            # Debug output for formatted history
            if self.debug_enabled:
                adapter_debug = self.history_adapter.format_debug_output(
                    formatted_messages, None, "DEEPSEEK REASONER INPUT"
                )
                logger.debug(f"Adapter conversion details:\n{adapter_debug}")

            # Get model response
            logger.debug(f"Calling DeepSeek reasoner model: {self.model}")
            response = await self._create_chat_completion(
                model=self.model,
                messages=formatted_messages
            )
            
            if not response or not response.choices:
                logger.error("Failed to get response from DeepSeek reasoner model")
                return create_error_response(LLMError("Failed to get response from model"))
                
            content = response.choices[0].message.content
            logger.debug(f"Received response from reasoner: {content[:200]}...")
            
            # Extract reasoning content if available
            reasoning_content = None
            if hasattr(response.choices[0].message, 'reasoning_content'):
                reasoning_content = response.choices[0].message.reasoning_content
                logger.debug(f"Reasoning content from reasoner: {reasoning_content}")

            # --- New Tool Calling Logic ---
            tool_calls = None
            tool_instruction = None
            
            # Search for the <tool_request> tag
            match = re.search(r"<tool_request>(.*?)</tool_request>", content, re.DOTALL)
            
            if match:
                tool_instruction = match.group(1).strip()
                logger.info(f"Found tool request instruction: {tool_instruction[:100]}...")
                
                if tools:
                    # Pass the instruction to the robust tool calling helper
                    logger.debug("Invoking tool_helper to generate validated tool call...")
                    validated_tool_call = await self.tool_helper.call_tool(tool_instruction, tools)
                    
                    if validated_tool_call:
                        tool_calls = [validated_tool_call]  # Expecting one call for now
                        logger.info(f"Helper generated tool call: {json.dumps(tool_calls)[:100]}...")
                    else:
                        logger.error("Tool helper failed to generate a valid tool call after retries.")
                        # Decide how to handle this - maybe return an error message in content?
                        # For now, we just won't have a tool_call
                        pass 
                else:
                    logger.warning("Tool request found, but no tools were provided to execute.")
            else:
                logger.debug("No <tool_request> tag found in the response.")
            # --- End New Tool Calling Logic ---

            # Return the response, potentially including the validated tool calls
            return {
                "choices": [{
                    "message": {
                        "content": content, # Keep original content, including the tag for now
                        "tool_calls": tool_calls, 
                        "reasoning_content": reasoning_content
                    }
                }]
            }
                
        except Exception as e:
            error = handle_error(e)
            logger.error(f"Error in model execution: {error}")
            return create_error_response(error)

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
            logger.debug(f"Added user message: {message[:50]}...")
        
    def add_assistant_message(self, message: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Add an assistant message to the conversation history.
        
        Args:
            message: The assistant message content
            tool_calls: Optional list of tool calls made by the assistant
        """
        self.history.add_assistant_message(message, tool_calls)
        if self.debug_enabled:
            logger.debug(f"Added assistant message: {message[:50]}...")
        
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
            logger.debug(f"Added tool result from {tool_name}: {result[:50]}...") 