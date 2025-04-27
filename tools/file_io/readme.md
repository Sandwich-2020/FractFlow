# File I/O Tool

A comprehensive tool for file and directory operations, designed to be used with the EnvisionCore framework.

## Features

- Read and write files (text and binary)
- List directory contents with metadata
- Delete files and directories
- Move and copy files and directories
- Check if files exist
- Get detailed file information

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Starting the Tool Server

```bash
# 1. 交互式聊天模式
python run_server.py

# 2. 单次查询模式 - 处理单个查询后自动退出
python run_server.py --user_query "读取文件 /path/to/file.txt 的内容"

# 3. 导入作为Agent工具
agent.add_tool("./tools/file_io/src/server.py")
```

#### 运行模式

1. **交互式聊天模式** - 默认模式
   - 启动后进入交互式命令行界面
   - 可以连续输入多个查询并获得响应
   - 输入 'exit'、'quit' 或 'bye' 退出

2. **单次查询模式** - 通过 `--user_query` 参数运行
   - 自动处理一个查询并显示结果
   - 处理完成后自动退出
   - 适合脚本集成和自动化任务

示例:
```bash
# 列出目录内容
python run_server.py --user_query "列出 /tmp 目录中的所有文件"

# 创建并写入文件
python run_server.py --user_query "创建文件 /tmp/test.txt 并写入 'Hello World'"

# 获取文件信息
python run_server.py --user_query "获取文件 /etc/hosts 的详细信息"
```

### API Reference

The following operations are available:

#### Get File Info

```python
async def info(file_path: str, fields: Optional[List[str]] = None)
```

Get detailed information about a file or directory.

**Parameters:**
- `file_path` (str): The absolute or relative path to the file or directory
- `fields` (Optional[List[str]]): List of specific fields to return. If not provided, returns all available information

**Returns:**
- Dict[str, Any]: A dictionary containing file metadata (filtered by requested fields):
  - name (str): The name of the file or directory
  - path (str): The full path to the file or directory
  - is_dir (bool): Whether the item is a directory
  - size (int): The size of the file in bytes (None for directories)
  - created (float): The creation timestamp
  - modified (float): The last modified timestamp
  - accessed (float): The last accessed timestamp
  - extension (str): The file extension (None for directories)
  - parent (str): The directory containing this file/directory
  - permissions (int): Unix-style permission bits
  - owner (int): User ID of the file owner
  - group (int): Group ID of the file owner

**Raises:**
- `FileNotFoundError`: If the specified file or directory does not exist

**Examples:**
```python
# Get all information
file_info = await info("/path/to/file.txt")

# Get only name and size
basic_info = await info("/path/to/file.txt", ["name", "size"])

# Get modification information
mod_info = await info("/path/to/file.txt", ["modified", "accessed"])
```
