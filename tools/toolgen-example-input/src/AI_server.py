"""
AI-Enhanced File Line Manager Server

This module provides a high-level, natural language interface to file_line_manager operations
by wrapping the low-level MCP tools with a FractFlow Agent. The agent interprets
user requests and selects the appropriate operations to execute.
"""

import asyncio
import os
import sys
import logging
import argparse
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import os.path as osp

# Import the FractFlow Agent
from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager
from FractFlow.infra.logging_utils import setup_logging, get_logger

# Setup logging
setup_logging(level=logging.INFO)

# Initialize FastMCP server
mcp = FastMCP("file_line_manager_tool")

# System prompt for the agent
SYSTEM_PROMPT = """
You are a File Line Management Assistant specialized in handling text file operations with precision and efficiency. Your primary role is to help users read, modify, and analyze text files through structured line-based operations.

Available tools and their purposes:
- check_file_exists: Verify if a file exists at given path
- get_file_line_count: Count total lines in a file
- read_file_range: Read specific line range (supports 1-based indexing)
- read_file_chunks: Read file in configurable chunks with overlap
- read_file_with_line_numbers: Read content with line numbers
- create_or_write_file: Create/overwrite file with content
- append_to_file: Add content to file end
- insert_at_line: Insert content at specific position
- delete_line: Remove a specific line

Tool selection guidelines:
1. For basic file checks: Use check_file_exists first
2. For reading operations:
   - Single range: read_file_range
   - Chunked reading: read_file_chunks
   - Numbered output: read_file_with_line_numbers
3. For writing operations:
   - New files: create_or_write_file
   - Appending: append_to_file
   - Precise insertion: insert_at_line
   - Line removal: delete_line

Common workflows:
1. File inspection:
   check_file_exists → get_file_line_count → read_file_range
2. Content review:
   read_file_chunks → analyze specific chunks
3. File modification:
   check_file_exists → read_file_range → insert_at_line/delete_line
4. Log file handling:
   append_to_file → read_file_with_line_numbers

Error handling protocol:
1. Always check 'success' field in tool responses
2. For permission errors: Suggest checking file permissions
3. For missing files: Verify path or suggest creation
4. For invalid line numbers: Validate against line count first
5. Present error messages verbatim to users

Best practices:
1. Normalize paths before operations
2. Validate line numbers against actual line counts
3. For large files, prefer chunked reading
4. Maintain 1-based line numbering consistency
5. Preserve original line endings when modifying

Response formatting:
1. Always include file path in responses
2. For read operations: Show line range and count
3. For write operations: Confirm changes made
4. Present errors clearly with suggested actions
"""

async def create_agent():
    """Create and initialize the Agent"""
    load_dotenv()
    # Create a new agent
    agent = Agent('file_line_manager_assistant')
    
    # Configure the agent
    config = agent.get_config()
    config['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    config['agent']['provider'] = 'deepseek'
    config['deepseek']['model'] = 'deepseek-chat'
    config['agent']['max_iterations'] = 5
    config['agent']['custom_system_prompt'] = SYSTEM_PROMPT
    config['tool_calling']['version'] = 'turbo'
    
    # Apply configuration
    agent.set_config(config)
    
    # Add tools to the agent
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "server.py")
    
    agent.add_tool(server_path, "file_line_manager_operations")
    
    # Initialize the agent
    print("Initializing agent...")
    await agent.initialize()
    
    return agent

@mcp.tool()
async def file_line_manager_tool(query: str) -> str:
    """
    Manages file content operations through natural language commands for line-based text manipulation.

This tool enables precise control over text files by performing line-oriented operations such as
insertion, deletion, modification, and extraction based on natural language instructions.

Input format:
- Commands specifying file operations (create/read/update/delete)
- Line number references (absolute, relative, or range-based)
- Content manipulation instructions (insert/replace/append)
- May include file paths and pattern matching criteria

Returns:
- 'content': Modified or extracted file content (string or list of lines)
- 'status': Operation result ('success'/'partial_success'/'error')
- 'changes': Summary of modifications made (for write operations)
- 'line_count': Total lines in file (for read operations)
- 'error': Detailed error message if operation failed

Examples:
- "Insert 'import os' at line 3 in config.py"
- "Delete lines 10-15 from report.txt and show remaining content"
- "Replace all occurrences of 'old_version' with 'new_version' in changelog.md"
- "Create new file setup.cfg with these 5 lines of content"
- "Show lines containing 'TODO' in main.js between lines 50-100"
    """
    # Create and initialize the agent
    agent = await create_agent()
    
    try:
        # Process the query with the agent
        result = await agent.process_query(query)
        return result
    finally:
        # Ensure the agent is properly shut down
        await agent.shutdown()

if __name__ == "__main__":
    # Run the MCP server
    mcp.run(transport='stdio') 