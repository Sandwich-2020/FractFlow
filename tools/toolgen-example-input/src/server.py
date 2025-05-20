"""
File Line Manager Tool Server

This module provides direct MCP tool implementations for the File Line Manager tool.
These functions are designed to be exposed as MCP tools and used by the AI server.
"""

import os
import sys
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP



# Initialize FastMCP server
mcp = FastMCP("file_line_manager")

# ===== IMPORTS SECTION =====
import os
from typing import Dict, List, Optional, Union
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


# ===== TOOL FUNCTIONS SECTION =====
@mcp.tool()
def tool_check_file_exists(file_path: str) -> Dict[str, Union[bool, str]]:
    """
    Check if a file exists at the specified path and return its status.
    
    Args:
        file_path (str): The path to the file to check
        
    Returns:
        Dict: {
            "exists": bool,  # Whether the file exists
            "path": str,     # Normalized file path
            "message": str,  # Optional status message
            "error": str     # Optional error message if operation failed
        }
    """
    return check_file_exists(file_path)

@mcp.tool()
def tool_get_file_line_count(file_path: str) -> Dict[str, Union[int, str, bool]]:
    """
    Count the number of lines in a file.
    
    Args:
        file_path (str): Path to the file to analyze
        
    Returns:
        Dict: {
            "success": bool,   # Whether operation succeeded
            "line_count": int, # Number of lines in file (if successful)
            "path": str,       # Normalized file path
            "error": str,      # Error message if operation failed
            "message": str     # Status message
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
    Read a range of lines from a file.
    
    Args:
        file_path (str): Path to the file
        start_line (int): First line to read (1-indexed, default: 1)
        end_line (Optional[int]): Last line to read (inclusive), None reads to end
        
    Returns:
        Dict: {
            "success": bool,     # Whether operation succeeded
            "content": str,      # Combined content of requested lines
            "lines": List[str],  # Individual lines as list
            "start_line": int,   # Actual start line used
            "end_line": int,     # Actual end line used
            "line_count": int,  # Total lines in file
            "path": str,        # Normalized file path
            "error": str,        # Error message if failed
            "message": str       # Status message
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
    Read a file in chunks with optional overlap between chunks.
    
    Args:
        file_path (str): Path to the file
        chunk_size (int): Number of lines per chunk
        overlap (int): Overlapping lines between chunks (default: 0)
        chunk_index (Optional[int]): Specific chunk to retrieve (0-indexed)
        
    Returns:
        Dict: {
            "success": bool,       # Whether operation succeeded
            "content": str,        # Content if chunk_index specified
            "lines": List[str],    # Lines if chunk_index specified
            "chunks": List[Dict],  # Chunk metadata if no chunk_index
            "chunk_count": int,    # Total number of chunks
            "chunk_index": int,    # Current chunk index if specified
            "start_line": int,     # Start line of chunk
            "end_line": int,       # End line of chunk
            "line_count": int,     # Total lines in file
            "path": str,           # Normalized file path
            "error": str,          # Error message if failed
            "message": str         # Status message
        }
    """
    return read_file_chunks(file_path, chunk_size, overlap, chunk_index)

@mcp.tool()
def tool_read_file_with_line_numbers(
    file_path: str,
    start_line: int = 1,
    end_line: Optional[int] = None
) -> Dict[str, Union[str, int, bool]]:
    """
    Read file content with line numbers prepended.
    
    Args:
        file_path (str): Path to the file
        start_line (int): First line to read (1-indexed, default: 1)
        end_line (Optional[int]): Last line to read (inclusive), None reads to end
        
    Returns:
        Dict: {
            "success": bool,     # Whether operation succeeded
            "content": str,      # Content with line numbers
            "start_line": int,   # Actual start line used
            "end_line": int,     # Actual end line used
            "line_count": int,   # Total lines in file
            "path": str,        # Normalized file path
            "error": str,        # Error message if failed
            "message": str      # Status message
        }
    """
    return read_file_with_line_numbers(file_path, start_line, end_line)

@mcp.tool()
def tool_create_or_write_file(
    file_path: str,
    content: str
) -> Dict[str, Union[bool, str]]:
    """
    Create a new file or overwrite existing file with content.
    
    Args:
        file_path (str): Path to the file
        content (str): Content to write
        
    Returns:
        Dict: {
            "success": bool,  # Whether operation succeeded
            "path": str,      # Normalized file path
            "message": str,   # Status message
            "error": str      # Error message if failed
        }
    """
    return create_or_write_file(file_path, content)

@mcp.tool()
def tool_append_to_file(
    file_path: str,
    content: str
) -> Dict[str, Union[bool, str]]:
    """
    Append content to an existing file (creates file if doesn't exist).
    
    Args:
        file_path (str): Path to the file
        content (str): Content to append
        
    Returns:
        Dict: {
            "success": bool,  # Whether operation succeeded
            "path": str,      # Normalized file path
            "message": str,   # Status message
            "error": str      # Error message if failed
        }
    """
    return append_to_file(file_path, content)

@mcp.tool()
def tool_insert_at_line(
    file_path: str,
    line_number: int,
    content: str
) -> Dict[str, Union[bool, str, int]]:
    """
    Insert content at specific line in file (creates file if doesn't exist).
    
    Args:
        file_path (str): Path to the file
        line_number (int): Line position to insert (1-indexed)
        content (str): Content to insert
        
    Returns:
        Dict: {
            "success": bool,  # Whether operation succeeded
            "path": str,     # Normalized file path
            "line_count": int, # New total lines in file
            "message": str,   # Status message
            "error": str     # Error message if failed
        }
    """
    return insert_at_line(file_path, line_number, content)

@mcp.tool()
def tool_delete_line(
    file_path: str,
    line_number: int
) -> Dict[str, Union[bool, str, int]]:
    """
    Delete a specific line from a file.
    
    Args:
        file_path (str): Path to the file
        line_number (int): Line to delete (1-indexed)
        
    Returns:
        Dict: {
            "success": bool,      # Whether operation succeeded
            "path": str,          # Normalized file path
            "deleted_line": str,   # The deleted line content
            "new_line_count": int, # New total lines in file
            "message": str,        # Status message
            "error": str          # Error message if failed
        }
    """
    return delete_line(file_path, line_number)

if __name__ == "__main__":
    mcp.run(transport='stdio') 