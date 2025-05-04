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
from collections import defaultdict


class FileIOError(Exception):
    """Custom exception for file I/O operations with consistent error messaging."""
    pass


# Global file history storage for undo operations
_file_history = defaultdict(list)
# Maximum number of versions to keep per file
_MAX_HISTORY_PER_FILE = 5
# Number of context lines to show in snippets
_SNIPPET_LINES = 4


def expand_path(file_path: str) -> Path:
    """
    Expand the path to handle home directory (~) and environment variables.
    
    Args:
        file_path (str): Path to expand
        
    Returns:
        Path: Expanded path as a Path object
    """
    # Expand user home directory (~)
    expanded_path = os.path.expanduser(file_path)
    # Expand environment variables ($VAR)
    expanded_path = os.path.expandvars(expanded_path)
    # Convert to Path object
    return Path(expanded_path)


def validate_path(file_path: Path, allow_create: bool = False) -> None:
    """
    Validate path for safety and correctness.
    
    Args:
        file_path (Path): Path to validate
        allow_create (bool): Whether to allow non-existent paths (for file creation)
        
    Raises:
        FileIOError: If path is invalid or unsafe
    """
    try:
        # Check if path exists (unless we're creating a new file)
        if not allow_create and not file_path.exists():
            raise FileIOError(f"Path does not exist: {file_path}")
            
        # For existing paths, check if it's a directory when we expect a file
        if file_path.exists() and file_path.is_dir():
            raise FileIOError(f"Expected a file but found a directory: {file_path}")

        # If parent directory doesn't exist for a creation operation
        if allow_create and not file_path.exists() and not file_path.parent.exists():
            # Don't auto-create directories with too many levels for safety
            if len(file_path.parts) > 10:
                raise FileIOError(f"Path has too many nested directories: {file_path}")
    except Exception as e:
        if not isinstance(e, FileIOError):
            raise FileIOError(f"Error validating path {file_path}: {str(e)}")
        raise


def _atomic_write(file_path: Path, content: str, encoding: str = "utf-8") -> None:
    """
    Write to a file atomically using a temporary file.
    
    Args:
        file_path (Path): Target file path
        content (str): Content to write
        encoding (str): File encoding
        
    Raises:
        FileIOError: If writing fails
    """
    try:
        # Create parent directory if it doesn't exist
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
        # Create a temporary file in the same directory
        tmp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
        
        # Write content to temporary file
        with open(tmp_path, "w", encoding=encoding) as f:
            f.write(content)
            
        # Ensure file is flushed to disk
        os.fsync(f.fileno())
            
        # Rename temporary file to target (atomic operation)
        os.replace(tmp_path, file_path)
    except Exception as e:
        # Try to clean up temporary file if it exists
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except:
                pass
        raise FileIOError(f"Failed to write to {file_path}: {str(e)}")


def _save_to_history(file_path: Path, content: str) -> None:
    """
    Save file content to history for undo operations.
    
    Args:
        file_path (Path): File path
        content (str): File content to save
    """
    # Convert Path to string for dictionary key
    path_str = str(file_path)
    
    # Add to history
    _file_history[path_str].append(content)
    
    # Limit history size
    if len(_file_history[path_str]) > _MAX_HISTORY_PER_FILE:
        _file_history[path_str].pop(0)


def _get_snippet(content: str, center_line: int, context_lines: int = _SNIPPET_LINES) -> Tuple[str, int]:
    """
    Extract a snippet from content surrounding a specific line.
    
    Args:
        content (str): Content to extract snippet from
        center_line (int): Line to center snippet around (0-indexed)
        context_lines (int): Number of context lines before and after
        
    Returns:
        Tuple[str, int]: Snippet and the starting line number (1-indexed)
    """
    lines = content.splitlines()
    
    start_line = max(0, center_line - context_lines)
    end_line = min(len(lines), center_line + context_lines + 1)
    
    return "\n".join(lines[start_line:end_line]), start_line + 1


