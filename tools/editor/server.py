"""
OpenHands ACI Tool Server Module

This module provides a FastMCP server that exposes OpenHands ACI (Auto Code Intelligence) 
operations as tools. It wraps the core OpenHands ACI functionality in a server interface 
that can be used by the EnvisionCore framework.

The server provides tools for:
- Code editing and file operations (view, create, modify, etc.)
- Code linting and static analysis
- Shell command execution
- File caching for performance optimization

Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-04-27
License: MIT License
"""

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
import os
from typing import Optional, List, Dict, Any, Union

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent))

# Import the actual modules available in OpenHands ACI
from openhands_aci.editor import file_editor, Command, OHEditor
from openhands_aci.editor.file_cache import FileCache
from openhands_aci.linter import DefaultLinter
from openhands_aci.utils.shell import run_shell_cmd

# Initialize MCP server
mcp = FastMCP("openhands_aci_tool")

@mcp.tool()
async def edit_code(command: str, path: str, file_text: Optional[str] = None, 
                   view_range: Optional[List[int]] = None, old_str: Optional[str] = None, 
                   new_str: Optional[str] = None, insert_line: Optional[int] = None,
                   enable_linting: bool = False):
    """
    Edit code using one of the supported commands: view, create, str_replace, insert, undo_edit.
    
    Parameters:
        command (str): The editor command to execute. Must be one of:
            - 'view': View file content (requires path)
            - 'create': Create a new file (requires path, file_text)
            - 'str_replace': Replace text in a file (requires path, old_str, new_str)
            - 'insert': Insert text at a specific line (requires path, insert_line, new_str)
            - 'undo_edit': Revert last edit (requires path)
            
        path (str): Absolute path to the file to edit
        
        file_text (str, optional): Content for the file when creating or for context when editing
        
        view_range (List[int], optional): Range of lines to view as [start_line, end_line].
            Line numbers start at 1. Only used with 'view' command.
            
        old_str (str, optional): String to replace when using 'str_replace' command
        
        new_str (str, optional): New string to use when replacing ('str_replace') or inserting ('insert')
        
        insert_line (int, optional): Line number for insertion with 'insert' command.
            Line numbers start at 0, where:
            - 0: Insert before the first line
            - n: Insert after line n (before line n+1)
            
        enable_linting (bool, optional): Whether to run linting on changes (default: False)
        
    Returns:
        str: A string containing the result of the operation in the following format:
             <oh_aci_output_{marker_id}>
             {JSON object with operation results}
             </oh_aci_output_{marker_id}>
             
             The JSON object typically includes:
             - path (str): Path to the edited file
             - new_content (str): New content of the file after edits (not in 'view' command)
             - old_content (str): Previous content before edits (returned as 'old_content')
             - prev_exist (bool): Whether the file existed before the operation
             - output (str): Human-readable message describing the operation
             - error (str, optional): Error message if operation failed
             - formatted_output_and_error (str): Formatted display output
            
    Raises:
        ValueError: If the command is invalid or required parameters are missing
        
    Notes:
        - For 'str_replace', the old_str must appear exactly once in the file
        - For 'insert', line numbering starts at 0 (insert before first line) 
          and can go up to the number of lines in the file (append to end)
        - For binary files or files larger than the configured size limit, operations will fail
    """
    # Convert command string to Command type
    if command not in ["view", "create", "str_replace", "insert", "undo_edit"]:
        raise ValueError(f"Invalid command: {command}. Must be one of: view, create, str_replace, insert, undo_edit")
    
    cmd = command  # Type checking will happen inside file_editor
    
    result = file_editor(
        command=cmd,
        path=path,
        file_text=file_text,
        view_range=view_range,
        old_str=old_str,
        new_str=new_str,
        insert_line=insert_line,
        enable_linting=enable_linting,
    )
    return result

