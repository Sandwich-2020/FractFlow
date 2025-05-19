"""
AI-Enhanced File I/O Server

This module provides a high-level, natural language interface to file I/O operations
by wrapping the low-level MCP tools with a FractFlow Agent. The agent interprets
user requests and selects the appropriate file operations to execute.
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


# System prompt for the file operations agent
SYSTEM_PROMPT = """
You are a File I/O Assistant specialized in helping with text file operations.

# Core Capabilities
- Reading: get file content (whole file, line ranges, with line numbers, in chunks)
- Writing: create, overwrite, append to, and insert into files
- Information: check file existence, count lines
- Management: delete specific lines (single or multiple)

# Key Workflows

## Working with Large Files
1. FIRST check file size by getting the total line count
2. If file is large (>1000 lines), use chunking strategy:
   - Divide file into manageable chunks (500-1000 lines)
   - Process each chunk separately while maintaining context
   - Consider using overlap between chunks (50-100 lines) for better continuity

## File Editing Workflow
1. ALWAYS verify file exists before attempting to read or modify
2. For modifications, read current content first to understand the file
3. Choose the most appropriate action:
   - create_file: When creating new or completely overwriting
   - append_content: When adding to the end
   - insert_content_at_line: When adding at specific position
   - delete_line_at: When removing content


Always choose the most efficient and appropriate tool for each task.
When working with line numbers, remember they are 1-indexed (first line is 1).

注意：
1. 无论传入的query 有多长，你都必须确保把信息能完整地保存下来，不要省略、遗漏任何信息。
2. 跟你交流的是LLM，不是人类，你做完之后，不需要提任何建议，只需要把是否顺利执行返回就行。
3. 在编辑一个文件之前，请先查看文件相邻5行的内容，以确保编辑的正确性。

"""

async def create_agent():
    """Create and initialize the Agent"""
    load_dotenv()
    # Create a new agent
    agent = Agent('file_io_assistant')  # No need to specify provider here if it's in config
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
    config['agent']['custom_system_prompt'] = SYSTEM_PROMPT
    config['tool_calling']['version'] = 'turbo'
    # 4. Set configuration loaded from environment
    agent.set_config(config)
    
    # Add tools to the agent

    # # Get the current directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "server.py")
    
    agent.add_tool(server_path, "file_operations")
    # Initialize the agent (starts up the tool servers)
    print("Initializing agent...")
    await agent.initialize()
    
    return agent

@mcp.tool()
async def file_operations(query: str) -> str:
    """
    Performs intelligent file operations based on natural language requests.
    
    Parameters:
        query: str - Natural language description of file operation to perform
               Examples: "Read the first 10 lines of log.txt"
                         "Create a new file called notes.txt with content 'Hello'"
                         "Delete lines 5, 10, and 15 from data.csv"
    
    Notes:
        - Automatically selects appropriate file operations based on request
        - Handles large files efficiently through chunking
        - Provides informative error messages and suggestions
        - Supports both absolute and relative file paths
        - All line numbers are 1-indexed (first line is line 1)
    
    Returns:
        str - Operation result or error message with guidance
    
    Examples:
        "Check if config.json exists" → Returns existence status
        "Read lines 5-10 from log.txt" → Returns specified content
        "Count lines in data.csv" → Returns line count
        "Append 'New entry' to log.txt" → Appends text and confirms
        "Process large_log.txt in chunks" → Processes in efficient chunks
    """
    agent = await create_agent()
    result = await agent.process_query(query)
    await agent.shutdown()
    return result

if __name__ == "__main__":
    # 运行MCP服务器
    mcp.run(transport='stdio') 