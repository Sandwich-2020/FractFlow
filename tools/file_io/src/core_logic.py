"""
Core File I/O Logic Module

This module implements the core file and directory operations for the EnvisionCore file_io tool.
It provides functions for reading, writing, copying, moving, and deleting files and directories,
as well as for retrieving file information and checking file existence.

All functions are implemented as async to maintain compatibility with the server interface,
although the underlying operations are synchronous file system calls.

Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-04-27
License: MIT License
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Union, Optional, Any, BinaryIO


def expand_path(file_path: str) -> str:
    """
    Expand the path to handle home directory (~) and environment variables.
    
    Args:
        file_path (str): Path to expand
        
    Returns:
        str: Expanded file path
    """
    # Expand user home directory (~)
    expanded_path = os.path.expanduser(file_path)
    # Expand environment variables ($VAR)
    expanded_path = os.path.expandvars(expanded_path)
    return expanded_path


async def read_file(file_path: str, binary: bool = False) -> Union[str, bytes]:
    """
    Read content from a file.
    
    Args:
        file_path (str): Path to the file to read
        binary (bool): Whether to read in binary mode
        
    Returns:
        Union[str, bytes]: File content as string or bytes
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If access is denied
    """
    # Expand the path for ~ and environment variables
    file_path = expand_path(file_path)
    
    mode = "rb" if binary else "r"
    with open(file_path, mode) as file:
        return file.read()


async def write_file(file_path: str, content: Union[str, bytes], binary: bool = False) -> bool:
    """
    Write content to a file.
    
    Args:
        file_path (str): Path to the file to write
        content (Union[str, bytes]): Content to write
        binary (bool): Whether to write in binary mode
        
    Returns:
        bool: True if successful
        
    Raises:
        PermissionError: If access is denied
        IOError: If write fails
    """
    # Expand the path for ~ and environment variables
    file_path = expand_path(file_path)
    
    # Make sure directory exists
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        
    mode = "wb" if binary else "w"
    with open(file_path, mode) as file:
        file.write(content)
    return True


async def insert_file(file_path: str, content: Union[str, bytes], position: Union[int, str], 
                     by_line: bool = False, binary: bool = False) -> bool:
    """
    Insert content into a file at a specific position.
    
    Args:
        file_path (str): Path to the file to modify
        content (Union[str, bytes]): Content to insert
        position (Union[int, str]): Position to insert at (line number, byte offset, or pattern)
        by_line (bool): If True, position is interpreted as line number, otherwise as byte offset
        binary (bool): Whether to operate in binary mode
        
    Returns:
        bool: True if successful
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If access is denied
        ValueError: If position is invalid
    """
    # Expand the path for ~ and environment variables
    file_path = expand_path(file_path)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Read mode depends on binary flag
    read_mode = "rb" if binary else "r"
    write_mode = "wb" if binary else "w"
    
    # Handle insertion by line
    if by_line:
        if not isinstance(position, int):
            try:
                position = int(position)
            except ValueError:
                raise ValueError("When by_line is True, position must be a line number (integer)")
        
        # Line numbers are 1-indexed for user convenience
        line_index = position - 1
        if line_index < 0:
            raise ValueError("Line number must be positive")
        
        # Read existing lines
        with open(file_path, read_mode) as file:
            if binary:
                lines = file.read().split(b'\n')
            else:
                lines = file.read().splitlines()
        
        # Insert content at specified line
        if line_index > len(lines):
            # If position is beyond the end of file, append to the end
            if binary:
                lines.append(content)
            else:
                lines.append(content)
        else:
            if binary:
                lines.insert(line_index, content)
            else:
                lines.insert(line_index, content)
        
        # Write back to file
        with open(file_path, write_mode) as file:
            if binary:
                file.write(b'\n'.join(lines))
            else:
                file.write('\n'.join(lines))
    
    # Handle insertion by byte offset
    else:
        if isinstance(position, str):
            # Handle pattern-based insertion
            with open(file_path, read_mode) as file:
                content_before = file.read()
            
            if binary and isinstance(position, str):
                # Convert string pattern to bytes for binary mode
                pattern = position.encode()
            else:
                pattern = position
            
            # Find pattern in content
            if binary:
                pattern_index = content_before.find(pattern)
            else:
                pattern_index = content_before.find(pattern)
            
            if pattern_index == -1:
                raise ValueError(f"Pattern '{position}' not found in file")
            
            # Use pattern index as position
            position = pattern_index + len(pattern)
        else:
            try:
                position = int(position)
            except ValueError:
                raise ValueError("Position must be a byte offset (integer) or a pattern (string)")
        
        # Read file content
        with open(file_path, read_mode) as file:
            content_before = file.read(position)
            content_after = file.read()
        
        # Write modified content
        with open(file_path, write_mode) as file:
            file.write(content_before)
            file.write(content)
            file.write(content_after)
    
    return True


async def list_directory(directory_path: str) -> List[Dict[str, Any]]:
    """
    List all files and directories in the specified directory.
    
    Args:
        directory_path (str): Path to the directory
        
    Returns:
        List[Dict[str, Any]]: List of files and directories with metadata
        
    Raises:
        FileNotFoundError: If the directory doesn't exist
        PermissionError: If access is denied
    """
    # Expand the path for ~ and environment variables
    directory_path = expand_path(directory_path)
    
    directory_path = Path(directory_path)
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    result = []
    for item in directory_path.iterdir():
        item_info = {
            "name": item.name,
            "path": str(item),
            "is_dir": item.is_dir(),
            "size": item.stat().st_size if not item.is_dir() else None,
            "modified": item.stat().st_mtime
        }
        result.append(item_info)
    
    return result


async def delete_file(file_path: str) -> bool:
    """
    Delete a file or directory.
    
    Args:
        file_path (str): Path to the file or directory to delete
        
    Returns:
        bool: True if successful
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If access is denied
    """
    # Expand the path for ~ and environment variables
    file_path = expand_path(file_path)
    
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {file_path}")
    
    if path.is_dir():
        shutil.rmtree(path)
    else:
        os.remove(path)
    
    return True


async def move_file(source_path: str, destination_path: str) -> bool:
    """
    Move a file or directory from source to destination.
    
    Args:
        source_path (str): Source file/directory path
        destination_path (str): Destination file/directory path
        
    Returns:
        bool: True if successful
        
    Raises:
        FileNotFoundError: If the source doesn't exist
        PermissionError: If access is denied
    """
    # Expand the paths for ~ and environment variables
    source_path = expand_path(source_path)
    destination_path = expand_path(destination_path)
    
    # Make sure destination directory exists
    dest_dir = os.path.dirname(destination_path)
    if dest_dir and not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        
    shutil.move(source_path, destination_path)
    return True


async def copy_file(source_path: str, destination_path: str) -> bool:
    """
    Copy a file or directory from source to destination.
    
    Args:
        source_path (str): Source file/directory path
        destination_path (str): Destination file/directory path
        
    Returns:
        bool: True if successful
        
    Raises:
        FileNotFoundError: If the source doesn't exist
        PermissionError: If access is denied
    """
    # Expand the paths for ~ and environment variables
    source_path = expand_path(source_path)
    destination_path = expand_path(destination_path)
    
    # Make sure destination directory exists
    dest_dir = os.path.dirname(destination_path)
    if dest_dir and not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    source_path = Path(source_path)
    if source_path.is_dir():
        shutil.copytree(source_path, destination_path)
    else:
        shutil.copy2(source_path, destination_path)
    
    return True


async def file_exists(file_path: str) -> bool:
    """
    Check if a file or directory exists.
    
    Args:
        file_path (str): Path to check
        
    Returns:
        bool: True if exists, False otherwise
    """
    # Expand the path for ~ and environment variables
    file_path = expand_path(file_path)
    
    return os.path.exists(file_path)


async def get_file_info(file_path: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Get detailed information about a file or directory.
    
    Args:
        file_path (str): Path to the file or directory
        fields (Optional[List[str]]): List of specific fields to return.
                                     If None, returns all available fields.
                                     
    Returns:
        Dict[str, Any]: File metadata (filtered by fields if specified)
        
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    # Expand the path for ~ and environment variables
    file_path = expand_path(file_path)
    
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {file_path}")
    
    # Get all available file information
    stat = path.stat()
    full_info = {
        "name": path.name,
        "path": str(path),
        "is_dir": path.is_dir(),
        "size": stat.st_size if not path.is_dir() else None,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "accessed": stat.st_atime,
        "extension": path.suffix if not path.is_dir() else None,
        "parent": str(path.parent),
        "permissions": stat.st_mode & 0o777,  # Get Unix-style permissions
        "owner": stat.st_uid,
        "group": stat.st_gid
    }
    
    # Return only requested fields if specified
    if fields is not None:
        # Filter the information dictionary to include only requested fields
        # If a requested field doesn't exist, it's ignored
        return {k: v for k, v in full_info.items() if k in fields}
        
    # Return all information if no fields specified
    return full_info 

async def create_directory(directory_path: str) -> bool:
    """
    Create a directory at the specified path. Creates parent directories if needed.
    
    Args:
        directory_path (str): Path to the directory to create
        
    Returns:
        bool: True if successful
        
    Raises:
        PermissionError: If access is denied
    """
    # Expand the path for ~ and environment variables
    directory_path = expand_path(directory_path)
    
    Path(directory_path).mkdir(parents=True, exist_ok=True)
    return True 