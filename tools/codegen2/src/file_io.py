"""
Code Generation Tool File I/O Module

This module implements the core file editing operations for the EnvisionCore codegen2 tool.
It provides functions for reading files with line numbers and editing files with line range support,
including partial file edits, handling large files, appending to files, and automatic file creation.

All functions are implemented as async to maintain compatibility with the server interface,
although the underlying operations are synchronous file system calls.

Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-08-11
License: MIT License
"""

import os
import json
import shutil
from pathlib import Path
import datetime
from typing import Dict, List, Union, Optional, Any, BinaryIO, Tuple


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


async def read_file(file_path: str, is_return_line_numbers: bool = False) -> str:
    """
    Read content from a file, optionally including line numbers.
    
    Args:
        file_path (str): Path to the file to read
        is_return_line_numbers (bool): Whether to include line numbers in the content
        
    Returns:
        str: File content as string, optionally with line numbers formatted as "1|line content"
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If access is denied
    """
    # Expand the path for ~ and environment variables
    file_path = expand_path(file_path)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Read the file
    with open(file_path, "r") as file:
        lines = file.readlines()
    
    # Return with or without line numbers
    if is_return_line_numbers:
        # Format lines with line numbers: "1|line content"
        numbered_lines = []
        for i, line in enumerate(lines, 1):
            line = line.rstrip('\n')  # Remove trailing newline
            numbered_lines.append(f"{i}|{line}")
        return '\n'.join(numbered_lines)
    else:
        return ''.join(lines)


async def read_file_with_line_range(file_path: str, start_line: int = 1, end_line: Optional[int] = None) -> Tuple[str, int, int]:
    """
    Read a specific range of lines from a file.
    
    Args:
        file_path (str): Path to the file to read
        start_line (int): Starting line number (1-indexed)
        end_line (Optional[int]): Ending line number (inclusive, 1-indexed)
                                 If None, reads to the end of the file
        
    Returns:
        Tuple[str, int, int]: Tuple containing:
            - content (str): The content of the specified line range
            - actual_start (int): The actual start line used (may differ if start_line was invalid)
            - actual_end (int): The actual end line used (may differ if end_line was invalid)
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If access is denied
    """
    # Expand the path for ~ and environment variables
    file_path = expand_path(file_path)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Read the file
    with open(file_path, "r") as file:
        lines = file.readlines()
    
    # Validate line numbers
    total_lines = len(lines)
    
    # Adjust start_line if needed (convert to 0-indexed for internal use)
    start_idx = max(0, start_line - 1)  # Ensure not negative
    
    # Adjust end_line if needed
    if end_line is None:
        end_idx = total_lines - 1
    else:
        end_idx = min(end_line - 1, total_lines - 1)  # Ensure not beyond file
    
    # Ensure start doesn't exceed end
    if start_idx > end_idx:
        start_idx = end_idx
    
    # Get the content for the specified range
    selected_lines = lines[start_idx:end_idx + 1]
    content = ''.join(selected_lines)
    
    # Return actual 1-indexed line numbers
    return content, start_idx + 1, end_idx + 1


async def list_directory(directory_path: str) -> List[Dict[str, Any]]:
    """
    List all files and directories in the specified directory with metadata.
    
    Args:
        directory_path (str): Path to the directory to list
        
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
        PermissionError: If permission is denied to read the directory
    """
    # Expand the path for ~ and environment variables
    directory_path = expand_path(directory_path)
    
    # Check if directory exists
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    # Check if path is a directory
    if not os.path.isdir(directory_path):
        raise NotADirectoryError(f"Path is not a directory: {directory_path}")
    
    # List the directory
    result = []
    
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        is_directory = os.path.isdir(item_path)
        
        # Get file/directory stats
        stats = os.stat(item_path)
        
        # Create item metadata
        item_info = {
            'name': item,
            'path': item_path,
            'is_dir': is_directory,
            'type': 'directory' if is_directory else 'file',
            'size': None if is_directory else stats.st_size,
            'modified': stats.st_mtime
        }
        
        result.append(item_info)
    
    # Sort the results: directories first, then files, both alphabetically
    result.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
    
    return result


