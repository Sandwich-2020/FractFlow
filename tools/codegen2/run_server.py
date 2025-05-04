"""
Code Generation Tool Server Runner

This module provides the entry point for starting the Code Generation Tool server.
It can be run in two modes:
1. Interactive chat mode - continuous processing of user queries until exit
2. Single query mode - processing a single query and then exiting

The module initializes an EnvisionCore agent with the Code Generation tool and
handles user interactions according to the chosen mode.

Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-08-11
License: MIT License
"""

import asyncio
import os
import sys
import logging
import argparse

import os.path as osp
# Add the project root directory to the Python path
project_root = osp.abspath(osp.join(osp.dirname(__file__), '..'))
sys.path.append(project_root)

# Import the FractalFlow Agent
from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager
from FractFlow.infra.logging_utils import setup_logging, get_logger

# Setup logging
setup_logging(level=logging.INFO)


CODE_WRITING_SYSTEM_PROMPT = """
# Code Writing Instructions

When you need to write, modify, or display code:
* DO NOT output code directly in your response
* ALWAYS use the edit_file tool to create or edit files
* The edit_file tool supports intelligent handling of file edits with the following parameters:
  - content: Code content to write
  - file_path: Path of the file to edit
  - start: Starting line number (1-indexed, inclusive, default: 1)
  - end: Ending line number (1-indexed, inclusive, default: -1 for end of file)


Remember: 

1. NEVER write code directly in your responses. ALWAYS use the edit_file tool.
2. 尽量用部分编辑解决问题.
3. 


"""

async def create_agent():
    """Create and initialize the Agent"""
    # Create a new agent
    agent = Agent('codegen2_agent')  # No need to specify provider here if it's in config
    config = agent.get_config()
    config['agent']['provider'] = 'deepseek'
    config['deepseek']['model'] = 'deepseek-chat'
    # You can modify configuration values directly
    config['agent']['max_iterations'] = 5  # Properly set as nested value
    config['agent']['custom_system_prompt'] = CODE_WRITING_SYSTEM_PROMPT
    # Set configuration loaded from environment
    agent.set_config(config)
    
    # Add tools to the agent
    agent.add_tool("./tools/codegen2/src/server.py", 'code_io')
    # Initialize the agent (starts up the tool servers)
    print("Initializing agent...")
    await agent.initialize()
    
    return agent


async def interactive_mode(agent):
    """Interactive chat mode"""
    print("Agent chat started. Type 'exit', 'quit', or 'bye' to end the conversation.")
    print("Available tools:")
    print("  - codegen2.read_file: Read file content with optional line numbers")
    print("  - codegen2.read_file_range: Read a specific range of lines from a file")
    print("  - codegen2.edit_file: Edit files with support for line ranges, appending, and auto-creation")
    print("  - codegen2.list_directory: List all files and directories in a specified directory")
    print("  - codegen2.remove_file_lines: Remove specified lines from a file")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ('exit', 'quit', 'bye'):
            break
            
        print("\n thinking... \n", end="")
        result = await agent.process_query(user_input)
        print("Agent: {}".format(result))


async def single_query_mode(agent, query):
    """One-time execution mode"""
    print(f"Processing query: {query}")
    print("\n thinking... \n", end="")
    result = await agent.process_query(query)
    print("Result: {}".format(result))
    return result


async def main():
    # Command line argument parsing
    parser = argparse.ArgumentParser(description='Run Code Generation Tool Server')
    parser.add_argument('--user_query', type=str, help='Single query mode: process this query and exit')
    args = parser.parse_args()
    
    # Create Agent
    agent = await create_agent()
    
    try:
        if args.user_query:
            # Single query mode
            await single_query_mode(agent, args.user_query)
        else:
            # Interactive chat mode
            await interactive_mode(agent)
    finally:
        # Close Agent
        await agent.shutdown()
        print("\nAgent session ended.")


if __name__ == "__main__":
    asyncio.run(main()) 