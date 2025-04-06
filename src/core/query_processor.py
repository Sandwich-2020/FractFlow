"""
Query processor.

Handles the processing of user queries, manages model execution,
and processes model responses with tool calls.
"""

import logging
from typing import Dict, Any, Optional, List
from .orchestrator import Orchestrator
from .tool_executor import ToolExecutor
from ..infra.config import ConfigManager
from ..infra.error_handling import AgentError, handle_error

logger = logging.getLogger(__name__)
config = ConfigManager()

class QueryProcessor:
    """
    Processes user queries and manages the ReAct loop.
    
    Handles the interaction between the user's query, the model, and tools,
    implementing the core ReAct-style loop.
    """
    
    def __init__(self, orchestrator: Orchestrator, tool_executor: ToolExecutor):
        """
        Initialize the query processor.
        
        Args:
            orchestrator: The orchestrator that manages components
            tool_executor: The tool executor that handles tool execution
        """
        self.orchestrator = orchestrator
        self.tool_executor = tool_executor
        self.max_iterations = config.get('agent.max_iterations', 10)
    
    async def process_query(self, user_query: str) -> str:
        """
        Process a user query through the ReAct loop.
        
        Args:
            user_query: The user's input query
            
        Returns:
            The final response to the user
        """
        try:
            model = self.orchestrator.get_model()
            
            # Add user message to history
            logger.info(f"Processing user query: {user_query}")
            model.add_user_message(user_query)
            
            # Get the tools schema
            tools = await self.orchestrator.get_available_tools()
            
            # Initial content placeholder
            content = ""
            
            # Main agent loop (ReAct)
            for iteration in range(self.max_iterations):
                logger.info(f"Starting iteration {iteration+1}/{self.max_iterations}")
                
                # Get response from model
                response = await model.execute(tools)
                
                message = response["choices"][0]["message"]
                logger.info(f"REACT Message: {message}")
                tool_calls = message.get("tool_calls", [])
                content = message.get("content", "Sorry, I couldn't understand your request.")
                
                # If there are no tool calls, return final answer
                if not tool_calls:
                    logger.info("No tool calls detected, returning final answer")
                    return content
                
                # Only process the FIRST tool call in each iteration
                # This ensures we handle one tool at a time for proper context building
                if tool_calls and len(tool_calls) > 0:
                    tool_call = tool_calls[0]
                    
                    # Skip None values
                    if tool_call is None:
                        logger.warning("Received empty tool call")
                        continue
                        
                    # Extract tool information
                    tool_name = tool_call.get("name")
                    function_args = tool_call.get("arguments", {})
                    tool_call_id = tool_call.get("id", "unknown")
                    
                    if not tool_name:
                        logger.warning("Tool call missing 'name' field")
                        continue
                    
                    logger.info(f"Calling tool: {tool_name} with args: {function_args}")
                    
                    # Store the assistant message first
                    model.add_assistant_message(content, [tool_call])
                    
                    # Call the tool
                    try:
                        result = await self.tool_executor.execute_tool(tool_name, function_args)
                        # Add result to conversation history
                        model.add_tool_result(tool_name, result, tool_call_id)
                        
                        # Log remaining tool calls for debugging
                        if len(tool_calls) > 1:
                            logger.info(f"Deferring {len(tool_calls)-1} additional tool calls to next iteration")
                            
                    except Exception as e:
                        error = handle_error(e, {"tool_name": tool_name, "args": function_args})
                        error_message = f"Error calling tool {tool_name}: {str(error)}"
                        logger.error(error_message)
                        model.add_tool_result(tool_name, error_message, tool_call_id)
            
            # If we reached the maximum iterations, return a fallback response
            logger.warning(f"Reached maximum iterations ({self.max_iterations})")
            return "I spent too much time processing your request. Here's what I've gathered so far: " + content
        
        except Exception as e:
            error = handle_error(e, {"user_query": user_query})
            logger.error(f"Error in process_query: {error}")
            return f"Sorry, there was a technical problem processing your request. Error: {str(error)}" 