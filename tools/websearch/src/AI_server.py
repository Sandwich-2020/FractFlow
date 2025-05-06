"""
Web Search Tool Server Runner

This module provides the entry point for starting the Web Search Tool server.
It can be run in two modes:
1. Interactive chat mode - continuous processing of user queries until exit
2. Single query mode - processing a single query and then exiting

The module initializes a FractFlow agent with the Web Search tool and
handles user interactions according to the chosen mode.

Author: Yingcong Chen (xxu068@connect.hkust-gz.edu.cn) - Envision Lab
Date: 2025-04-28
License: MIT License
"""

import asyncio
import os
import sys
import logging
import argparse
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import os.path as osp
# Add the project root directory to the Python path
project_root = osp.abspath(osp.join(osp.dirname(__file__), '../..'))
sys.path.append(project_root)

# Import the FractFlow Agent
from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager
from FractFlow.infra.logging_utils import setup_logging, get_logger

# Setup logging
setup_logging(level=logging.INFO)

mcp = FastMCP("web_search_browse_tool")

async def create_agent():
    """Create and initialize the Agent"""
    load_dotenv()
    # Create a new agent
    agent = Agent('websearch_agent')  # No need to specify provider here if it's in config
    config = agent.get_config()
    config['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    config['agent']['provider'] = 'deepseek'
    config['agent']['custom_system_prompt'] = '当调用网页浏览工具无法得出具体或者确切的答案时，请调用网页浏览工具来浏览相关性最强的网页回答。请你一次性回答，避免让用户确认'

    # config['agent']['custom_system_prompt'] = """
    # You are an intelligent assistant. You carefully analyze user requests and determine if external tools are needed.
    # When a user asks you some knowledge and needs to use the search_from_web tool, please decide based on the amount of information you searched. 
    # If it is not enough, do not answer directly, use web_browse tool. Next, call the web browsing tool to view the web page to get more information.
    # If the amount of information is enough, you can answer directly.

    # """
    config['deepseek']['model'] = 'deepseek-chat'
    # You can modify configuration values directly
    config['agent']['max_iterations'] = 5  # Properly set as nested value
    # 4. Set configuration loaded from environment
    agent.set_config(config)
    
    # Add tools to the agent

    # Get the current directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "server.py")
    
    agent.add_tool(server_path, "web_search")
    # Initialize the agent (starts up the tool servers)
    print("Initializing agent...")
    await agent.initialize()
    
    return agent



@mcp.tool()
async def single_query_mode(agent, query):
    """One-time execution mode"""
    agent = await create_agent()
    result = await agent.process_query(query)
    await agent.shutdown()
    return result


if __name__ == "__main__":
    mcp.run(transport='stdio') 