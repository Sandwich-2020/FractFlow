# Code Generation Tool (codegen2)

A tool for the EnvisionCore framework that provides advanced file editing capabilities for code generation.

## Features

- **Read files with line numbers** - Get file contents with corresponding line numbers (1|Line content)
- **Line range editing** - Edit specific sections of files by line numbers
- **Large file handling** - Handle large files by editing specific sections
- **Append mode** - Add content to the end of files
- **Auto-file creation** - Create files automatically if they don't exist
- **Directory listing** - List all files and directories in a specified path
- **Line removal** - Remove specified lines from files

## Installation

1. Clone this repository or download the source code
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Server

You can run the tool server in two modes:

1. **Interactive mode** - Process queries continuously until exit
   ```bash
   python run_server.py
   ```

2. **Single query mode** - Process a single query and exit
   ```bash
   python run_server.py --user_query "Edit the file example.py to add a new function"
   ```

### API

The tool provides the following operations:

#### 1. Read File

Read the contents of a file, optionally with line numbers.

```python
# Read file content without line numbers
content = await agent.tool("codegen2.read_file", file_path="/path/to/file.py", is_return_line_numbers=False)

# Read with line numbers (Default behavior)
numbered_content = await agent.tool("codegen2.read_file", file_path="/path/to/file.py")
# Result will be formatted as:
# 1|def example():
# 2|    print("Hello world")
# 3|
# 4|example()
```

#### 2. Read File Range

Read a specific range of lines from a file.

```python
# Read lines 10-20
result = await agent.tool("codegen2.read_file_range", file_path="/path/to/file.py", start_line=10, end_line=20)
content = result['content']
```

#### 3. List Directory

List all files and directories in a specified directory.

```python
# List files in a directory
result = await agent.tool("codegen2.list_directory", directory_path="/path/to/directory")

# Process the results
for item in result:
    # Check if item is a directory
    if item['is_dir']:
        print(f"Directory: {item['name']}")
    else:
        print(f"File: {item['name']} (Size: {item['size']} bytes)")
```

#### 4. Edit File

Edit a file by replacing content between specified lines.

```python
# Replace entire file
result = await agent.tool("codegen2.edit_file", file_path="/path/to/file.py", content="new content")

# Edit specific lines (lines 3-5)
result = await agent.tool("codegen2.edit_file", file_path="/path/to/file.py", content="new content", start_line=3, end_line=5)

# Append to file
result = await agent.tool("codegen2.edit_file", file_path="/path/to/file.py", content="new content", start_line=-1)
```

#### 5. Remove File Lines

Remove specified lines from a file.

```python
# Remove lines 3-5
result = await agent.tool("codegen2.remove_file_lines", file_path="/path/to/file.py", start_line=3, end_line=5)

# Remove from line 10 to the end of the file
result = await agent.tool("codegen2.remove_file_lines", file_path="/path/to/file.py", start_line=10)
```

## Examples

### Example 1: Edit a Short File

```python
# Read the current file with line numbers
numbered_content = await agent.tool("codegen2.read_file", file_path="example.py")
print(f"Original content:\n{numbered_content}")

# Edit the file
edit_result = await agent.tool("codegen2.edit_file", 
                              file_path="example.py", 
                              content="def hello_world():\n    print('Hello, World!')\n\nhello_world()", 
                              start_line=1)
print(f"Edit result: {edit_result}")
```

### Example 2: Edit a Specific Section of a Large File

```python
# Read a range of lines
result = await agent.tool("codegen2.read_file_range", 
                         file_path="large_file.py", 
                         start_line=100, 
                         end_line=110)
print(f"Lines 100-110: {result['content']}")

# Edit just those lines
edit_result = await agent.tool("codegen2.edit_file", 
                              file_path="large_file.py", 
                              content="# This is the edited section\ndef new_function():\n    return 'New functionality'\n", 
                              start_line=100, 
                              end_line=110)
print(f"Edit result: {edit_result}")
```

### Example 3: Append to a File

```python
# Append a new function to the end of the file
edit_result = await agent.tool("codegen2.edit_file", 
                              file_path="example.py", 
                              content="\n\ndef another_function():\n    print('Another function')\n", 
                              start_line=-1)
print(f"Append result: {edit_result}")
```

### Example 4: List Files in a Directory

```python
# List files in the current directory
dir_result = await agent.tool("codegen2.list_directory", directory_path=".")

# Display the results
print("Files and directories:")
for item in dir_result:
    item_type = "Directory" if item['is_dir'] else "File"
    size_info = "" if item['is_dir'] else f" ({item['size']} bytes)"
    print(f"{item_type}: {item['name']}{size_info}")
```

### Example 5: Remove Lines from a File

```python
# First read the file with line numbers
numbered_content = await agent.tool("codegen2.read_file", file_path="example.py")
print(f"Original content:\n{numbered_content}")

# Remove lines 3-5
remove_result = await agent.tool("codegen2.remove_file_lines", 
                                file_path="example.py", 
                                start_line=3, 
                                end_line=5)
print(f"Removed {remove_result['removed_lines']} lines")

# Read the file again to see changes
updated_content = await agent.tool("codegen2.read_file", file_path="example.py")
print(f"Updated content:\n{updated_content}")
```

## License

MIT License 