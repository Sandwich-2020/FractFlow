# File I/O Tool

A comprehensive tool for file and directory operations, designed to be used with the EnvisionCore framework.

## Features

- Read and write files (text and binary)
- List directory contents with metadata
- Delete files and directories
- Move and copy files and directories
- Check if files exist
- Get detailed file information

## Project Structure

- `__init__.py` - Package initialization file
- `requirements.txt` - Lists required packages (pytest, pytest-asyncio, mcp, pathlib)
- `run_server.py` - Main entry point for starting the tool server in interactive or single query mode
- `src/` - Source code directory
  - `__init__.py` - Package initialization for the source directory
  - `core_logic.py` - Core functions for file operations (read, write, move, copy, delete, etc.)
  - `server.py` - FastMCP server that exposes file operations as tools for the EnvisionCore framework
- `tests/` - Test directory
  - `__init__.py` - Package initialization for the tests directory
  - `test_core_logic.py` - Unit tests for core file operation functions
  - `test_run_server_integration.py` - Integration tests for the server interface

## Environment Setup with uv

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver that can be used to create isolated environments. Follow these steps to set up an environment for the File I/O Tool:

```bash
# Navigate to the file_io directory
cd tools/file_io

# Create a virtual environment
uv venv

# Activate the virtual environment
# On Unix/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies using uv
uv pip install -r requirements.txt

# To install dev dependencies or additional packages
uv pip install pytest pytest-asyncio
```

## Testing

The tool includes both unit tests and integration tests. You can run the tests using pytest:

```bash
# Run all tests
python -m pytest tools/file_io/tests/

# Run specific test file
python -m pytest tools/file_io/tests/test_core_logic.py
python -m pytest tools/file_io/tests/test_run_server_integration.py

# Run with verbose output
python -m pytest -v tools/file_io/tests/

# Run a specific test function
python -m pytest tools/file_io/tests/test_core_logic.py::test_read_write_file
```

## Usage

### Starting the Tool Server

```bash
# 1. Interactive chat mode
python run_server.py

# 2. Single query mode - process a single query and exit automatically
python run_server.py --user_query "Read the file /path/to/file.txt"

# 3. Import as an Agent tool
agent.add_tool("./tools/file_io/src/server.py")
```

#### Running Modes

1. **Interactive Chat Mode** - Default mode
   - Starts an interactive command line interface
   - Can input multiple queries and receive responses
   - Enter 'exit', 'quit', or 'bye' to exit

2. **Single Query Mode** - Run with `--user_query` parameter
   - Automatically processes one query and displays the result
   - Exits automatically after processing
   - Suitable for script integration and automation tasks

Examples:
```bash
# List directory contents
python run_server.py --user_query "List all files in /tmp directory"

# Create and write to a file
python run_server.py --user_query "Create a file at ~/Downloads/test.txt and write 'Hello World'"

# Get file information
python run_server.py --user_query "Get detailed information about the file /etc/hosts"
```

---

# Development Guidelines

To ensure consistency and easy integration, please follow these development standards:

1. **Project Structure**
   - Follow the standard layout: `src/`, `tests/`, `requirements.txt`, `run_server.py`.
   - Keep core logic (`core_logic.py`) and server interface (`server.py`) separated.

2. **Environment Management**
   - Use `uv venv` to create a virtual environment inside each tool directory.
   - Install dependencies from `requirements.txt`.
   - Always activate the `.venv` before developing or running the tool.

3. **Testing Requirements**
   - Provide at least one unit test (`test_core_logic.py`) to verify basic functions.
   - Provide at least one integration test (`test_run_server_integration.py`) to test server interface.
   - Use `pytest` for all tests.

4. **Coding Style**
   - Use `snake_case` for all variable, function, and file names.
   - Write clear docstrings for all public functions and classes.
   - Avoid hardcoding paths; use parameters or environment variables.
   - Keep each function small and focused.

5. **README Requirements**
   - Document your tool's main functions.
   - Include a section on environment setup.
   - Include usage examples (minimum 3 queries).