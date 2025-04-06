#!/usr/bin/env python3
"""
Main entry point for the agent system.

Provides the main entry point for running the agent system, handling setup,
initialization, and command line arguments.
"""

import asyncio
import os
import argparse
import logging
import sys
from typing import Dict, Optional

# Add parent directory to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.core.orchestrator import Orchestrator
from src.core.query_processor import QueryProcessor
from src.core.tool_executor import ToolExecutor
from src.infra.config import ConfigManager

logger = logging.getLogger(__name__)
config = ConfigManager()

async def run_agent_chat(tool_configs: Optional[Dict[str, str]] = None, 
                         system_prompt: Optional[str] = None,
                         provider: Optional[str] = None):
    """
    Run an interactive agent chat session.
    
    Args:
        tool_configs: Dictionary of tool configurations
        system_prompt: System prompt to initialize the agent with
        provider: The AI provider to use (e.g., 'openai', 'deepseek')
    """
    # Create and configure the agent system
    orchestrator = Orchestrator(
        system_prompt=system_prompt,
        tool_configs=tool_configs,
        provider=provider
    )
    
    tool_executor = ToolExecutor()
    query_processor = QueryProcessor(orchestrator, tool_executor)
    
    # Launch tools
    await orchestrator.start()
    
    try:
        # Interactive loop
        print("Agent chat started. Type 'exit' to end the conversation.")
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ('exit', 'quit', 'bye'):
                break
                
            print("\nAgent: ", end="")
            result = await query_processor.process_query(user_input)
            print(result)
    finally:
        # Shut down gracefully
        await orchestrator.shutdown()
        print("\nAgent chat ended.")

async def main():
    """Main entry point for running the agent chat system."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the MCP agent with selected AI provider")
    parser.add_argument("--provider", type=str, choices=["openai", "deepseek"], default="deepseek",
                        help="The AI provider to use")
    parser.add_argument("--system-prompt", type=str, default=None,
                        help="Custom system prompt to initialize the agent")
    args = parser.parse_args()
    
    # Define tool configurations explicitly
    tool_configs = {}
    
    # Check if tools exist and add them
    if os.path.exists("./src/tools/filesystem/operations.py"):
        tool_configs["filesystem"] = "./src/tools/filesystem/operations.py"
    
    if os.path.exists("./src/tools/weather/forecast.py"):
        tool_configs["weather"] = "./src/tools/weather/forecast.py"
    
    if os.path.exists("./src/tools/document/pandoc.py"):
        tool_configs["pandoc"] = "./src/tools/document/pandoc.py"
    
    # Run the agent with explicit tool configurations and selected provider
    await run_agent_chat(
        tool_configs=tool_configs,
        system_prompt=args.system_prompt,
        provider=args.provider
    )

if __name__ == "__main__":
    asyncio.run(main()) 