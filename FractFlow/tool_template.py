"""
tool_template.py
Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-05-31
Description: Base template class for creating FractFlow tools that can run in multiple modes.
License: MIT License
"""

"""
ToolTemplate - Base class for creating FractFlow tools with dual functionality.

This template provides a unified interface for creating tools that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced operations as MCP tools
2. Interactive mode: Runs as an interactive agent 
3. Single query mode: Processes a single query and exits

Usage:
    class MyTool(ToolTemplate):
        SYSTEM_PROMPT = "You are a helpful assistant..."
        TOOLS = [("path/to/tool.py", "tool_name")]
        
        # Optional: Override configuration
        @classmethod
        def create_config(cls):
            return ConfigManager(
                provider='deepseek',
                deepseek_model='deepseek-chat',
                max_iterations=10,
                custom_system_prompt=cls.SYSTEM_PROMPT
            )
        
    if __name__ == "__main__":
        MyTool.main()
"""

import asyncio
import os
import sys
import logging
import argparse
from typing import List, Tuple, Dict, Any, Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import os.path as osp

# Import the FractFlow Agent and Config
from .agent import Agent
from .infra.config import ConfigManager
from .infra.logging_utils import setup_logging, get_logger

class ToolTemplate:
    """
    Base template class for creating FractFlow tools with multiple running modes.
    
    Subclasses must define:
        SYSTEM_PROMPT (str): The system prompt for the agent
        TOOLS (List[Tuple[str, str]]): List of (tool_path, tool_name) tuples
    
    Subclasses can optionally define:
        MCP_SERVER_NAME (str): Custom MCP server name (defaults to class name)
        TOOL_DESCRIPTION (str): Description for the main MCP tool function
        
    Subclasses can optionally override:
        create_config() -> ConfigManager: Custom configuration creation
    """
    
    # Subclasses must define these
    SYSTEM_PROMPT: str = None
    TOOLS: List[Tuple[str, str]] = []
    
    # Subclasses can optionally define these
    MCP_SERVER_NAME: Optional[str] = None
    TOOL_DESCRIPTION: Optional[str] = None
    
    # Class-level MCP server instance
    _mcp = None
    
    @classmethod
    def create_config(cls) -> ConfigManager:
        """
        Create configuration for the agent.
        
        Subclasses can override this method to customize configuration.
        
        Returns:
            ConfigManager: Configured instance ready for Agent creation
        """
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )
    
    @classmethod
    async def create_agent(cls, name_suffix='assistant') -> Agent:
        """
        Create and initialize an Agent with tools.
        
        Args:
            name_suffix: Suffix for agent name (e.g., 'assistant', 'agent')
            
        Returns:
            Agent: Initialized agent ready for use
        """
        config = cls.create_config()
        agent = Agent(config=config, name=f'{cls.__name__.lower()}_{name_suffix}')
        
        # Add tools to the agent
        await cls._add_tools_to_agent(agent)
        
        # Initialize the agent
        print("Initializing agent...")
        await agent.initialize()
        
        return agent
    
    @classmethod
    async def _add_tools_to_agent(cls, agent: Agent):
        """
        Add tools to the agent based on TOOLS configuration.
        
        Args:
            agent: Agent instance to add tools to
        """
        current_dir = os.path.dirname(os.path.abspath(sys.modules[cls.__module__].__file__))
        
        for tool_path, tool_name in cls.TOOLS:
            # Handle relative paths
            if not os.path.isabs(tool_path):
                full_path = os.path.join(current_dir, tool_path)
            else:
                full_path = tool_path
                
            if not os.path.exists(full_path):
                raise ValueError(f"Tool path does not exist: {full_path}")
                
            agent.add_tool(full_path, tool_name)
    
    @classmethod
    def _get_mcp_server_name(cls):
        """Get the MCP server name, using class name as default"""
        return cls.MCP_SERVER_NAME or f"{cls.__name__.lower()}_tool"
    
    @classmethod
    def _get_tool_description(cls):
        """Get the tool description for MCP function"""
        if cls.TOOL_DESCRIPTION:
            return cls.TOOL_DESCRIPTION
        
        return f"""
        Performs intelligent operations based on natural language requests using {cls.__name__}.
        
        Parameters:
            query: str - Natural language description of operation to perform
        
        Returns:
            str - Operation result or error message with guidance
        """
    
    @classmethod
    def _validate_configuration(cls):
        """Validate that required class attributes are defined"""
        if cls.SYSTEM_PROMPT is None:
            raise ValueError(f"{cls.__name__} must define SYSTEM_PROMPT")
        
        if not cls.TOOLS:
            raise ValueError(f"{cls.__name__} must define TOOLS list")
        
        # Validate tool paths exist
        current_dir = os.path.dirname(os.path.abspath(sys.modules[cls.__module__].__file__))
        for tool_path, tool_name in cls.TOOLS:
            # Handle relative paths
            if not os.path.isabs(tool_path):
                full_path = os.path.join(current_dir, tool_path)
            else:
                full_path = tool_path
                
            if not os.path.exists(full_path):
                raise ValueError(f"Tool path does not exist: {full_path}")
    
    @classmethod
    async def _mcp_tool_function(cls, query: str) -> str:
        """The main MCP tool function that processes queries"""
        agent = await cls.create_agent()
        try:
            result = await agent.process_query(query)
            return result
        finally:
            await agent.shutdown()
    
    @classmethod
    async def _run_interactive(cls):
        """Interactive chat mode with multi-turn conversation support"""
        print(f"\n{cls.__name__} Interactive Mode")
        print("Type 'exit', 'quit', or 'bye' to end the conversation.\n")
        
        agent = await cls.create_agent('agent')
        
        try:
            while True:
                user_input = input("You: ")
                if user_input.lower() in ('exit', 'quit', 'bye'):
                    break
                
                print("\nProcessing...\n")
                result = await agent.process_query(user_input)
                print(f"Agent: {result}")
        finally:
            await agent.shutdown()
            print("\nAgent session ended.")
    
    @classmethod
    async def _run_single_query(cls, query: str):
        """One-time execution mode for a single query"""
        print(f"Processing query: {query}")
        print("\nProcessing...\n")
        
        agent = await cls.create_agent('agent')
        
        try:
            result = await agent.process_query(query)
            print(f"Result: {result}")
            return result
        finally:
            await agent.shutdown()
            print("\nAgent session ended.")
    
    @classmethod
    def _run_mcp_server(cls):
        """Run in MCP Server mode"""
        # Initialize MCP server if not already done
        if cls._mcp is None:
            cls._mcp = FastMCP(cls._get_mcp_server_name())
            
            # Register the main tool function
            cls._mcp.tool()(cls._mcp_tool_function)
        
        # Run the MCP server
        cls._mcp.run(transport='stdio')
    
    @classmethod
    def main(cls):
        """Main entry point for the tool"""
        # Validate configuration
        cls._validate_configuration()
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(description=f'{cls.__name__} - Unified Interface')
        parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
        parser.add_argument('--query', type=str, help='Single query mode: process this query and exit')
        args = parser.parse_args()
        
        # Setup logging
        setup_logging(level=logging.INFO)
        
        if args.interactive:
            # Interactive mode
            print(f"Starting {cls.__name__} in interactive mode.")
            asyncio.run(cls._run_interactive())
        elif args.query:
            # Single query mode
            print(f"Starting {cls.__name__} in single query mode.")
            asyncio.run(cls._run_single_query(args.query))
        else:
            # Default: MCP Server mode
            print(f"Starting {cls.__name__} in MCP Server mode.")
            cls._run_mcp_server() 