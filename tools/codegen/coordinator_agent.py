"""
Coordinator Agent implementation for ChatToolGen.

Provides a flexible framework for tool generation by dynamically incorporating
specialized agents defined as tools, with workflow defined by system prompts.
"""

import asyncio
import os
import sys
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
import mcp
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

# 导入FractFlow Agent类，用于调用其他Agent
from FractFlow.agent import Agent


import logging
from FractFlow.infra.logging_utils import setup_logging, get_logger

# 设置日志
setup_logging(20)


# Initialize FastMCP server
mcp = FastMCP("Code Generator")


@mcp.tool()
async def code_gen_coordinator(user_input: str, save_dir: str) -> str:
    """
    Given a request about coding, coordinate multipole LLM to generate the code.

    Args:
        user_input: Natural language description of the desired code
        save_dir: Directory to save the generated code
    Returns:
        A message describing the generated code, with file path
    """
    # Load environment variables
    load_dotenv()
    
    # Create an agent instance
    agent = Agent('coordinator_agent')
    config = agent.get_config()
    config['agent']['provider'] = 'deepseek'
    config['deepseek']['model'] = 'deepseek-chat'
    config['agent']['max_iterations'] = 10 
    agent.set_config(config)
    agent.add_tool(os.path.join(current_dir, "implementation_agent.py"))
    os.makedirs(save_dir, exist_ok=True)
    
    # Initialize the agent
    await agent.initialize()
    
    try:
        # Process the user request, letting the agent decide which tools to use
        # based on the workflow defined in the system prompt
        prompt = f"""
User wants to generate a tool with this description: 

"{user_input}"

General workflow:
1. 深入思考并理解用户的需求
2. 详细规划总共要写哪些文件，每个文件要实现什么功能。
3. 使用implementation_agent生成代码，路径为{save_dir}。

NOTE： before taking any action, you should think step by step.
"""
        result = await agent.process_query(prompt)
        return result
    finally:
        # Shut down the agent
        await agent.shutdown()

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 