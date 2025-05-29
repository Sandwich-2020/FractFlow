"""
File Manipulator Tool Server

This module provides direct MCP tool implementations for the File Manipulator tool.
These functions are designed to be exposed as MCP tools and used by the AI server.
"""

# Standard library imports
import os
import sys
from typing import Dict, Any, List, Optional

# MCP framework imports
from mcp.server.fastmcp import FastMCP

# Add current directory to Python path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Source-specific imports (generated based on source code analysis)
# 1. 源码特定导入部分
from file_operations import (
    normalize_path,
    check_file_exists,
    get_file_line_count,
    read_file_range,
    read_file_chunks,
    read_file_with_line_numbers,
    create_or_write_file,
    append_to_file,
    insert_at_line,
    delete_line
)

# 2. 工具函数定义部分

# Initialize FastMCP server
mcp = FastMCP("file_manipulator")

@mcp.tool()
def tool_normalize_path(file_path: str) -> str:
    """
    Normalizes a file path to prevent path traversal attacks and returns the absolute path.
    
    Args:
        file_path (str): The file path to normalize
        
    Returns:
        str: Normalized absolute file path
    """
    return normalize_path(file_path)

@mcp.tool()
def tool_check_file_exists(file_path: str) -> Dict[str, Union[bool, str]]:
    """
    Checks if a file exists at the specified path and returns detailed status information.
    
    Args:
        file_path (str): Path to the file to check
        
    Returns:
        Dict: {
            'exists': bool - whether file exists,
            'path': str - normalized path checked,
            'message': str - optional status message,
            'error': str - optional error message
        }
    """
    return check_file_exists(file_path)

@mcp.tool()
def tool_get_file_line_count(file_path: str) -> Dict[str, Union[int, str, bool]]:
    """
    Counts the number of lines in a file and returns the result with metadata.
    
    Args:
        file_path (str): Path to the file to count lines
        
    Returns:
        Dict: {
            'success': bool - whether operation succeeded,
            'line_count': int - number of lines (if successful),
            'path': str - normalized file path,
            'error': str - optional error message,
            'message': str - optional status message
        }
    """
    return get_file_line_count(file_path)

@mcp.tool()
def tool_read_file_range(
    file_path: str, 
    start_line: int = 1, 
    end_line: Optional[int] = None
) -> Dict[str, Union[str, int, bool, List[str]]]:
    """
    Reads a range of lines from a file with optional start and end line numbers.
    
    Args:
        file_path (str): Path to the file to read
        start_line (int): Starting line number (1-indexed, default: 1)
        end_line (Optional[int]): Ending line number (inclusive), None reads to end
        
    Returns:
        Dict: {
            'success': bool - whether operation succeeded,
            'content': str - file content as string,
            'lines': List[str] - lines as list,
            'start_line': int - actual start line,
            'end_line': int - actual end line,
            'line_count': int - total lines in file,
            'path': str - normalized file path,
            'error': str - optional error message
        }
    """
    return read_file_range(file_path, start_line, end_line)

@mcp.tool()
def tool_read_file_chunks(
    file_path: str, 
    chunk_size: int, 
    overlap: int = 0, 
    chunk_index: Optional[int] = None
) -> Dict[str, Union[str, int, bool, List[Dict]]]:
    """
    Reads a file in chunks with optional overlap between chunks.
    
    Args:
        file_path (str): Path to the file
        chunk_size (int): Number of lines per chunk
        overlap (int): Overlapping lines between chunks (default: 0)
        chunk_index (Optional[int]): Specific chunk to retrieve (0-indexed)
        
    Returns:
        Dict: Either chunk metadata or specific chunk content with:
            - 'chunks': List[Dict] - chunk metadata (if chunk_index=None)
            OR
            - 'content': str - chunk content (if chunk_index specified)
            Plus common fields like 'success', 'path', 'error' etc.
    """
    return read_file_chunks(file_path, chunk_size, overlap, chunk_index)

@mcp.tool()
def tool_read_file_with_line_numbers(
    file_path: str, 
    start_line: int = 1, 
    end_line: Optional[int] = None
) -> Dict[str, Union[str, int, bool]]:
    """
    Reads file content with line numbers prepended to each line.
    
    Args:
        file_path (str): Path to the file
        start_line (int): Starting line number (1-indexed, default: 1)
        end_line (Optional[int]): Ending line number (inclusive), None reads to end
        
    Returns:
        Dict: Same structure as tool_read_file_range but with numbered content
    """
    return read_file_with_line_numbers(file_path, start_line, end_line)

@mcp.tool()
def tool_create_or_write_file(
    file_path: str, 
    content: str
) -> Dict[str, Union[bool, str]]:
    """
    Creates a new file or overwrites existing file with given content.
    
    Args:
        file_path (str): Path to the file
        content (str): Content to write
        
    Returns:
        Dict: {
            'success': bool - whether operation succeeded,
            'path': str - normalized file path,
            'message': str - status message,
            'error': str - optional error message
        }
    """
    return create_or_write_file(file_path, content)

@mcp.tool()
def tool_append_to_file(
    file_path: str, 
    content: str
) -> Dict[str, Union[bool, str]]:
    """
    Appends content to an existing file or creates new file if not exists.
    
    Args:
        file_path (str): Path to the file
        content (str): Content to append
        
    Returns:
        Dict: Same structure as tool_create_or_write_file
    """
    return append_to_file(file_path, content)

@mcp.tool()
def tool_insert_at_line(
    file_path: str, 
    line_number: int, 
    content: str
) -> Dict[str, Union[bool, str, int]]]:
    """
    Inserts content at specified line in file, creating file if needed.
    
    Args:
        file_path (str): Path to the file
        line_number (int): Line number to insert at (1-indexed)
        content (str): Content to insert
        
    Returns:
        Dict: {
            'success': bool - whether operation succeeded,
            'path': str - normalized file path,
            'line_count': int - new line count,
            'message': str - status message,
            'error': str - optional error message
        }
    """
    return insert_at_line(file_path, line_number, content)

@mcp.tool()
def tool_delete_line(
    file_path: str, 
    line_number: int
) -> Dict[str, Union[bool, str, int]]:
    """
    Deletes specified line from a file.
    
    Args:
        file_path (str): Path to the file
        line_number (int): Line number to delete (1-indexed)
        
    Returns:
        Dict: {
            'success': bool - whether operation succeeded,
            'path': str - normalized file path,
            'deleted_line': str - the deleted line content,
            'new_line_count': int - updated line count,
            'message': str - status message,
            'error': str - optional error message
        }
    """
    return delete_line(file_path, line_number)

if __name__ == "__main__":
    mcp.run(transport='stdio') 