async def read_file(file_path: str, is_return_line_numbers: bool = False) -> str:
    """
    Read content from a file, optionally including line numbers.
    
    Args:
        file_path (str): Path to the file to read
        is_return_line_numbers (bool): Whether to include line numbers in the content
        
    Returns:
        str: File content as string, optionally with line numbers formatted as "1|line content"
        
    Raises:
        FileIOError: If the file doesn't exist or can't be read
    """
    try:
        # Convert to Path object
        path = expand_path(file_path)
        
        # Validate path
        validate_path(path)
        
        # Read the file
        with open(path, "r", encoding="utf-8") as file:
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
    except Exception as e:
        if isinstance(e, FileIOError):
            raise
        raise FileIOError(f"Error reading file {file_path}: {str(e)}")


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
        FileIOError: If the file doesn't exist or can't be read
    """
    try:
        # Convert to Path object
        path = expand_path(file_path)
        
        # Validate path
        validate_path(path)
        
        # Read the file
        with open(path, "r", encoding="utf-8") as file:
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
    except Exception as e:
        if isinstance(e, FileIOError):
            raise
        raise FileIOError(f"Error reading file {file_path}: {str(e)}")


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
        FileIOError: If the directory doesn't exist or can't be accessed
    """
    try:
        # Convert to Path object
        path = expand_path(directory_path)
        
        # Check if directory exists
        if not path.exists():
            raise FileIOError(f"Directory not found: {path}")
        
        # Check if path is a directory
        if not path.is_dir():
            raise FileIOError(f"Path is not a directory: {path}")
        
        # List the directory
        result = []
        
        for item in os.listdir(path):
            item_path = path / item
            is_directory = item_path.is_dir()
            
            # Get file/directory stats
            stats = os.stat(item_path)
            
            # Create item metadata
            item_info = {
                'name': item,
                'path': str(item_path),
                'is_dir': is_directory,
                'type': 'directory' if is_directory else 'file',
                'size': None if is_directory else stats.st_size,
                'modified': stats.st_mtime
            }
            
            result.append(item_info)
        
        # Sort the results: directories first, then files, both alphabetically
        result.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        
        return result
    except Exception as e:
        if isinstance(e, FileIOError):
            raise
        raise FileIOError(f"Error listing directory {directory_path}: {str(e)}")


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
        
    Raises:
        FileIOError: If the file can't be edited
    """
    try:
        # Convert to Path object
        path = expand_path(file_path)
        
        # Check if the file exists
        file_exists = path.exists()
        
        # Save the original content if file exists (for undo)
        if file_exists:
            with open(path, "r", encoding="utf-8") as file:
                original_content = file.read()
                _save_to_history(path, original_content)
        
        # If file doesn't exist, create it (after validating)
        if not file_exists:
            validate_path(path, allow_create=True)
            _atomic_write(path, content)
            return True
            
        # Validate existing file
        validate_path(path)
        
        # Read the file if it exists
        with open(path, "r", encoding="utf-8") as file:
            lines = file.readlines()
        
        # Special case: if start_line is -1, we want to append to the end of the file
        if start_line == -1:
            # Add newline before appending if the file doesn't end with one and isn't empty
            if lines and not lines[-1].endswith('\n'):
                new_content = ''.join(lines) + '\n' + content
            else:
                new_content = ''.join(lines) + content
            
            # Write atomically
            _atomic_write(path, new_content)
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
                new_content = ''.join(lines) + '\n' + content
            else:
                new_content = ''.join(lines) + content
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
                
            new_content = ''.join(new_lines)
        
        # Write the modified content back to the file atomically
        _atomic_write(path, new_content)
        
        return True
    except Exception as e:
        if isinstance(e, FileIOError):
            raise
        raise FileIOError(f"Error editing file {file_path}: {str(e)}")


async def insert_lines(file_path: str, insert_line: int, new_text: str) -> bool:
    """
    Insert text at a specific line in a file.
    
    Args:
        file_path (str): Path to the file
        insert_line (int): Line number to insert at (1-indexed)
                          Use 0 to insert at the beginning of the file
        new_text (str): Text to insert
        
    Returns:
        bool: True if successful
        
    Raises:
        FileIOError: If the file can't be edited or line number is invalid
    """
    try:
        # Convert to Path object
        path = expand_path(file_path)
        
        # Validate path
        validate_path(path)
        
        # Save the original content (for undo)
        with open(path, "r", encoding="utf-8") as file:
            original_content = file.read()
            _save_to_history(path, original_content)
        
        # Read the file
        with open(path, "r", encoding="utf-8") as file:
            lines = file.readlines()
        
        # Validate insert line
        if insert_line < 0 or insert_line > len(lines):
            raise FileIOError(f"Invalid insert_line {insert_line}. Valid range is 0-{len(lines)}")
        
        # Prepare new text, ensuring it ends with newline if needed
        new_text_lines = new_text.splitlines(True)  # Keep newlines
        
        # Insert lines
        if insert_line == 0:
            # Insert at beginning
            new_lines = new_text_lines + lines
        else:
            # Insert at specified position
            new_lines = lines[:insert_line] + new_text_lines + lines[insert_line:]
        
        # Ensure proper line breaks between inserted content and existing content
        new_content = ''.join(new_lines)
        
        # Write atomically
        _atomic_write(path, new_content)
        
        # Create snippet for return info
        snippet, snippet_line = _get_snippet(new_content, insert_line, _SNIPPET_LINES)
        
        return True
    except Exception as e:
        if isinstance(e, FileIOError):
            raise
        raise FileIOError(f"Error inserting lines in file {file_path}: {str(e)}")


async def str_replace(file_path: str, old_str: str, new_str: str, require_unique: bool = True) -> Tuple[bool, List[int]]:
    """
    Replace a string in a file.
    
    Args:
        file_path (str): Path to the file
        old_str (str): String to replace
        new_str (str): Replacement string
        require_unique (bool): Whether the old string must appear exactly once
        
    Returns:
        Tuple[bool, List[int]]: Success flag and list of line numbers where replacements were made
        
    Raises:
        FileIOError: If the file can't be edited or if multiple occurrences found when require_unique=True
    """
    try:
        # Convert to Path object
        path = expand_path(file_path)
        
        # Validate path
        validate_path(path)
        
        # Save the original content (for undo)
        with open(path, "r", encoding="utf-8") as file:
            original_content = file.read()
            _save_to_history(path, original_content)
        
        # Find occurrences
        lines = original_content.splitlines()
        occurrence_lines = []
        
        for i, line in enumerate(lines):
            if old_str in line:
                occurrence_lines.append(i + 1)  # 1-indexed
        
        # Check uniqueness if required
        if require_unique and len(occurrence_lines) > 1:
            raise FileIOError(
                f"Multiple occurrences of string found in lines {occurrence_lines}. "
                f"Use require_unique=False to replace all instances."
            )
        
        if not occurrence_lines:
            return False, []
            
        # Perform replacement
        new_content = original_content.replace(old_str, new_str)
        
        # Write atomically
        _atomic_write(path, new_content)
        
        return True, occurrence_lines
    except Exception as e:
        if isinstance(e, FileIOError):
            raise
        raise FileIOError(f"Error replacing string in file {file_path}: {str(e)}")


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
        FileIOError: If the file can't be accessed or modified
    """
    try:
        # Convert to Path object
        path = expand_path(file_path)
        
        # Validate path
        validate_path(path)
        
        # Save the original content (for undo)
        with open(path, "r", encoding="utf-8") as file:
            original_content = file.read()
            _save_to_history(path, original_content)
        
        # Read the file
        with open(path, "r", encoding="utf-8") as file:
            lines = file.readlines()
        
        # Handle empty file case
        if not lines:
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
        
        if start_idx >= len(lines):
            start_idx = len(lines) - 1
        
        if end_idx >= len(lines):
            end_idx = len(lines) - 1
        
        if start_idx > end_idx:
            # Invalid range, do nothing
            return True
        
        # Remove the specified lines
        new_lines = lines[:start_idx] + lines[end_idx + 1:]
        new_content = ''.join(new_lines)
        
        # Write atomically
        _atomic_write(path, new_content)
        
        return True
    except Exception as e:
        if isinstance(e, FileIOError):
            raise
        raise FileIOError(f"Error removing lines from file {file_path}: {str(e)}")


