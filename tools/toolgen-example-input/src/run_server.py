#!/usr/bin/env python3
"""
File Line Manager Tool Server Runner

This module provides the entry point for starting the File Line Manager Tool server.
It can be run in two modes:
1. Interactive chat mode - continuous processing of user queries until exit
2. Single query mode - processing a single query and then exiting

The module supports loading either the direct MCP tools or the AI-enhanced version.

Usage:
  python run_server.py                   # Interactive mode with direct MCP tools
  python run_server.py --ai              # Interactive mode with AI server
  python run_server.py -q "..."          # Single query with direct MCP tools
  python run_server.py --ai -q "..."     # Single query with AI server
"""

import asyncio
import os
import sys
import logging
import argparse
from FractFlow.infra.logging_utils import setup_logging

# Import the FractFlow Agent
from FractFlow.agent import Agent

# System prompt for the AI-enhanced version
SYSTEM_PROMPT = """
File Line Manager provides tools for reading, writing, and modifying text files with line-level precision. Key capabilities include:

- Check file existence and line counts
- Read specific line ranges or chunks
- Insert/append/delete lines
- Create or overwrite files

Basic usage:
- Specify file paths clearly
- Line numbers are 1-indexed
- Check file existence before operations
- Handle large files in chunks when needed

Limitations:
- Works only with text files
- No concurrent access handling
- Large files may impact performance
"""

async def create_agent(use_ai_server=False):
    """Create and initialize the Agent with appropriate tools"""
    # Create a new agent
    agent = Agent('file_line_manager_agent')
    
    # Configure the agent
    config = agent.get_config()
    # You can customize the config here if needed
    config['agent']['max_iterations'] = 5
    config['agent']['custom_system_prompt'] = SYSTEM_PROMPT
    config['tool_calling']['version'] = 'turbo'
    agent.set_config(config)
    
    # Get the tool path based on the use_ai_server flag
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tool_path = os.path.join(current_dir, "AI_server.py" if use_ai_server else "server.py")
    
    # Add the appropriate tool to the agent
    print(f"Loading tool from: {tool_path}")
    agent.add_tool(tool_path, 'file_line_manager')
    
    # Initialize the agent (starts up the tool servers)
    print("Initializing agent...")
    await agent.initialize()
    
    return agent

async def interactive_mode(agent):
    """Interactive chat mode with multi-turn conversation support"""
    print("\nFile Line Manager Tool Interactive Mode")
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
    parser = argparse.ArgumentParser(description='Run File Line Manager Tool Server')
    parser.add_argument('-q', '--query', type=str, help='Single query mode: process this query and exit')
    parser.add_argument('--ai', action='store_true', help='Use AI-enhanced server instead of direct MCP tools')
    args = parser.parse_args()
    
    # Determine which server to use and display info
    server_type = "AI-enhanced" if args.ai else "direct MCP"
    mode_type = "single query" if args.query else "interactive"
    print(f"Starting File Line Manager Tool in {mode_type} mode using {server_type} tools.")
    
    # Create and initialize the agent
    agent = await create_agent(use_ai_server=args.ai)
    
    try:
        if args.query:
            # Single query mode
            await single_query_mode(agent, args.query)
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