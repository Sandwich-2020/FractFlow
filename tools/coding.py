import os
import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("code_executor")

@mcp.tool()
async def write_file(path: str, content: str) -> str:
    """
    Writes content to a file at the specified path.
    
    Args:
        path (str): The file path where the content will be written. If the file already exists, 
                   it will be overwritten.
        content (str): The text content to write to the file.
        
    Returns:
        str: A confirmation message indicating the file has been written.
        
    Example:
        write_file("example.txt", "Hello World!")
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Written to {path}"

@mcp.tool()
async def read_file(path: str) -> str:
    """
    Reads and returns the content of a file at the specified path.
    
    Args:
        path (str): The path of the file to read.
        
    Returns:
        str: The content of the file as a string or an error message if the file doesn't exist.
        
    Example:
        read_file("example.txt")
    """
    if not os.path.exists(path):
        return "File does not exist"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@mcp.tool()
async def run_file(path: str) -> str:
    """
    Executes a Python file and returns its output.
    
    Args:
        path (str): The path to the Python file to execute.
        
    Returns:
        str: The combined stdout and stderr output from the execution, or an error message if
             the file doesn't exist or execution times out after 10 seconds.
        
    Example:
        run_file("script.py")
    """
    if not os.path.exists(path):
        return "File does not exist"
    try:
        result = subprocess.run(
            ["python", path],
            capture_output=True,
            text=True,
            timeout=10
        )
        return f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Execution timed out"

@mcp.tool()
async def make_dir(path: str, exist_ok: bool = True) -> str:
    """
    Creates a directory at the specified path.
    
    Args:
        path (str): The path where the directory will be created.
        exist_ok (bool, optional): If True, don't raise an error if the directory already exists.
                                  Defaults to True.
        
    Returns:
        str: A confirmation message indicating the directory has been created or a message
             indicating it already exists.
        
    Example:
        make_dir("./projects/new_project")
    """
    try:
        os.makedirs(path, exist_ok=exist_ok)
        return f"Directory created at {path}"
    except FileExistsError:
        return f"Directory already exists at {path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"

# @mcp.tool()
# async def delete_file(path: str) -> str:
#     """
#     Deletes a file at the specified path.
#     
#     Args:
#         path (str): The path of the file to delete.
#         
#     Returns:
#         str: A confirmation message indicating the file has been deleted or an error message
#              if the file doesn't exist.
#         
#     Example:
#         delete_file("example.txt")
#     """
#     if os.path.exists(path):
#         os.remove(path)
#         return f"Deleted {path}"
#     else:
#         return "File does not exist"

@mcp.tool()
async def list_dir(path: str) -> list[str]:
    """
    Lists the contents of a directory.
    
    Args:
        path (str): The path of the directory to list.
        
    Returns:
        list[str]: A list of filenames and directory names contained in the specified directory.
                  Returns an empty list if the path is not a directory.
        
    Example:
        list_dir("./projects")
    """
    if not os.path.isdir(path):
        return []
    return os.listdir(path)

@mcp.tool()
async def diff_files(path1: str, path2: str) -> str:
    """
    Compares two files and returns a unified diff of their contents.
    
    Args:
        path1 (str): The path to the first file for comparison.
        path2 (str): The path to the second file for comparison.
        
    Returns:
        str: A unified diff showing the differences between the two files, or an error message
             if one or both files don't exist.
        
    Example:
        diff_files("file1.txt", "file2.txt")
    """
    if not os.path.exists(path1) or not os.path.exists(path2):
        return "One or both files do not exist"
    with open(path1, "r", encoding="utf-8") as f1, open(path2, "r", encoding="utf-8") as f2:
        lines1 = f1.readlines()
        lines2 = f2.readlines()
    import difflib
    diff = difflib.unified_diff(lines1, lines2, fromfile=path1, tofile=path2)
    return ''.join(diff)

if __name__ == "__main__":
    mcp.run(transport="stdio")
