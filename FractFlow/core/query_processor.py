"""
query_processor.py
Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-04-08
Description: Processes user queries, manages model execution, and handles the loop with tool calls.
License: MIT License
"""

"""
Query processor.

Handles the processing of user queries, manages model execution,
and processes model responses with tool calls.
"""

import json
from typing import Dict, Any, Optional, List
from .orchestrator import Orchestrator
from .tool_executor import ToolExecutor
from ..infra.config import ConfigManager
from ..infra.error_handling import AgentError, handle_error
from ..infra.logging_utils import get_logger

class QueryProcessor:
    """
    Processes user queries and manages the loop.
    
    Handles the interaction between the user's query, the model, and tools,
    implementing the core loop.
    """
    
    def __init__(self, orchestrator: Orchestrator, tool_executor: ToolExecutor, config: Optional[ConfigManager] = None):
        """
        Initialize the query processor.
        
        Args:
            orchestrator: The orchestrator that manages components
            tool_executor: The tool executor that handles tool execution
            config: Configuration manager instance to use
        """
        self.orchestrator = orchestrator
        self.tool_executor = tool_executor
        if config is None:
            self.config = ConfigManager()
        else:
            self.config = config
        
        # Push component name to call path
        self.config.push_to_call_path("query_processor")
        
        # Initialize logger
        self.logger = get_logger(self.config.get_call_path())
        
        self.max_iterations = self.config.get('agent.max_iterations', 10)
        self.logger.debug("Query processor initialized", {"max_iterations": self.max_iterations})
    
    async def process_query(self, user_query: str) -> str:
        """
        Process a user query through the loop.
        
        Args:
            user_query: The user's input query
            
        Returns:
            The final response to the user
        """
        try:
            model = self.orchestrator.get_model()
            
            # Add user message to history
            self.logger.debug("Processing user query", {"query": user_query})
            model.add_user_message(user_query)
            
            # Get the tools schema
            tools = await self.orchestrator.get_available_tools()
            
            # Initial content placeholder
            content = ""
            
            # Main agent loop
            for iteration in range(self.max_iterations):
                # self.logger.debug("Starting iteration", {"current": iteration+1, "max": self.max_iterations})
                
                # Get response from model
                response = await model.execute(tools)
                
                message = response["choices"][0]["message"]
                tool_calls = message.get("tool_calls", [])
                content = message.get("content", "Sorry, I couldn't understand your request.")
                
                # Log reasoning content (if exists)
                reasoning_content = message.get("reasoning_content")
                if reasoning_content:
                    self.logger.info("Reasoning content", {"reasoning": reasoning_content})
                
                # If there are no tool calls, return final answer
                if not tool_calls:
                    # Add final answer to conversation history
                    model.add_assistant_message(content)
                    self.logger.info(content, {"iterations": iteration+1})
                    # Log complete conversation history for final result
                    # self.logger.info(f"Final response ready", {"iterations": iteration+1})
                    return content
                
                # Process all tool calls in each iteration
                if tool_calls and len(tool_calls) > 0:
                    # Store the assistant message first with all tool calls
                    model.add_assistant_message(content, tool_calls)
                    self.logger.debug(f"Processing tool calls", {"count": len(tool_calls)})
                    
                    # Process each tool call
                    for tool_call in tool_calls:
                        # Skip None values
                        if tool_call is None:
                            self.logger.warning("Received empty tool call")
                            continue
                            
                        # Extract tool information in OpenAI format
                        function_info = tool_call["function"]
                        tool_name = function_info.get("name")
                        
                        # Arguments might be a JSON string, so parse it if needed
                        function_args = function_info.get("arguments", "{}")
                        if isinstance(function_args, str):
                            try:
                                function_args = json.loads(function_args)
                            except json.JSONDecodeError:
                                function_args = {}
                        
                        tool_call_id = tool_call.get("id", "unknown")
                        
                        if not tool_name:
                            self.logger.warning("Tool call missing 'name' field")
                            continue
                        
                        self.logger.info("Calling tool", {"name": tool_name, "args": function_args})
                        
                        # Call the tool
                        try:
                            result = await self.tool_executor.execute_tool(tool_name, function_args)
                            # Add tool execution result log
                            self.logger.info("Tool execution result", {"tool": tool_name, "result": result})
                            # Add result to conversation history
                            model.add_tool_result(tool_name, result, tool_call_id)
                                
                        except Exception as e:
                            error = handle_error(e, {"tool_name": tool_name, "args": function_args})
                            error_message = f"Error calling tool {tool_name}: {str(error)}"
                            self.logger.error(error_message, {"tool": tool_name, "error": str(error)})
                            model.add_tool_result(tool_name, error_message, tool_call_id)
            
            # If we reached the maximum iterations, return a fallback response
            self.logger.warning("Reached maximum iterations", {"max": self.max_iterations})
            # Log complete conversation history when max iterations reached
            final_content = "I spent too much time processing your request. Here's what I've gathered so far: " + content
            model.add_assistant_message(final_content)
            return final_content
        
        except Exception as e:
            error = handle_error(e, {"user_query": user_query})
            self.logger.error("Error in process_query", {"error": str(error)})
            # If model is initialized, log conversation history when error occurs
            if 'model' in locals() and hasattr(model, 'history'):
                self.logger.error("Error occurred while processing query", {"history_length": len(model.history.get_messages())})
            return f"Sorry, there was a technical problem processing your request. Error: {str(error)}"

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the conversation history from the current model.
        
        Returns:
            The current conversation history
        """
        return self.orchestrator.get_history() 