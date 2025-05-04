"""
Code Generation Tool Server Module

This module provides a FastMCP server that exposes file editing operations as tools.
It wraps the core file editing logic in a server interface that can be used by the EnvisionCore
framework. Each tool is exposed as an endpoint that can be called by the EnvisionCore agent.

The server provides tools for:
- Reading files with line numbers
- Editing files with line range support
- Partial file editing for large files
- Appending to files
- Auto-creating files if they don't exist
- Listing directory contents
- Removing lines from files

Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-08-11
License: MIT License
"""

from mcp.server.fastmcp import FastMCP
import os
import sys
from pathlib import Path
from typing import Optional, List, Union, Dict, Any

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the file_io module (instead of individual functions)
import src.file_io as file_io

# Initialize MCP server
mcp = FastMCP("codegen2_tool")

@mcp.tool()
async def read_file(file_path: str, is_return_line_numbers: bool = True):
    """
    Read content from a file, optionally including line numbers.
    
    Parameters:
        file_path (str): The absolute or relative path to the file to read
        is_return_line_numbers (bool, optional): Whether to include line numbers in the content.
                                               Default is True.
        
    Returns:
        str: The content of the file as a string, optionally with line numbers formatted as "1|line content"
        
    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If permission is denied to read the file
    """
    return await file_io.read_file(file_path, is_return_line_numbers)

@mcp.tool()
async def read_file_range(file_path: str, start_line: int = 1, end_line: Optional[int] = None):
    """
    Read a specific range of lines from a file.
    
    Parameters:
        file_path (str): The absolute or relative path to the file to read
        start_line (int, optional): Starting line number (1-indexed). Default is 1.
        end_line (int, optional): Ending line number (inclusive, 1-indexed).
                                If None, reads to the end of the file. Default is None.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - content (str): The content of the specified line range
            - start_line (int): The actual start line used
            - end_line (int): The actual end line used
            - total_lines (int): Total number of lines in the file
        
    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If permission is denied to read the file
    """
    content, actual_start, actual_end = await file_io.read_file_with_line_range(file_path, start_line, end_line)
    
    # Get total lines in file by reading the file and counting lines
    file_path = file_io.expand_path(file_path)
    with open(file_path, "r") as file:
        total_lines = sum(1 for _ in file)
    
    return {
        'content': content,
        'start_line': actual_start,
        'end_line': actual_end,
        'total_lines': total_lines
    }

@mcp.tool()
async def list_directory(directory_path: str):
    """
    List all files and directories in the specified directory with metadata.
    
    Parameters:
        directory_path (str): The absolute or relative path to the directory to list
        
    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing file/directory metadata:
            - name (str): The name of the file or directory
            - path (str): The full path to the file or directory
            - is_dir (bool): Whether the item is a directory
            - size (int): The size of the file in bytes (None for directories)
            - modified (float): The last modified timestamp
            - type (str): Type of the item ('file' or 'directory')
            
    Raises:
        FileNotFoundError: If the specified directory does not exist
        NotADirectoryError: If the specified path is not a directory
        PermissionError: If permission is denied to read the directory
    """
    return await file_io.list_directory(directory_path)

@mcp.tool()
async def edit_file(file_path: str, content: str, start_line: int = 1, end_line: int = -1):
    """
    Edit a file by replacing content between start_line and end_line.
    
    Parameters:
        file_path (str): The absolute or relative path to the file to edit
        content (str): New content to insert
        start_line (int, optional): Starting line number (1-indexed). Default is 1 (beginning of file).
                                  Special case: if start_line is -1, content will be appended to the end of the file.
        end_line (int, optional): Ending line number (1-indexed, inclusive).
                                Default is -1 (end of file).
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if the edit operation was successful
            - file_path (str): The path of the edited file
            - created (bool): True if the file was created, False if it existed
        
    Raises:
        PermissionError: If permission is denied to write to the file
        
    Notes:
        - If the file does not exist, it will be created automatically
        - If start_line is -1, content will be appended to the end of the file
        - If start_line is larger than the file size, content will be appended
        - If end_line is -1, it means the end of the file
        - If end_line is larger than the file size, it will be treated as the end of the file
        
    Examples:
        # Replace entire file
        edit_file("/path/to/file.txt", "New content")
        
        # Edit specific lines
        edit_file("/path/to/file.txt", "New content", 3, 5)
        
        # Append to file
        edit_file("/path/to/file.txt", "New content", -1, -1)
    """
    # Check if the file exists before editing
    file_path = file_io.expand_path(file_path)
    file_existed = os.path.exists(file_path)
    
    # Perform the edit
    success = await file_io.edit_file(file_path, content, start_line, end_line)
    
    return {
        'success': success,
        'file_path': file_path,
        'created': not file_existed
    } 

@mcp.tool()
async def remove_file_lines(file_path: str, start_line: int, end_line: int = -1):
    """
    Remove specified lines from a file.
    
    Parameters:
        file_path (str): The absolute or relative path to the file to edit
        start_line (int): Starting line number to remove (1-indexed)
        end_line (int, optional): Ending line number to remove (1-indexed, inclusive).
                                Default is -1 (end of file).
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if the removal operation was successful
            - file_path (str): The path of the edited file
            - removed_lines (int): Number of lines removed
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If permission is denied to write to the file
        
    Notes:
        - If end_line is -1, it means removing from start_line to the end of the file
        - If the line range is invalid or outside file boundaries, the function will
          still complete but may not remove any lines
        
    Examples:
        # Remove lines 3-5
        remove_file_lines("/path/to/file.txt", 3, 5)
        
        # Remove from line 10 to the end of the file
        remove_file_lines("/path/to/file.txt", 10)
    """
    # Expand path and check if file exists
    file_path = file_io.expand_path(file_path)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Get number of lines in the file
    with open(file_path, "r") as file:
        total_lines = sum(1 for _ in file)
    
    # Calculate effective line range
    effective_start = max(1, min(start_line, total_lines))
    effective_end = total_lines if end_line == -1 else min(end_line, total_lines)
    
    # Calculate number of lines to be removed
    if effective_start <= effective_end:
        removed_lines = effective_end - effective_start + 1
    else:
        removed_lines = 0
    
    # Perform the removal
    success = await file_io.remove_lines(file_path, start_line, end_line)
    
    return {
        'success': success,
        'file_path': file_path,
        'removed_lines': removed_lines
    }

if __name__ == "__main__":
    mcp.run(transport='stdio') 