import os
import pathlib
from typing import List, Dict, Union, Optional, Tuple
import re


def normalize_path(file_path: str) -> str:
    """
    Normalize a file path to prevent path traversal attacks.
    
    Args:
        file_path: The file path to normalize
        
    Returns:
        Normalized file path
    """
    # Convert to absolute path if not already
    path = os.path.abspath(os.path.expanduser(file_path))
    return path


def ensure_parent_directory(file_path: str) -> None:
    """
    Ensure that the parent directory of a file exists.
    
    Args:
        file_path: The file path
    """
    parent_dir = os.path.dirname(file_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir)


def check_file_exists(file_path: str) -> Dict[str, Union[bool, str]]:
    """
    Check if a file exists at the specified path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with 'exists' status and additional info
    """
    try:
        path = normalize_path(file_path)
        exists = os.path.isfile(path)
        
        result = {
            "exists": exists,
            "path": path
        }
        
        if not exists:
            result["message"] = f"File does not exist: {path}"
        
        return result
    except Exception as e:
        return {
            "exists": False,
            "error": str(e),
            "message": f"Error checking file existence: {str(e)}"
        }


def get_file_line_count(file_path: str) -> Dict[str, Union[int, str, bool]]:
    """
    Get the total number of lines in a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with 'line_count' if successful, or error information
    """
    try:
        path = normalize_path(file_path)
        
        # Check if file exists
        if not os.path.isfile(path):
            return {
                "success": False,
                "error": "File not found",
                "message": f"File does not exist: {path}. Please check the file path or create the file first."
            }
        
        # Count lines
        with open(path, 'r', encoding='utf-8') as file:
            line_count = sum(1 for _ in file)
        
        return {
            "success": True,
            "line_count": line_count,
            "path": path
        }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "message": f"Cannot read file due to permission issues: {path}. Please check file permissions."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error counting lines in file: {str(e)}"
        }


def read_file_range(file_path: str, start_line: int = 1, end_line: Optional[int] = None) -> Dict[str, Union[str, int, bool, List[str]]]:
    """
    Read content from a specified line range in a file.
    
    Args:
        file_path: Path to the file
        start_line: Starting line number (1-indexed)
        end_line: Ending line number (1-indexed, inclusive), if None, reads to the end
        
    Returns:
        Dictionary with file content and metadata
    """
    try:
        path = normalize_path(file_path)
        
        # Check if file exists
        if not os.path.isfile(path):
            return {
                "success": False,
                "error": "File not found",
                "message": f"File does not exist: {path}. Please check the file path or create the file first."
            }
        
        # Validate line ranges
        if start_line < 1:
            return {
                "success": False,
                "error": "Invalid start line",
                "message": f"Start line must be at least 1, got {start_line}."
            }
            
        # Get file line count
        line_count_result = get_file_line_count(path)
        if not line_count_result.get("success", False):
            return line_count_result
            
        line_count = line_count_result["line_count"]
        
        # Empty file check
        if line_count == 0:
            return {
                "success": True,
                "content": "",
                "lines": [],
                "start_line": start_line,
                "end_line": start_line,
                "line_count": 0,
                "path": path,
                "message": "File is empty"
            }
            
        # Adjust end_line if not specified or exceeds file length
        if end_line is None or end_line > line_count:
            end_line = line_count
            
        # Check if start_line is beyond file length
        if start_line > line_count:
            return {
                "success": False,
                "error": "Invalid start line",
                "message": f"Start line ({start_line}) exceeds file length ({line_count})."
            }
            
        # Read file content
        with open(path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        # Get requested lines (adjust for 0-indexed list)
        requested_lines = lines[start_line-1:end_line]
        content = ''.join(requested_lines)
        
        return {
            "success": True,
            "content": content,
            "lines": requested_lines,
            "start_line": start_line,
            "end_line": end_line,
            "line_count": line_count,
            "path": path
        }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "message": f"Cannot read file due to permission issues: {path}. Please check file permissions."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error reading file range: {str(e)}"
        }


