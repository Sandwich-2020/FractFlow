from mcp.server.fastmcp import FastMCP
import os
import sys
from typing import Union, List, Tuple

# # 添加当前目录到Python路径，解决相对导入问题
# current_dir = os.path.dirname(os.path.abspath(__file__))
# if current_dir not in sys.path:
#     sys.path.append(current_dir)

from file_operations import (
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

# Initialize MCP server
mcp = FastMCP("file_io_tool")

@mcp.tool()
async def check_if_file_exists(file_path: str) -> dict:
    """
    Determines whether a file exists at the specified path.
    
    Parameters:
        file_path: str - Absolute or relative path to the file to check
    
    Notes:
        - Returns success even for empty files
        - Does not verify read/write permissions
        - Both absolute and relative paths are supported
    
    Returns:
        dict with keys:
        - exists: bool - True if file exists, False otherwise
        - path: str - Normalized absolute path to the file
        - message: str - Present only when file doesn't exist
        - error: str - Present only when an error occurs
    
    Examples:
        "Check if config.json exists" → check_if_file_exists(file_path="config.json")
        "Does ./data/users.csv exist?" → check_if_file_exists(file_path="./data/users.csv")
    """
    return check_file_exists(file_path)

@mcp.tool()
async def get_total_line_count(file_path: str) -> dict:
    """
    Counts the total number of lines in a text file.
    
    Parameters:
        file_path: str - Absolute or relative path to the file
    
    Notes:
        - Returns 0 for empty files
        - Fails if file doesn't exist
        - Counts all lines including empty ones
        - Performance may degrade for very large files (>100MB)
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded, False otherwise
        - line_count: int - Number of lines in file (only if success=True)
        - path: str - Normalized absolute path to the file
        - error: str - Error type if operation failed
        - message: str - Detailed error message if operation failed
    
    Examples:
        "How many lines are in log.txt?" → get_total_line_count(file_path="log.txt")
        "Count lines in ./src/main.py" → get_total_line_count(file_path="./src/main.py")
    """
    return get_file_line_count(file_path)

@mcp.tool()
async def read_lines(file_path: str, start_line: int = 1, end_line: int = None) -> dict:
    """
    Reads specific line range from a text file.
    
    Parameters:
        file_path: str - Absolute or relative path to the file
        start_line: int - First line to read (1-indexed, default=1)
        end_line: int - Last line to read (1-indexed, inclusive, default=end of file)
    
    Notes:
        - Line numbers are 1-indexed (first line is 1, not 0)
        - If end_line exceeds file length, reads until end of file
        - Returns error if start_line < 1 or start_line > file length
        - Returns empty content for empty files
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded, False otherwise
        - content: str - File content from specified range (only if success=True)
        - lines: list - List of line strings (only if success=True)
        - start_line: int - Actual starting line read
        - end_line: int - Actual ending line read
        - line_count: int - Total number of lines in file
        - path: str - Normalized absolute path to the file
        - error: str - Error type if operation failed
        - message: str - Success/error message
    
    Examples:
        "Read file data.txt" → read_lines(file_path="data.txt")
        "Show lines 10-20 from log.txt" → read_lines(file_path="log.txt", start_line=10, end_line=20)
        "Read first 5 lines of config.ini" → read_lines(file_path="config.ini", end_line=5)
    """
    return read_file_range(file_path, start_line, end_line)

@mcp.tool()
async def read_file_in_chunks(file_path: str, chunk_size: int, overlap: int = 0, chunk_index: int = None) -> dict:
    """
    Divides file into chunks for processing large files, with optional overlap between chunks.
    
    Parameters:
        file_path: str - Absolute or relative path to the file
        chunk_size: int - Number of lines per chunk
        overlap: int - Number of overlapping lines between chunks (default=0)
        chunk_index: int - Specific chunk to retrieve (0-indexed, default=None)
    
    Notes:
        - When chunk_index is None, returns metadata about all chunks without content
        - When chunk_index is specified, returns content of only that chunk
        - chunk_index is 0-indexed (first chunk is 0)
        - overlap must be less than chunk_size
        - For large files, first get metadata (without chunk_index), then request specific chunks
    
    Returns:
        If chunk_index is None:
            dict with keys:
            - success: bool - True if operation succeeded, False otherwise
            - chunks: list - List of dicts with chunk metadata (index, start_line, end_line)
            - chunk_count: int - Total number of chunks
            - line_count: int - Total number of lines in file
            - path: str - Normalized absolute path to the file
            - message: str - Success/error message
        
        If chunk_index is specified:
            dict with keys:
            - success: bool - True if operation succeeded, False otherwise
            - content: str - Content of the specified chunk
            - lines: list - List of line strings in the chunk
            - chunk_index: int - Index of the retrieved chunk
            - total_chunks: int - Total number of chunks
            - start_line: int - Starting line number of chunk
            - end_line: int - Ending line number of chunk
            - line_count: int - Total number of lines in file
            - path: str - Normalized absolute path to the file
            - error: str - Error type if operation failed
            - message: str - Success/error message
    
    Examples:
        "Get chunk info for large_log.txt with 500-line chunks" → read_file_in_chunks(file_path="large_log.txt", chunk_size=500)
        "Read chunk 2 from data.csv with 100-line chunks" → read_file_in_chunks(file_path="data.csv", chunk_size=100, chunk_index=2)
        "Read chunk 1 with 30 lines of overlap" → read_file_in_chunks(file_path="file.txt", chunk_size=200, overlap=30, chunk_index=1)
    """
    return read_file_chunks(file_path, chunk_size, overlap, chunk_index)

@mcp.tool()
async def read_with_line_numbers(file_path: str, start_line: int = 1, end_line: int = None) -> dict:
    """
    Reads file content with line numbers prefixed to each line (similar to 'cat -n').
    
    Parameters:
        file_path: str - Absolute or relative path to the file
        start_line: int - First line to read (1-indexed, default=1)
        end_line: int - Last line to read (1-indexed, inclusive, default=end of file)
    
    Notes:
        - Line numbers are 1-indexed (first line is 1, not 0)
        - Line numbers are displayed with consistent width
        - Format is "{line_number:4d} | {line_content}"
        - Otherwise behaves identically to read_lines()
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded, False otherwise
        - content: str - File content with line numbers
        - lines: list - List of line strings without line numbers
        - start_line: int - Actual starting line read
        - end_line: int - Actual ending line read
        - line_count: int - Total number of lines in file
        - path: str - Normalized absolute path to the file
        - error: str - Error type if operation failed
        - message: str - Success/error message
    
    Examples:
        "Show file.py with line numbers" → read_with_line_numbers(file_path="file.py")
        "Display lines 50-100 from log.txt with line numbers" → read_with_line_numbers(file_path="log.txt", start_line=50, end_line=100)
    """
    return read_file_with_line_numbers(file_path, start_line, end_line)

@mcp.tool()
async def create_file(file_path: str, content: str) -> dict:
    """
    Creates a new file or overwrites an existing file with specified content.
    
    Parameters:
        file_path: str - Absolute or relative path to the file
        content: str - Text content to write to the file
    
    Notes:
        - Creates parent directories if they don't exist
        - Overwrites file if it already exists without confirmation
        - Preserves the content string exactly, including newlines and whitespace
        - For appending or inserting instead of overwriting, use append_content or insert_content_at_line
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded, False otherwise
        - path: str - Normalized absolute path to the file
        - message: str - Success/error message
        - error: str - Error type if operation failed
    
    Examples:
        "Create file notes.txt with content 'Meeting notes'" → create_file(file_path="notes.txt", content="Meeting notes")
        "Write 'Hello World' to ./output/greeting.txt" → create_file(file_path="./output/greeting.txt", content="Hello World")
    """
    return create_or_write_file(file_path, content)

@mcp.tool()
async def append_content(file_path: str, content: str) -> dict:
    """
    Appends content to the end of a file, creating the file if it doesn't exist.
    
    Parameters:
        file_path: str - Absolute or relative path to the file
        content: str - Text content to append to the file
    
    Notes:
        - Creates parent directories if they don't exist
        - Creates a new file if it doesn't exist
        - Preserves the content string exactly, including newlines and whitespace
        - Does not automatically add newlines between existing content and appended content
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded, False otherwise
        - path: str - Normalized absolute path to the file
        - message: str - Success/error message
        - error: str - Error type if operation failed
    
    Examples:
        "Append 'New log entry' to log.txt" → append_content(file_path="log.txt", content="New log entry")
        "Add '# TODO: Fix this' to script.py" → append_content(file_path="script.py", content="# TODO: Fix this")
    """
    return append_to_file(file_path, content)

@mcp.tool()
async def insert_content_at_line(file_path: str, line_number: int, content: str) -> dict:
    """
    Inserts content at a specific line number in a file, shifting existing content down.
    
    Parameters:
        file_path: str - Absolute or relative path to the file
        line_number: int - Line position to insert at (1-indexed)
        content: str - Text content to insert
    
    Notes:
        - Creates the file if it doesn't exist
        - Creates parent directories if they don't exist
        - Line number is 1-indexed (first line is 1, not 0)
        - If line_number > file length, appends to end of file
        - If line_number > file length + 1, adds empty lines to reach position
        - Does not automatically add newlines; add explicitly if needed
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded, False otherwise
        - path: str - Normalized absolute path to the file
        - line_count: int - New total line count after insertion
        - message: str - Success/error message
        - error: str - Error type if operation failed
    
    Examples:
        "Insert 'import os' at line 1 of script.py" → insert_content_at_line(file_path="script.py", line_number=1, content="import os")
        "Add header at the top of document.md" → insert_content_at_line(file_path="document.md", line_number=1, content="# Document Title")
    """
    return insert_at_line(file_path, line_number, content)

@mcp.tool()
async def delete_line_at(file_path: str, line_number: Union[int, List[int], Tuple[int, ...]]) -> dict:
    """
    Deletes one or more specific lines from a file.
    
    Parameters:
        file_path: str - Absolute or relative path to the file
        line_number: int, list, or tuple - Line number(s) to delete (1-indexed)
                     Can be a single integer, a list of integers, or a tuple of integers
    
    Notes:
        - Line numbers are 1-indexed (first line is 1, not 0)
        - Returns error if file doesn't exist
        - Returns error if any line number is invalid (<1 or >file length)
        - When deleting multiple lines, they're deleted from highest to lowest
          to avoid line number shifting problems
        - Shifts all following lines up after deletion
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded, False otherwise
        - path: str - Normalized absolute path to the file
        - deleted_lines: list - Content of the deleted lines
        - new_line_count: int - Updated line count after deletion
        - message: str - Success/error message
        - error: str - Error type if operation failed
    
    Examples:
        "Delete line 10 from config.txt" → delete_line_at(file_path="config.txt", line_number=10)
        "Remove the first line of log.txt" → delete_line_at(file_path="log.txt", line_number=1)
        "Delete lines 5, 10, and 15" → delete_line_at(file_path="data.txt", line_number=[5, 10, 15])
    """
    try:
        path = normalize_path(file_path)
        
        # Check if file exists
        if not os.path.isfile(path):
            return {
                "success": False,
                "error": "File not found",
                "message": f"File does not exist: {path}. Please check the file path."
            }
            
        # Read existing content
        with open(path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        line_count = len(lines)
        
        # Handle different types of line_number
        if isinstance(line_number, int):
            # Single line deletion
            if line_number < 1 or line_number > line_count:
                return {
                    "success": False,
                    "error": "Invalid line number",
                    "message": f"Line number ({line_number}) is out of range (1-{line_count})."
                }
                
            # Delete the single line
            deleted_line = lines.pop(line_number - 1)
            
            # Write back to file
            with open(path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
                
            return {
                "success": True,
                "path": path,
                "deleted_lines": [deleted_line],
                "new_line_count": len(lines),
                "message": f"Line {line_number} deleted from {path}"
            }
        else:
            # Multiple line deletion
            if not line_number:
                return {
                    "success": False,
                    "error": "Invalid line numbers",
                    "message": "No line numbers provided for deletion."
                }
                
            # Convert to list if it's a tuple
            line_numbers = list(line_number) if isinstance(line_number, tuple) else line_number
            
            # Validate all line numbers
            for ln in line_numbers:
                if not isinstance(ln, int) or ln < 1 or ln > line_count:
                    return {
                        "success": False,
                        "error": "Invalid line number",
                        "message": f"Line number ({ln}) is invalid or out of range (1-{line_count})."
                    }
            
            # Sort line numbers in descending order to avoid index shifting issues
            line_numbers.sort(reverse=True)
            
            # Delete lines one by one from highest to lowest
            deleted_lines = []
            for ln in line_numbers:
                deleted_lines.append(lines.pop(ln - 1))
            
            # Reverse the deleted lines list so it matches the original order
            deleted_lines.reverse()
            
            # Write back to file
            with open(path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
                
            return {
                "success": True,
                "path": path,
                "deleted_lines": deleted_lines,
                "new_line_count": len(lines),
                "message": f"Lines {', '.join(map(str, sorted(line_numbers)))} deleted from {path}"
            }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "message": f"Cannot modify file due to permission issues: {path}. Please check file permissions."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error deleting lines: {str(e)}"
        }

if __name__ == "__main__":
    # Run the MCP server
    mcp.run(transport='stdio') 