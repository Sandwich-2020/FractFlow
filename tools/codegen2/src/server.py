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
- String replacement with uniqueness validation
- Line insertion
- Undo previous edits
- File backup

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
from src.file_io import FileIOError

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
        FileIOError: If the file can't be read (doesn't exist, permission denied, etc.)
    """
    try:
        return await file_io.read_file(file_path, is_return_line_numbers)
    except FileIOError as e:
        raise e

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
        FileIOError: If the file can't be read (doesn't exist, permission denied, etc.)
    """
    try:
        content, actual_start, actual_end = await file_io.read_file_with_line_range(file_path, start_line, end_line)
        
        # Get total lines in file
        path = file_io.expand_path(file_path)
        with open(path, "r", encoding="utf-8") as file:
            total_lines = sum(1 for _ in file)
        
        return {
            'content': content,
            'start_line': actual_start,
            'end_line': actual_end,
            'total_lines': total_lines
        }
    except FileIOError as e:
        raise e

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
        FileIOError: If the directory can't be accessed (doesn't exist, not a directory, permission denied)
    """
    try:
        return await file_io.list_directory(directory_path)
    except FileIOError as e:
        raise e

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
        FileIOError: If the file can't be edited (permission denied, path invalid, etc.)
        
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
    try:
        # Check if the file exists before editing
        path = file_io.expand_path(file_path)
        file_existed = path.exists()
        
        # Perform the edit
        success = await file_io.edit_file(file_path, content, start_line, end_line)
        
        return {
            'success': success,
            'file_path': str(path),
            'created': not file_existed
        }
    except FileIOError as e:
        raise e

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
        FileIOError: If the file can't be edited (doesn't exist, permission denied, etc.)
        
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
    try:
        # Expand path and check if file exists
        path = file_io.expand_path(file_path)
        
        # Get number of lines in the file
        if path.exists():
            with open(path, "r", encoding="utf-8") as file:
                total_lines = sum(1 for _ in file)
            
            # Calculate effective line range
            effective_start = max(1, min(start_line, total_lines))
            effective_end = total_lines if end_line == -1 else min(end_line, total_lines)
            
            # Calculate number of lines to be removed
            if effective_start <= effective_end:
                removed_lines = effective_end - effective_start + 1
            else:
                removed_lines = 0
        else:
            raise FileIOError(f"File not found: {path}")
        
        # Perform the removal
        success = await file_io.remove_lines(file_path, start_line, end_line)
        
        return {
            'success': success,
            'file_path': str(path),
            'removed_lines': removed_lines
        }
    except FileIOError as e:
        raise e

@mcp.tool()
async def str_replace(file_path: str, old_str: str, new_str: str, require_unique: bool = True):
    """
    Replace a string in a file, with option to require uniqueness.
    
    Parameters:
        file_path (str): The absolute or relative path to the file to edit
        old_str (str): String to replace
        new_str (str): Replacement string
        require_unique (bool, optional): Whether to require the old string appears exactly once.
                                      Default is True.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if the replacement was successful
            - file_path (str): The path of the edited file
            - lines_affected (List[int]): Line numbers where replacements were made (1-indexed)
            - count (int): Number of replacements made
        
    Raises:
        FileIOError: If the file can't be edited or uniqueness requirement is violated
        
    Notes:
        - If require_unique is True and the string appears multiple times, an error is raised
        - If the string doesn't appear in the file, success will be False and count will be 0
        
    Examples:
        # Replace a unique string
        str_replace("/path/to/file.txt", "old text", "new text")
        
        # Replace all occurrences of a string
        str_replace("/path/to/file.txt", "old text", "new text", require_unique=False)
    """
    try:
        path = file_io.expand_path(file_path)
        success, affected_lines = await file_io.str_replace(file_path, old_str, new_str, require_unique)
        
        return {
            'success': success,
            'file_path': str(path),
            'lines_affected': affected_lines,
            'count': len(affected_lines)
        }
    except FileIOError as e:
        raise e

@mcp.tool()
async def insert_lines(file_path: str, insert_line: int, new_text: str):
    """
    Insert text at a specific line in a file.
    
    Parameters:
        file_path (str): The absolute or relative path to the file to edit
        insert_line (int): Line number to insert at (1-indexed).
                         Use 0 to insert at the beginning of the file.
        new_text (str): Text to insert
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if the insertion was successful
            - file_path (str): The path of the edited file
            - insert_position (int): Position where the text was inserted
        
    Raises:
        FileIOError: If the file can't be edited or the line number is invalid
        
    Notes:
        - If insert_line is 0, the text is inserted at the beginning of the file
        - If insert_line is greater than the file's line count, an error is raised
        
    Examples:
        # Insert at the beginning of the file
        insert_lines("/path/to/file.txt", 0, "New content at the beginning")
        
        # Insert after line 5
        insert_lines("/path/to/file.txt", 5, "New content after line 5")
    """
    try:
        path = file_io.expand_path(file_path)
        success = await file_io.insert_lines(file_path, insert_line, new_text)
        
        return {
            'success': success,
            'file_path': str(path),
            'insert_position': insert_line
        }
    except FileIOError as e:
        raise e

@mcp.tool()
async def undo_edit(file_path: str):
    """
    Undo the last edit to a file.
    
    Parameters:
        file_path (str): The absolute or relative path to the file
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if the undo was successful
            - file_path (str): The path of the file
            - message (str): Description of the action performed
        
    Raises:
        FileIOError: If there's no edit history for the file or the file can't be accessed
        
    Notes:
        - This tool can undo the most recent edit operation performed on the file
        - Each file maintains its own history of recent changes
        - If no edit history exists for the file, an error is raised
        
    Examples:
        # Undo the last edit to a file
        undo_edit("/path/to/file.txt")
    """
    try:
        path = file_io.expand_path(file_path)
        success = await file_io.undo_edit(file_path)
        
        return {
            'success': success,
            'file_path': str(path),
            'message': f"Last edit to {path.name} was successfully undone"
        }
    except FileIOError as e:
        raise e

@mcp.tool()
async def make_backup(file_path: str):
    """
    Create a backup of a file.
    
    Parameters:
        file_path (str): The absolute or relative path to the file to back up
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if the backup was successful
            - file_path (str): The path of the original file
            - backup_path (str): The path of the backup file
        
    Raises:
        FileIOError: If the file can't be backed up
        
    Notes:
        - The backup file will be created in the same directory as the original file
        - The backup filename will be the original filename with a timestamp and .bak extension
        
    Examples:
        # Create a backup of a file
        make_backup("/path/to/file.txt")  # Creates e.g. /path/to/file.txt.20250811153045.bak
    """
    try:
        path = file_io.expand_path(file_path)
        backup_path = await file_io.make_backup(file_path)
        
        return {
            'success': True,
            'file_path': str(path),
            'backup_path': backup_path
        }
    except FileIOError as e:
        raise e

if __name__ == "__main__":
    mcp.run(transport='stdio') 