async def undo_edit(file_path: str) -> bool:
    """
    Undo the last edit to a file.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        bool: True if the undo was successful
        
    Raises:
        FileIOError: If there's no edit history or the file can't be accessed
    """
    try:
        # Convert to Path object
        path = expand_path(file_path)
        path_str = str(path)
        
        # Check if we have history for this file
        if path_str not in _file_history or not _file_history[path_str]:
            raise FileIOError(f"No edit history found for {file_path}")
        
        # Get the previous version
        previous_content = _file_history[path_str].pop()
        
        # Write it back to the file
        _atomic_write(path, previous_content)
        
        return True
    except Exception as e:
        if isinstance(e, FileIOError):
            raise
        raise FileIOError(f"Error undoing edit to file {file_path}: {str(e)}")


async def make_backup(file_path: str) -> str:
    """
    Create a backup of a file.
    
    Args:
        file_path (str): Path to the file to back up
        
    Returns:
        str: Path to the backup file
        
    Raises:
        FileIOError: If the file can't be backed up
    """
    try:
        # Convert to Path object
        path = expand_path(file_path)
        
        # Validate path
        validate_path(path)
        
        # Create timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create backup path
        backup_path = path.with_name(f"{path.name}.{timestamp}.bak")
        
        # Copy the file
        shutil.copy2(path, backup_path)
        
        return str(backup_path)
    except Exception as e:
        if isinstance(e, FileIOError):
            raise
        raise FileIOError(f"Error creating backup of file {file_path}: {str(e)}") 