def read_file_chunks(file_path: str, chunk_size: int, 
                    overlap: int = 0, 
                    chunk_index: Optional[int] = None) -> Dict[str, Union[str, int, bool, List[Dict]]]:
    """
    Read a file in chunks with optional overlap between chunks.
    
    Args:
        file_path: Path to the file
        chunk_size: Number of lines per chunk
        overlap: Number of overlapping lines between chunks (default: 0)
        chunk_index: Index of specific chunk to retrieve (0-indexed, optional)
        
    Returns:
        Dictionary with either metadata about all chunks or content of specific chunk
    """
    try:
        path = normalize_path(file_path)
        
        # Check if file exists
        if not os.path.isfile(path):
            return {
                "success": False,
                "error": "File not found",
                "message": f"File does not exist: {path}. Please check the file path or create the file first."
            }
            
        # Validate parameters
        if chunk_size <= 0:
            return {
                "success": False,
                "error": "Invalid chunk size",
                "message": f"Chunk size must be positive, got {chunk_size}."
            }
            
        if overlap < 0:
            return {
                "success": False,
                "error": "Invalid overlap",
                "message": f"Overlap must be non-negative, got {overlap}."
            }
            
        if overlap >= chunk_size:
            return {
                "success": False,
                "error": "Invalid overlap",
                "message": f"Overlap ({overlap}) must be less than chunk size ({chunk_size})."
            }
        
        # Get file line count
        line_count_result = get_file_line_count(path)
        if not line_count_result.get("success", False):
            return line_count_result
            
        line_count = line_count_result["line_count"]
        
        # Empty file check
        if line_count == 0:
            return {
                "success": True,
                "chunks": [],
                "chunk_count": 0,
                "line_count": 0,
                "path": path,
                "message": "File is empty"
            }
            
        # Calculate number of chunks
        if line_count <= chunk_size:
            chunk_count = 1
        else:
            # Calculate effective step size between chunks
            step = chunk_size - overlap
            chunk_count = (line_count - chunk_size) // step + 2
            
        # Generate chunk metadata
        chunks = []
        for i in range(chunk_count):
            start = i * (chunk_size - overlap) + 1  # 1-indexed
            end = min(start + chunk_size - 1, line_count)  # inclusive end
            
            chunks.append({
                "index": i,
                "start_line": start,
                "end_line": end
            })
        
        # If chunk_index is specified, return that specific chunk
        if chunk_index is not None:
            if chunk_index < 0 or chunk_index >= chunk_count:
                return {
                    "success": False,
                    "error": "Invalid chunk index",
                    "message": f"Chunk index must be between 0 and {chunk_count-1}, got {chunk_index}."
                }
                
            chunk_info = chunks[chunk_index]
            chunk_content = read_file_range(path, chunk_info["start_line"], chunk_info["end_line"])
            
            if not chunk_content.get("success", False):
                return chunk_content
                
            return {
                "success": True,
                "content": chunk_content["content"],
                "lines": chunk_content["lines"],
                "chunk_index": chunk_index,
                "total_chunks": chunk_count,
                "start_line": chunk_info["start_line"],
                "end_line": chunk_info["end_line"],
                "line_count": line_count,
                "path": path
            }
        else:
            # Return metadata about all chunks
            return {
                "success": True,
                "chunks": chunks,
                "chunk_count": chunk_count,
                "line_count": line_count,
                "path": path,
                "message": f"File contains {line_count} lines divided into {chunk_count} chunks of size {chunk_size} with overlap {overlap}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error reading file chunks: {str(e)}"
        }


def read_file_with_line_numbers(file_path: str, start_line: int = 1, 
                               end_line: Optional[int] = None) -> Dict[str, Union[str, int, bool]]:
    """
    Read file content with line numbers.
    
    Args:
        file_path: Path to the file
        start_line: Starting line number (1-indexed)
        end_line: Ending line number (1-indexed, inclusive), if None, reads to the end
        
    Returns:
        Dictionary with file content including line numbers
    """
    try:
        # First get the content without line numbers
        result = read_file_range(file_path, start_line, end_line)
        
        if not result.get("success", False):
            return result
            
        # Add line numbers to each line
        lines = result.get("lines", [])
        line_count = len(lines)
        content_with_numbers = ""
        
        for i, line in enumerate(lines):
            line_num = start_line + i
            content_with_numbers += f"{line_num:4d} | {line}"
            
            # Add newline if not present and not the last line
            if not line.endswith('\n') and i < line_count - 1:
                content_with_numbers += '\n'
                
        # Update the result with the new content
        result["content"] = content_with_numbers
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error reading file with line numbers: {str(e)}"
        }


