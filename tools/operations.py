"""
Filesystem operations tool.

Provides tools for interacting with the filesystem, including listing directories,
creating, copying, and deleting files and directories.
"""

from typing import List, Dict, Optional, Any
import os
import shutil
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("filesystem")

@mcp.tool()
async def list_directory(path: str) -> str:
    """List contents of a directory.
    
    Args:
        path: Directory path to list
    """
    try:
        path_obj = Path(path).resolve()
        if not path_obj.exists():
            return f"Path does not exist: {path}"
        
        contents = []
        for item in path_obj.iterdir():
            item_type = "📁" if item.is_dir() else "📄"
            size = ""
            if item.is_file():
                size = f"({human_readable_size(item.stat().st_size)})"
            contents.append(f"{item_type} {item.name} {size}")
        
        return "\n".join(contents) if contents else "Directory is empty"
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@mcp.tool()
async def create_directory(path: str) -> str:
    """Create a new directory.
    
    Args:
        path: Path where to create the directory
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return f"Directory created successfully: {path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"

@mcp.tool()
async def delete_item(path: str, recursive: bool = False) -> str:
    """Delete a file or directory.
    
    Args:
        path: Path to delete
        recursive: If True, recursively delete directories
    """
    try:
        path_obj = Path(path)
        if not path_obj.exists():
            return f"Path does not exist: {path}"
            
        if path_obj.is_file():
            path_obj.unlink()
            return f"File deleted successfully: {path}"
        elif path_obj.is_dir():
            if recursive:
                shutil.rmtree(path)
                return f"Directory and its contents deleted successfully: {path}"
            else:
                path_obj.rmdir()
                return f"Empty directory deleted successfully: {path}"
    except Exception as e:
        return f"Error deleting path: {str(e)}"

@mcp.tool()
async def copy_item(source: str, destination: str) -> str:
    """Copy a file or directory.
    
    Args:
        source: Source path
        destination: Destination path
    """
    try:
        src_path = Path(source)
        dst_path = Path(destination)
        
        if not src_path.exists():
            return f"Source path does not exist: {source}"
            
        if src_path.is_file():
            shutil.copy2(src_path, dst_path)
            return f"File copied successfully: {source} -> {destination}"
        elif src_path.is_dir():
            shutil.copytree(src_path, dst_path)
            return f"Directory copied successfully: {source} -> {destination}"
    except Exception as e:
        return f"Error copying: {str(e)}"

@mcp.tool()
async def move_files_by_type(source_dir: str, destination_dir: str, file_extension: str) -> str:
    """Move files of a specific type from source directory to destination directory.
    
    Args:
        source_dir: Source directory to search for files
        destination_dir: Destination directory to move files to
        file_extension: File extension to filter by (e.g., '.txt', '.pdf')
    """
    try:
        source_path = Path(source_dir)
        dest_path = Path(destination_dir)
        
        if not source_path.exists() or not source_path.is_dir():
            return f"Source directory does not exist: {source_dir}"
            
        # Create destination directory if it doesn't exist
        dest_path.mkdir(parents=True, exist_ok=True)
        
        # Make sure file_extension starts with a dot
        if not file_extension.startswith('.'):
            file_extension = '.' + file_extension
            
        # Find and move files
        moved_count = 0
        for item in source_path.rglob(f"*{file_extension}"):
            if item.is_file():
                # Create the destination path
                dest_file = dest_path / item.name
                
                # Move the file
                shutil.move(str(item), str(dest_file))
                moved_count += 1
                
        if moved_count > 0:
            return f"Moved {moved_count} files with extension '{file_extension}' to {destination_dir}"
        else:
            return f"No files with extension '{file_extension}' found in {source_dir}"
            
    except Exception as e:
        return f"Error moving files: {str(e)}"

def human_readable_size(size_in_bytes: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.1f}{unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.1f}PB"

# 为测试提供的函数
def list_directory_contents(path: str) -> Dict[str, Any]:
    """
    列出目录内容并返回结构化数据。
    
    Args:
        path: 要列出内容的目录路径
        
    Returns:
        包含目录和文件列表的字典
    """
    result = {"directories": [], "files": []}
    
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                result["directories"].append(item)
            else:
                result["files"].append(item)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_file(file_path: str, content: str) -> Dict[str, Any]:
    """
    创建文件并写入内容。
    
    Args:
        file_path: 要创建的文件路径
        content: 要写入的内容
        
    Returns:
        操作结果的字典
    """
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return {"success": True, "path": file_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_file(file_path: str) -> Dict[str, Any]:
    """
    删除文件。
    
    Args:
        file_path: 要删除的文件路径
        
    Returns:
        操作结果的字典
    """
    try:
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
        os.remove(file_path)
        return {"success": True, "path": file_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

def copy_file(source_path: str, target_path: str) -> Dict[str, Any]:
    """
    复制文件。
    
    Args:
        source_path: 源文件路径
        target_path: 目标文件路径
        
    Returns:
        操作结果的字典
    """
    try:
        if not os.path.exists(source_path):
            return {"success": False, "error": f"Source file not found: {source_path}"}
        shutil.copy2(source_path, target_path)
        return {"success": True, "source": source_path, "target": target_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

def move_file(source_path: str, target_path: str) -> Dict[str, Any]:
    """
    移动文件。
    
    Args:
        source_path: 源文件路径
        target_path: 目标文件路径
        
    Returns:
        操作结果的字典
    """
    try:
        if not os.path.exists(source_path):
            return {"success": False, "error": f"Source file not found: {source_path}"}
        shutil.move(source_path, target_path)
        return {"success": True, "source": source_path, "target": target_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

def format_size(size_in_bytes: int) -> str:
    """
    格式化文件大小为人类可读格式。
    
    Args:
        size_in_bytes: 字节为单位的文件大小
        
    Returns:
        格式化后的大小字符串
    """
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes/1024:.1f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes/(1024*1024):.1f} MB"
    else:
        return f"{size_in_bytes/(1024*1024*1024):.1f} GB"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 