@mcp.tool()
async def run_linter(code: str, language: str):
    """
    Run the linter on the provided code to identify potential issues and errors.
    
    Parameters:
        code (str): Source code to analyze
        language (str): Programming language of the code (e.g., 'python', 'javascript')
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - issues (List[Dict]): List of linting issues found, each with:
                - line (int): Line number where the issue was found
                - column (int): Column number where the issue was found
                - message (str): Description of the issue
                - severity (str): Severity level (e.g., 'error', 'warning')
                - rule (str): The linting rule that was violated
            - success (bool): Whether the linting operation completed successfully
            - error (str, optional): Error message if linting failed
            
    Raises:
        ValueError: If the language is not supported or the code cannot be parsed
    """
    linter = DefaultLinter()
    try:
        with open("temp_lint_file.py", "w") as f:
            f.write(code)
        
        results = linter.run("temp_lint_file.py", language)
        
        return {
            "issues": results,
            "success": True
        }
    except Exception as e:
        return {
            "issues": [],
            "success": False,
            "error": str(e)
        }
    finally:
        # Clean up temporary file
        if os.path.exists("temp_lint_file.py"):
            os.remove("temp_lint_file.py")

@mcp.tool()
async def execute_shell(cmd: str, timeout: float = 60.0):
    """
    Execute a shell command and return the result, including stdout and stderr.
    
    Parameters:
        cmd (str): Shell command to execute (runs in the server's environment)
        timeout (float, optional): Maximum time in seconds to wait for completion. Defaults to 60.0.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - returncode (int): Return code of the command (0 typically indicates success)
            - stdout (str): Standard output captured from the command
            - stderr (str): Standard error captured from the command
            - success (bool): Whether the command completed successfully (returncode == 0)
            
    Raises:
        TimeoutError: If the command execution exceeds the specified timeout
        
    Notes:
        - Commands are executed in the server's environment, not the client's
        - For security reasons, certain commands may be restricted
        - Large output may be truncated
    """
    try:
        returncode, stdout, stderr = run_shell_cmd(cmd, timeout=timeout)
        return {
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "success": returncode == 0
        }
    except TimeoutError as e:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }

@mcp.tool()
async def cache_file(path: str, content: Optional[str] = None, directory: str = "/tmp/filecache"):
    """
    Cache a file for faster access or store content without writing to disk.
    
    Parameters:
        path (str): Path to identify the file in the cache (used as the cache key)
        content (str, optional): Content to store. If None, tries to read from the path
        directory (str, optional): Directory to store the cache. Defaults to "/tmp/filecache"
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - path (str): Path used as the cache key
            - success (bool): Whether the caching was successful
            - error (str, optional): Error message if caching failed
            
    Raises:
        FileNotFoundError: If content is None and the file doesn't exist
    """
    file_cache = FileCache(directory=directory)
    
    try:
        if content is None:
            # Read and cache the content from the file
            with open(path, 'r') as f:
                content = f.read()
        
        file_cache.set(path, content)
        
        return {
            "path": path,
            "success": True
        }
    except Exception as e:
        return {
            "path": path,
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def get_cached_file(path: str, directory: str = "/tmp/filecache"):
    """
    Retrieve a file from the cache by its path key.
    
    Parameters:
        path (str): Path used as the cache key when the file was cached
        directory (str, optional): Directory where the cache is stored. Defaults to "/tmp/filecache"
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - path (str): Path used as the cache key
            - content (str): The cached content, if found
            - success (bool): Whether the retrieval was successful
            - error (str, optional): Error message if retrieval failed
            
    Raises:
        KeyError: If the path is not found in the cache
    """
    file_cache = FileCache(directory=directory)
    
    try:
        content = file_cache.get(path)
        return {
            "path": path,
            "content": content,
            "success": True
        }
    except KeyError:
        return {
            "path": path,
            "success": False,
            "error": f"Path '{path}' not found in cache"
        }

if __name__ == "__main__":
    mcp.run(transport='stdio')
