#!/usr/bin/env python3
"""
Example script demonstrating how to use the FractalFlow Agent interface.

This example shows the basic setup and usage of the FractalFlow Agent
as described in the interface requirements.
"""

import asyncio
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)  # <-- 添加这3行
from dotenv import load_dotenv
from FractFlow.infra.logging_utils import setup_logging

setup_logging(20)
# Import the FractalFlow Agent
from FractFlow.agent import Agent
import mcp
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("fractal weather")

@mcp.tool()
async def weather_agent(user_input: str) -> str:
    """
    This function has an built-in LLM, it can takes user input and returns a weather forecast.
    Args:
        user_input: The user's input
    Returns:
        A weather forecast
    """
    # 1. Load environment variables 
    load_dotenv()
    print('working on weather agent')
    # 3. Create a new agent
    agent = Agent('Inner Weather Agent')  # No need to specify provider here if it's in config
    config = agent.get_config()
    config['agent']['provider'] = 'deepseek'
    config['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    config['deepseek']['model'] = 'deepseek-chat'
    # You can modify configuration values directly
    config['agent']['max_iterations'] = 100  # Properly set as nested value
    # 4. Set configuration loaded from environment
    agent.set_config(config)
    
    
    agent.add_tool("./tools/forecast.py", 'weather tool')
    print("Added weather tool")
    
    # Initialize the agent (starts up the tool servers)
    print("Initializing agent...")
    await agent.initialize()
    
    try:
        result = await agent.process_query(user_input)
    finally:
        # Shut down the agent gracefully
        await agent.shutdown()
        print("\nAgent chat ended.")
    return result

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 