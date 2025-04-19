#!/usr/bin/env python
"""
Simple test script for DeepSeek tool calling functionality.
This is a standalone script, not a pytest test.
"""

import asyncio
import json
import logging
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from FractFlow.models.deepseek_model import DeepSeekModel
from FractFlow.infra.config import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('deepseek_test')

# Sample tools for testing
SAMPLE_TOOLS = [
    {
        "function": {
            "name": "get_weather",
            "description": "Get current weather information for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The unit of temperature"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "function": {
            "name": "search_products",
            "description": "Search for products in the catalog",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "category": {
                        "type": "string",
                        "description": "Product category to search in"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# Sample tool result for simulation
def mock_tool_result(tool_name, arguments):
    """Simulate a tool execution result"""
    if tool_name == "get_weather":
        args = json.loads(arguments)
        location = args.get("location", "Unknown")
        unit = args.get("unit", "celsius")
        temp = "22°C" if unit == "celsius" else "72°F"
        return f"Weather in {location}: Sunny, {temp}"
    
    elif tool_name == "search_products":
        args = json.loads(arguments)
        query = args.get("query", "")
        category = args.get("category", "all")
        return f"Found 3 products matching '{query}' in category '{category}': Product A, Product B, Product C"
    
    return "Unknown tool or error in execution"

async def run_test():
    """Run a test of the DeepSeek tool calling functionality"""
    try:
        logger.info("Initializing DeepSeek model...")
        model = DeepSeekModel()
        
        # Add some messages to create context
        user_message = "I'd like to know the weather in Tokyo"
        logger.info(f"Adding user message: {user_message}")
        model.add_user_message(user_message)
        
        # Execute the model with our sample tools
        logger.info("Executing model with tools...")
        response = await model.execute(SAMPLE_TOOLS)
        
        if not response or "choices" not in response or not response["choices"]:
            logger.error("No response from model")
            return
        
        # Extract content and tool_calls if present
        message = response["choices"][0]["message"]
        content = message.get("content", "")
        tool_calls = message.get("tool_calls")
        reasoning = message.get("reasoning_content")
        
        logger.info(f"Model response content: {content[:200]}...")
        if reasoning:
            logger.info(f"Reasoning content: {reasoning[:200]}...")
        
        if not tool_calls:
            logger.info("No tool calls in the response")
            return
        
        # Process each tool call
        logger.info(f"Found {len(tool_calls)} tool calls")
        for i, tool_call in enumerate(tool_calls):
            tool_id = tool_call.get("id", "unknown_id")
            function = tool_call.get("function", {})
            tool_name = function.get("name", "unknown_tool")
            arguments = function.get("arguments", "{}")
            
            logger.info(f"Tool call {i+1}: {tool_name}")
            logger.info(f"Arguments: {arguments}")
            
            # Simulate tool execution
            result = mock_tool_result(tool_name, arguments)
            logger.info(f"Tool result: {result}")
            
            # Add the tool result to the conversation history
            model.add_tool_result(tool_name, result, tool_id)
        
        # Try a follow-up to see how the model uses the tool results
        logger.info("Testing follow-up...")
        model.add_user_message("What about the weather in New York?")
        
        # Execute again
        response2 = await model.execute(SAMPLE_TOOLS)
        if not response2 or "choices" not in response2:
            logger.error("No response from model on follow-up")
            return
            
        # Extract content and tool_calls for the second response
        message2 = response2["choices"][0]["message"]
        content2 = message2.get("content", "")
        tool_calls2 = message2.get("tool_calls")
        
        logger.info(f"Follow-up response content: {content2[:200]}...")
        
        if tool_calls2:
            logger.info(f"Found {len(tool_calls2)} tool calls in follow-up")
            # Process follow-up tool calls same as before
            for i, tool_call in enumerate(tool_calls2):
                function = tool_call.get("function", {})
                tool_name = function.get("name", "unknown_tool")
                arguments = function.get("arguments", "{}")
                
                logger.info(f"Follow-up tool call {i+1}: {tool_name}")
                logger.info(f"Arguments: {arguments}")
        else:
            logger.info("No tool calls in follow-up response")
        
        logger.info("Test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # Check if config is properly set
    config = ConfigManager()
    api_key = config.get('deepseek.api_key')
    if not api_key:
        logger.error("No DeepSeek API key found in config. Please set it before running the test.")
        sys.exit(1)
    
    # Run the async test
    asyncio.run(run_test()) 