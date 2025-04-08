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
from ..infra.logging_utils import get_logger

logger = get_logger(__name__)
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
            logger.info("Processing user query", {"query": user_query})
            model.add_user_message(user_query)
            
            # Get the tools schema
            tools = await self.orchestrator.get_available_tools()
            
            # Initial content placeholder
            content = ""
            
            # Main agent loop (ReAct)
            for iteration in range(self.max_iterations):
                logger.info("Starting iteration", {"current": iteration+1, "max": self.max_iterations})
                
                # Get response from model
                response = await model.execute(tools)
                
                message = response["choices"][0]["message"]
                logger.info("REACT Message received", {"message_preview": str(message)})
                tool_calls = message.get("tool_calls", [])
                content = message.get("content", "Sorry, I couldn't understand your request.")
                
                # 记录推理内容（如果存在）
                reasoning_content = message.get("reasoning_content")
                if reasoning_content:
                    truncated_reasoning = str(reasoning_content)[:500] + ("..." if len(str(reasoning_content)) > 500 else "")
                    logger.info("Reasoning content", {"reasoning": truncated_reasoning})
                
                # If there are no tool calls, return final answer
                if not tool_calls:
                    # 将最终回答添加到历史记录中
                    model.add_assistant_message(content)
                    # 记录最终结果时的完整对话历史
                    model.history.log_history(logging.INFO, f"Interation History（Number of Iteration:{iteration+1}）")
                    return content
                
                # Only process the FIRST tool call in each iteration
                # This ensures we handle one tool at a time for proper context building
                if tool_calls and len(tool_calls) > 0:
                    tool_call = tool_calls[0]
                    
                    # Skip None values
                    if tool_call is None:
                        logger.warning("Received empty tool call")
                        continue
                        
                    # Extract tool information in OpenAI format
                    if "function" in tool_call and isinstance(tool_call["function"], dict):
                        function_info = tool_call["function"]
                        tool_name = function_info.get("name")
                        
                        # Arguments might be a JSON string, so parse it if needed
                        function_args = function_info.get("arguments", "{}")
                        if isinstance(function_args, str):
                            import json
                            try:
                                function_args = json.loads(function_args)
                            except json.JSONDecodeError:
                                function_args = {}
                        
                        tool_call_id = tool_call.get("id", "unknown")
                    else:
                        # Legacy format fallback
                        tool_name = tool_call.get("name")
                        function_args = tool_call.get("arguments", {})
                        tool_call_id = tool_call.get("id", "unknown")
                    
                    if not tool_name:
                        logger.warning("Tool call missing 'name' field")
                        continue
                    
                    logger.info("Calling tool", {"name": tool_name, "args": function_args})
                    
                    # Store the assistant message first
                    model.add_assistant_message(content, [tool_call])
                    
                    # Call the tool
                    try:
                        result = await self.tool_executor.execute_tool(tool_name, function_args)
                        # 添加截断的工具执行结果日志
                        truncated_result = str(result)[:200] + ("..." if len(str(result)) > 200 else "")
                        logger.info("Tool execution result", {"tool": tool_name, "result": truncated_result})
                        # Add result to conversation history
                        model.add_tool_result(tool_name, result, tool_call_id)
                        
                        # Log remaining tool calls for debugging
                        if len(tool_calls) > 1:
                            logger.info("Deferring additional tool calls", {"count": len(tool_calls)-1})
                            
                    except Exception as e:
                        error = handle_error(e, {"tool_name": tool_name, "args": function_args})
                        error_message = f"Error calling tool {tool_name}: {str(error)}"
                        logger.error(error_message, {"tool": tool_name, "error": str(error)})
                        model.add_tool_result(tool_name, error_message, tool_call_id)
            
            # If we reached the maximum iterations, return a fallback response
            logger.warning("Reached maximum iterations", {"max": self.max_iterations})
            # 记录达到最大迭代次数时的完整对话历史
            final_content = "I spent too much time processing your request. Here's what I've gathered so far: " + content
            model.add_assistant_message(final_content)
            model.history.log_history(logging.WARNING, "达到最大迭代次数")
            return final_content
        
        except Exception as e:
            error = handle_error(e, {"user_query": user_query})
            logger.error("Error in process_query", {"error": str(error)})
            # 如果模型已初始化，记录错误时的对话历史
            if 'model' in locals() and hasattr(model, 'history'):
                model.history.log_history(logging.ERROR, "ERROR in process_query")
            return f"Sorry, there was a technical problem processing your request. Error: {str(error)}" 