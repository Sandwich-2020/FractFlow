"""
File I/O Tool Server Runner

This module provides the entry point for starting the File I/O Tool server.
It can be run in two modes:
1. Interactive chat mode - continuous processing of user queries until exit
2. Single query mode - processing a single query and then exiting

The module supports loading either the direct MCP tools or the AI-enhanced version.

Usage:
  python run_server.py                   # Interactive mode with direct MCP tools
  python run_server.py --AI_server       # Interactive mode with AI server
  python run_server.py --user_query "..."  # Single query with direct MCP tools
  python run_server.py --AI_server --user_query "..."  # Single query with AI server
"""

import asyncio
import os
import sys
import logging
import argparse
from FractFlow.infra.logging_utils import setup_logging
# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow Agent
from FractFlow.agent import Agent

SYSTEM_PROMPT = """
你是一个长篇小说作家。

你可以先用比较短的语言规划每一章大纲（不直接写入文件），然后通过调用tool，让子agent 把直接一整章的小说写入文件里面。

每一章小说都不少于5000字。如果你一次性写不进去，可以分多次写。


"""

async def create_agent(use_ai_server=False):
    """Create and initialize the Agent with appropriate tools"""
    # Create a new agent
    agent = Agent('file_io_agent')
    
    # Configure the agent
    config = agent.get_config()
    # You can customize the config here if needed
    config['agent']['max_iterations'] = 20
    config['agent']['custom_system_prompt'] = SYSTEM_PROMPT
    config['tool_calling']['version'] = 'turbo'
    agent.set_config(config)
    
    # Get the tool path based on the use_ai_server flag
    tool_path = os.path.join(current_dir, "AI_server.py" if use_ai_server else "server.py")
    
    # Add the appropriate tool to the agent
    print(f"Loading tool from: {tool_path}")
    agent.add_tool(tool_path, 'file_io')
    
    # Initialize the agent (starts up the tool servers)
    print("Initializing agent...")
    await agent.initialize()
    
    return agent


async def interactive_mode(agent):
    """Interactive chat mode with multi-turn conversation support"""
    print("\nFile I/O Tool Interactive Mode")
    print("Type 'exit', 'quit', or 'bye' to end the conversation.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ('exit', 'quit', 'bye'):
            break
        
        print("\nProcessing...\n")
        result = await agent.process_query(user_input)
        print(f"Agent: {result}")


async def single_query_mode(agent, query):
    """One-time execution mode for a single query"""
    print(f"Processing query: {query}")
    print("\nProcessing...\n")
    result = await agent.process_query(query)
    print(f"Result: {result}")
    return result


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run File I/O Tool Server')
    parser.add_argument('--user_query', type=str, help='Single query mode: process this query and exit')
    parser.add_argument('--AI_server', action='store_true', help='Use AI-enhanced server instead of direct MCP tools')
    args = parser.parse_args()
    
    # Determine which server to use and display info
    server_type = "AI-enhanced" if args.AI_server else "direct MCP"
    mode_type = "single query" if args.user_query else "interactive"
    print(f"Starting File I/O Tool in {mode_type} mode using {server_type} tools.")
    
    # Create and initialize the agent
    agent = await create_agent(use_ai_server=args.AI_server)
    
    try:
        if args.user_query:
            # Single query mode
            await single_query_mode(agent, args.user_query)
        else:
            # Interactive chat mode
            await interactive_mode(agent)
    finally:
        # Clean up and shut down
        await agent.shutdown()
        print("\nAgent session ended.")


if __name__ == "__main__":
    # Set basic logging
    setup_logging(level=logging.DEBUG)
    # Run the async main function
    asyncio.run(main()) 