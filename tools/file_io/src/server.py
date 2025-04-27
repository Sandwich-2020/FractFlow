"""
File I/O Tool Server Module

This module provides a FastMCP server that exposes file and directory operations as tools.
It wraps the core file I/O logic in a server interface that can be used by the EnvisionCore
framework. Each tool is exposed as an endpoint that can be called by the EnvisionCore agent.

The server provides tools for:
- Reading and writing files
- Listing directory contents
- Moving, copying, and deleting files and directories
- Checking file existence
- Getting detailed file information
- Creating directories

Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-04-27
License: MIT License
"""

from mcp.server.fastmcp import FastMCP
import os
import sys
from pathlib import Path
from typing import Optional, List
# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from core_logic import (
    read_file, 
    write_file, 
    list_directory, 
    delete_file, 
    move_file, 
    copy_file, 
    file_exists, 
    get_file_info,
    create_directory as create_dir_core,
    expand_path
)

# Initialize MCP server
mcp = FastMCP("file_io_tool")

@mcp.tool()
async def read(file_path: str, binary: bool = False):
    """
    Read content from a file and return it as text or binary data.
    
    Parameters:
        file_path (str): The absolute or relative path to the file to read
        binary (bool, optional): Whether to read in binary mode. Defaults to False.
        
    Returns:
        Union[str, bytes]: The content of the file as a string (if binary=False) or as bytes (if binary=True)
        
    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If permission is denied to read the file
    """
    return await read_file(file_path, binary)

@mcp.tool()
async def write(file_path: str, content: str, binary: bool = False):
    """
    Write content to a file. Creates the file if it doesn't exist.
    
    Parameters:
        file_path (str): The absolute or relative path to the file to write
        content (str): The content to write to the file
        binary (bool, optional): Whether to write in binary mode. Defaults to False.
        
    Returns:
        bool: True if the write operation was successful
        
    Raises:
        PermissionError: If permission is denied to write to the file
        IOError: If the write operation fails
    """
    return await write_file(file_path, content, binary)

@mcp.tool()
async def list_files(directory_path: str):
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
            
    Raises:
        FileNotFoundError: If the specified directory does not exist
        PermissionError: If permission is denied to read the directory
    """
    return await list_directory(directory_path)

@mcp.tool()
async def delete(file_path: str):
    """
    Delete a file or directory. For directories, this will recursively delete all contents.
    
    Parameters:
        file_path (str): The absolute or relative path to the file or directory to delete
        
    Returns:
        bool: True if the delete operation was successful
        
    Raises:
        FileNotFoundError: If the specified file or directory does not exist
        PermissionError: If permission is denied to delete the file or directory
    """
    return await delete_file(file_path)

@mcp.tool()
async def move(source_path: str, destination_path: str):
    """
    Move a file or directory from source to destination. Creates parent directories if needed.
    
    Parameters:
        source_path (str): The absolute or relative path to the source file or directory
        destination_path (str): The absolute or relative path to the destination location
        
    Returns:
        bool: True if the move operation was successful
        
    Raises:
        FileNotFoundError: If the source file or directory does not exist
        PermissionError: If permission is denied for the operation
    """
    return await move_file(source_path, destination_path)

@mcp.tool()
async def copy(source_path: str, destination_path: str):
    """
    Copy a file or directory from source to destination. Creates parent directories if needed.
    
    Parameters:
        source_path (str): The absolute or relative path to the source file or directory
        destination_path (str): The absolute or relative path to the destination location
        
    Returns:
        bool: True if the copy operation was successful
        
    Raises:
        FileNotFoundError: If the source file or directory does not exist
        PermissionError: If permission is denied for the operation
    """
    return await copy_file(source_path, destination_path)

@mcp.tool()
async def exists(file_path: str):
    """
    Check if a file or directory exists at the specified path.
    
    Parameters:
        file_path (str): The absolute or relative path to check
        
    Returns:
        bool: True if the file or directory exists, False otherwise
    """
    return await file_exists(file_path)

@mcp.tool()
async def info(file_path: str, fields: Optional[List[str]] = None):
    """
    Get detailed information about a file or directory.
    
    Parameters:
        file_path (str): The absolute or relative path to the file or directory
        fields (Optional[List[str]]): List of specific fields to return. If not provided, returns all available fields.
                                    Available fields include: name, path, is_dir, size, created, modified, accessed,
                                    extension, parent, permissions, owner, group.
        
    Returns:
        Dict[str, Any]: A dictionary containing file metadata (filtered by fields if specified):
            - name (str): The name of the file or directory
            - path (str): The full path to the file or directory
            - is_dir (bool): Whether the item is a directory
            - size (int): The size of the file in bytes (None for directories)
            - created (float): The creation timestamp
            - modified (float): The last modified timestamp
            - accessed (float): The last accessed timestamp
            - extension (str): The file extension (None for directories)
            - parent (str): The directory containing this file/directory
            - permissions (int): Unix-style permission bits
            - owner (int): User ID of the file owner
            - group (int): Group ID of the file owner
            
    Raises:
        FileNotFoundError: If the specified file or directory does not exist
        
    Examples:
        # Get all information
        info("/path/to/file.txt")
        
        # Get only name and size
        info("/path/to/file.txt", ["name", "size"])
        
        # Get modification info
        info("/path/to/file.txt", ["modified", "accessed"])

        # list all files in a directory (for example, ~/Documents)
        info("~/Documents", ["name"])
    
    Notes:
        - Filter out as much as possible the information of the returned files and only return the necessary fields.
    """
    return await get_file_info(file_path, fields)

@mcp.tool()
async def create_directory(directory_path: str):
    """
    Create a directory at the specified path. Creates parent directories if needed.
    
    Parameters:
        directory_path (str): The absolute or relative path to the directory to create
        
    Returns:
        bool: True if the directory was created successfully or already exists
        
    Raises:
        PermissionError: If permission is denied to create the directory
    """
    return await create_dir_core(directory_path)

if __name__ == "__main__":
    mcp.run(transport='stdio') 