def create_or_write_file(file_path: str, content: str) -> Dict[str, Union[bool, str]]:
    """
    Create a new file or overwrite an existing file with the given content.
    
    Args:
        file_path: Path to the file
        content: Content to write to the file
        
    Returns:
        Dictionary with operation status
    """
    try:
        path = normalize_path(file_path)
        
        # Ensure parent directory exists
        ensure_parent_directory(path)
        
        # Write content to file
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
            
        return {
            "success": True,
            "path": path,
            "message": f"File written successfully: {path}"
        }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "message": f"Cannot write to file due to permission issues: {path}. Please check file permissions."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error writing to file: {str(e)}"
        }


def append_to_file(file_path: str, content: str) -> Dict[str, Union[bool, str]]:
    """
    Append content to the end of a file. If the file doesn't exist, it will be created.
    
    Args:
        file_path: Path to the file
        content: Content to append to the file
        
    Returns:
        Dictionary with operation status
    """
    try:
        path = normalize_path(file_path)
        
        # Ensure parent directory exists
        ensure_parent_directory(path)
        
        # Append content to file
        with open(path, 'a', encoding='utf-8') as file:
            file.write(content)
            
        return {
            "success": True,
            "path": path,
            "message": f"Content appended successfully to: {path}"
        }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "message": f"Cannot append to file due to permission issues: {path}. Please check file permissions."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error appending to file: {str(e)}"
        }


def insert_at_line(file_path: str, line_number: int, content: str) -> Dict[str, Union[bool, str, int]]:
    """
    Insert content at a specified line in a file. If the file doesn't exist, it will be created.
    If line_number exceeds the file length, the content will be appended to the end.
    
    Args:
        file_path: Path to the file
        line_number: Line number to insert at (1-indexed)
        content: Content to insert
        
    Returns:
        Dictionary with operation status
    """
    try:
        path = normalize_path(file_path)
        
        # Check if line_number is valid
        if line_number < 1:
            return {
                "success": False,
                "error": "Invalid line number",
                "message": f"Line number must be at least 1, got {line_number}."
            }
            
        # Check if file exists
        file_exists = os.path.isfile(path)
        
        if not file_exists:
            # Create new file with content
            ensure_parent_directory(path)
            return create_or_write_file(path, content)
            
        # Read existing content
        with open(path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        line_count = len(lines)
        
        # Ensure content ends with newline if not empty
        if content and not content.endswith('\n'):
            content += '\n'
            
        # Handle insertion
        if line_number > line_count + 1:
            # If line number is beyond the end with a gap, add empty lines
            for _ in range(line_count + 1, line_number):
                lines.append('\n')
            lines.append(content)
        elif line_number > line_count:
            # If the line number is just past the end, simply append
            lines.append(content)
        else:
            # Insert at the specified position
            lines.insert(line_number - 1, content)
            
        # Write back to file
        with open(path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
            
        return {
            "success": True,
            "path": path,
            "line_count": len(lines),
            "message": f"Content inserted at line {line_number} in {path}"
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
            "message": f"Error inserting content at line: {str(e)}"
        }


def delete_line(file_path: str, line_number: int) -> Dict[str, Union[bool, str, int]]:
    """
    Delete a specific line from a file.
    
    Args:
        file_path: Path to the file
        line_number: Line number to delete (1-indexed)
        
    Returns:
        Dictionary with operation status
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
            
        # Check if line_number is valid
        if line_number < 1:
            return {
                "success": False,
                "error": "Invalid line number",
                "message": f"Line number must be at least 1, got {line_number}."
            }
            
        # Read existing content
        with open(path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        line_count = len(lines)
        
        # Check if line number is within range
        if line_number > line_count:
            return {
                "success": False,
                "error": "Invalid line number",
                "message": f"Line number ({line_number}) exceeds file length ({line_count})."
            }
            
        # Delete the specified line
        deleted_line = lines.pop(line_number - 1)
        
        # Write back to file
        with open(path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
            
        return {
            "success": True,
            "path": path,
            "deleted_line": deleted_line,
            "new_line_count": len(lines),
            "message": f"Line {line_number} deleted from {path}"
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
            "message": f"Error deleting line: {str(e)}"
        } 