async def edit_file(file_path: str, content: str, start_line: int = 1, end_line: int = -1) -> bool:
    """
    Edit a file by replacing content between start_line and end_line.
    
    Args:
        file_path (str): Path to the file to edit
        content (str): New content to insert
        start_line (int): Starting line number (1-indexed), default is 1 (beginning of file)
                        Special case: if start_line is -1, content will be appended to the end of the file
        end_line (int): Ending line number (1-indexed, inclusive), 
                       default is -1 (end of file)
        
    Returns:
        bool: True if successful
        
    Notes:
        - If the file does not exist, it will be created
        - If start_line is -1, content will be appended to the end of the file
        - If start_line is larger than the file size, content will be appended
        - If end_line is -1, it means the end of the file
        - If end_line is larger than the file size, it will be treated as the end of the file
    """
    # Expand the path for ~ and environment variables
    file_path = expand_path(file_path)
    
    # Check if the file exists
    file_exists = os.path.exists(file_path)
    
    # If file doesn't exist and we're not appending to the end, create it
    if not file_exists:
        # Create the directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Write the content directly to the new file
        with open(file_path, "w") as file:
            file.write(content)
        return True
    
    # If the file exists, read its contents
    with open(file_path, "r") as file:
        lines = file.readlines()
    
    # Special case: if start_line is -1, we want to append to the end of the file
    if start_line == -1:
        # Add newline before appending if the file doesn't end with one and isn't empty
        if lines and not lines[-1].endswith('\n'):
            new_lines = lines + ['\n' + content]
        else:
            new_lines = lines + [content]
        
        # Write the modified content back to the file
        with open(file_path, "w") as file:
            file.writelines(new_lines)
        return True
    
    # Adjust end_line if it's -1 (end of file)
    if end_line == -1:
        end_line = len(lines)
    
    # Convert to 0-indexed for internal use
    start_idx = start_line - 1
    end_idx = end_line - 1
    
    # Handle special cases
    if start_idx < 0:
        start_idx = 0
    
    if end_idx < 0:
        end_idx = 0
    
    # If start line is beyond the file, append to the end
    if start_idx >= len(lines):
        # Add newline before appending if the file doesn't end with one
        if lines and not lines[-1].endswith('\n'):
            new_lines = lines + ['\n' + content]
        else:
            new_lines = lines + [content]
    else:
        # Split the content into lines
        new_content_lines = content.splitlines(True)  # Keep the newline characters
        
        # Construct the new file content
        new_lines = lines[:start_idx] + new_content_lines
        
        # Add the remaining lines after end_line
        if end_idx + 1 < len(lines):
            # If the new content doesn't end with a newline but needs one, add it
            if new_content_lines and not new_content_lines[-1].endswith('\n') and lines[end_idx + 1:]:
                new_lines.append('\n')
            
            new_lines.extend(lines[end_idx + 1:])
    
    # Write the modified content back to the file
    with open(file_path, "w") as file:
        file.writelines(new_lines)
    
    return True


async def remove_lines(file_path: str, start_line: int, end_line: int = -1) -> bool:
    """
    Remove specified lines from a file.
    
    Args:
        file_path (str): Path to the file to edit
        start_line (int): Starting line number to remove (1-indexed)
        end_line (int): Ending line number to remove (1-indexed, inclusive),
                       default is -1 (end of file)
        
    Returns:
        bool: True if successful
        
    Notes:
        - If end_line is -1, it means removing from start_line to the end of the file
        - If the line range is invalid or outside file boundaries, the function will
          still complete but may not remove any lines
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If access is denied
    """
    # Expand the path for ~ and environment variables
    file_path = expand_path(file_path)
    
    # Check if the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Read the file
    with open(file_path, "r") as file:
        lines = file.readlines()
    
    # Adjust end_line if it's -1 (end of file)
    if end_line == -1:
        end_line = len(lines)
    
    # Convert to 0-indexed for internal use
    start_idx = start_line - 1
    end_idx = end_line - 1
    
    # Handle special cases
    if start_idx < 0:
        start_idx = 0
    
    if end_idx < 0:
        end_idx = 0
    
    if start_idx >= len(lines):
        start_idx = len(lines) - 1
    
    if end_idx >= len(lines):
        end_idx = len(lines) - 1
    
    if start_idx > end_idx:
        # Invalid range, do nothing
        return True
    
    # Remove the specified lines
    new_lines = lines[:start_idx] + lines[end_idx + 1:]
    
    # Write the modified content back to the file
    with open(file_path, "w") as file:
        file.writelines(new_lines)
    
    return True 