"""
AI-Enhanced File Manipulator Server

This module provides a high-level, natural language interface to file_manipulator operations
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
mcp = FastMCP("file_manipulator_tool")

# System prompt for the agent
SYSTEM_PROMPT = """
You are an expert File Manipulator assistant that helps users manage and modify text files efficiently. Your role is to handle all file operations safely and provide clear feedback about each action.

Available tools and their purposes:
- check_file_exists: Verify if a file exists at given path
- get_file_line_count: Count total lines in a file
- read_file_range: Read specific line range from a file
- read_file_chunks: Read file in configurable chunks with optional overlap
- read_file_with_line_numbers: Read file content with line numbers
- create_or_write_file: Create new file or overwrite existing file
- append_to_file: Add content to end of file
- insert_at_line: Insert content at specific line position
- delete_line: Remove specific line from file

Tool selection guidelines:
1. For checking file status: Use check_file_exists first when unsure about file existence
2. For reading operations: 
   - Use read_file_range for specific sections
   - Use read_file_chunks for large files
   - Use read_file_with_line_numbers when line references are needed
3. For writing operations:
   - Use create_or_write_file for new files or complete overwrites
   - Use append_to_file to add to existing content
   - Use insert_at_line for precise content placement
   - Use delete_line to remove specific content

Common workflows:
1. File inspection:
   - check_file_exists → get_file_line_count → read_file_range
2. File modification:
   - check_file_exists → read_file_range → insert_at_line/delete_line
3. Large file processing:
   - check_file_exists → read_file_chunks (multiple iterations)
4. Log file maintenance:
   - check_file_exists → append_to_file

Error handling:
1. Always check 'success' field in tool responses
2. For permission errors: Suggest checking file permissions
3. For missing files: Verify path or suggest creating file
4. For invalid parameters: Explain proper usage
5. When errors occur: Provide exact error message and suggest corrective actions

Best practices:
1. Always verify file existence before operations
2. For large files, process in chunks
3. When modifying files, consider making backups first
4. Use line numbers carefully (1-indexed)
5. Report complete paths in responses for clarity

Response format:
1. Always include operation status (success/failure)
2. Provide relevant file metadata (path, line counts)
3. For read operations, clearly indicate line ranges
4. For write operations, confirm changes made
5. Include actionable messages for next steps
"""

async def create_agent():
    """Create and initialize the Agent"""
    load_dotenv()
    # Create a new agent
    agent = Agent('file_manipulator_assistant')
    
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
    
    agent.add_tool(server_path, "file_manipulator_operations")
    
    # Initialize the agent
    print("Initializing agent...")
    await agent.initialize()
    
    return agent

@mcp.tool()
async def file_manipulator_tool(query: str) -> str:
    """
    Perform various file operations based on natural language commands.

This tool enables reading, writing, modifying, and managing files through natural language
queries. It supports operations on both local and cloud storage files.

Input format:
- Natural language commands specifying file operations
- Can include file paths, content to write, or specific modifications
- May specify file formats (text, binary, JSON, etc.)
- Can include search patterns or filters for file operations

Returns:
- 'content': File contents for read operations (None for write/modify)
- 'status': Operation result ('success', 'partial_success', 'failed')
- 'message': Detailed information about operation outcome
- 'file_path': Path of affected file(s)
- 'file_size': Size of affected file(s) in bytes (when applicable)

Examples:
- "Read the contents of /documents/report.txt"
- "Create a new file at /data/config.json with this content: {'timeout': 30}"
- "Append 'Updated on 2024-01-15' to /logs/system.log"
- "Search for all .csv files in /downloads and return their sizes"
- "Compress /backups/project_files into a zip archive"
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