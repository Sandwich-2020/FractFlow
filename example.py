#!/usr/bin/env python3
"""
Example script demonstrating how to use the FractalMCP Agent interface.

This example shows the basic setup and usage of the FractalMCP Agent
as described in the interface requirements.
"""

import asyncio
import os
from dotenv import load_dotenv

# Import the FractalMCP Agent
from FractalMCP.agent import Agent
from FractalMCP.infra.config import ConfigManager

async def main():
    # 1. Load environment variables 
    load_dotenv()
    
    # 2. Get configuration from environment
    config_manager = ConfigManager()
    config_manager.load_from_env()
    env_config = config_manager.get_config()
    
    # 3. Create a new agent
    agent = Agent(provider="deepseek")
    
    # 4. Set configuration loaded from environment
    agent.set_config(env_config)
    
    # 5. Get the current configuration for display/verification
    config = agent.get_config()
    print("Current configuration:")
    print(f"Provider: {config['agent']['provider']}")
    
    # Check API key
    if config['deepseek']['api_key']:
        print("Using DeepSeek API key from environment")
    else:
        # Set API key directly if needed
        # config['deepseek']['api_key'] = 'your_api_key_here'
        # agent.set_config(config)
        print("Warning: No DeepSeek API key found in environment variables")
    
    # Add tools to the agent
    if os.path.exists("./tools/filesystem/operations.py"):
        agent.add_tool("./tools/filesystem/operations.py")
        print("Added filesystem tool")
    
    if os.path.exists("./tools/weather/forecast.py"):
        agent.add_tool("./tools/weather/forecast.py")
        print("Added weather tool")
    
    # Initialize the agent (starts up the tool servers)
    print("Initializing agent...")
    await agent.initialize()
    
    try:
        # Interactive chat loop
        print("Agent chat started. Type 'exit', 'quit', or 'bye' to end the conversation.")
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ('exit', 'quit', 'bye'):
                break
                
            print("\nAgent: ", end="")
            result = await agent.process_query(user_input)
            print(result)
    finally:
        # Shut down the agent gracefully
        await agent.shutdown()
        print("\nAgent chat ended.")

if __name__ == "__main__":
    asyncio.run(main()) 