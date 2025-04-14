"""
基础工具服务（Basic Tool Service）for the ChatToolGen system.

本模块提供ChatToolGen系统所需的基础工具功能，包括：
- 文件读写操作
- 目录操作
- 工具路径生成

这些工具通过MCP（Model-Code-Protocol）服务提供给其他组件使用。
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import mcp
from mcp.server.fastmcp import FastMCP

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

# 初始化MCP服务器
mcp = FastMCP("basic tools")

@mcp.tool()
def read_file(file_path: str) -> str:
    """读取文件内容并返回其文本内容。
    
    Args:
        file_path: 要读取的文件的完整路径
        
    Returns:
        str: 文件的文本内容
        
    Raises:
        FileNotFoundError: 当指定的文件不存在时
        IOError: 当读取文件时发生IO错误
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

@mcp.tool()
def write_file(file_path: str, content: str) -> bool:
    """将文本内容写入指定文件，如果文件所在目录不存在则自动创建。
    
    此工具也可作为save_file使用。
    
    Args:
        file_path: 要写入的文件的完整路径
        content: 要写入文件的文本内容
        
    Returns:
        bool: 操作是否成功完成，成功返回True，失败返回False
        
    Raises:
        无显式抛出异常，但会捕获并记录所有异常
    """
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        return True
    except Exception as e:
        print(f"Error writing to file: {str(e)}")
        return False

# @mcp.tool()
# def extract_summary(text: str, max_length: int = 200) -> str:
#     """从文本中提取摘要，默认最大长度为200字符。
    
#     摘要提取方法为选择文本的第一段落，如超过最大长度则截断并添加省略号。
    
#     Args:
#         text: 要进行摘要的原始文本
#         max_length: 摘要的最大字符数，默认为200
        
#     Returns:
#         str: 提取的文本摘要
#     """
#     # 简单摘要提取 - 首段或截断
#     paragraphs = text.split('\n\n')
#     if paragraphs:
#         summary = paragraphs[0].strip()
#         if len(summary) > max_length:
#             summary = summary[:max_length - 3] + '...'
#         return summary
#     return ''

# @mcp.tool()
# def load_json(file_path: str) -> Dict[str, Any]:
#     """从文件加载JSON数据并返回为Python字典或列表。
    
#     Args:
#         file_path: JSON文件的完整路径
        
#     Returns:
#         Dict[str, Any]: 包含JSON数据的Python字典
        
#     Raises:
#         FileNotFoundError: 当指定的文件不存在时
#         json.JSONDecodeError: 当JSON格式无效时
#     """
#     with open(file_path, 'r', encoding='utf-8') as file:
#         return json.load(file)

# @mcp.tool()
# def save_json(file_path: str, data: Union[Dict[str, Any], List[Any]]) -> bool:
#     """将Python字典或列表保存为JSON文件。
    
#     如果目标目录不存在，会自动创建。输出的JSON将格式化为带缩进的形式。
    
#     Args:
#         file_path: 保存JSON的文件完整路径
#         data: 要保存的Python字典或列表数据
        
#     Returns:
#         bool: 操作是否成功完成，成功返回True，失败返回False
        
#     Raises:
#         无显式抛出异常，但会捕获并记录所有异常
#     """
#     try:
#         directory = os.path.dirname(file_path)
#         if directory and not os.path.exists(directory):
#             os.makedirs(directory)
            
#         with open(file_path, 'w', encoding='utf-8') as file:
#             json.dump(data, file, indent=2)
        
#         return True
#     except Exception as e:
#         print(f"Error saving JSON: {str(e)}")
#         return False

@mcp.tool()
def create_tool_file_path(tool_name: str) -> str:
    """根据工具名称生成标准化的工具文件路径。
    
    会将工具名称转换为小写并将空格替换为下划线，以符合Python文件命名规范。
    
    Args:
        tool_name: 工具的名称，可以包含空格和大小写
        
    Returns:
        str: 生成的工具文件标准路径，格式为"tools/{sanitized_name}.py"
    """
    # 替换空格为下划线并确保小写
    sanitized_name = tool_name.lower().replace(' ', '_')
    return f"tools/{sanitized_name}.py"

@mcp.tool()
def list_directory(directory_path: str = ".") -> List[str]:
    """列出指定目录中的所有文件和文件夹。
    
    Args:
        directory_path: 要列出内容的目录路径，默认为当前目录(".")
        
    Returns:
        List[str]: 包含目录中所有文件和文件夹名称的列表
        
    Raises:
        无显式抛出异常，但会捕获并记录所有异常，失败时返回空列表
    """
    try:
        return os.listdir(directory_path)
    except Exception as e:
        print(f"Error listing directory: {str(e)}")
        return []

@mcp.tool()
def create_directory(directory_path: str) -> bool:
    """递归创建目录结构，支持创建多级目录。
    
    如果目录已存在，则不会报错而是正常返回成功。
    
    Args:
        directory_path: 要创建的目录完整路径
        
    Returns:
        bool: 操作是否成功完成，成功返回True，失败返回False
        
    Raises:
        无显式抛出异常，但会捕获并记录所有异常
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory: {str(e)}")
        return False

if __name__ == "__main__":
    # 启动MCP服务器
    mcp.run(transport='stdio') 
    