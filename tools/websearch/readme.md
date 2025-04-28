# Web Search Tool

A comprehensive tool for web search and browsing operations, designed to be used with the FractFlow framework.

## Features

- Search the web using different search engines (DuckDuckGo, Bing, Google)
- Browse web pages and extract various types of content
- Extract full text content from web pages
- Extract only titles from web pages
- Extract all links from web pages
- Retrieve raw HTML content from web pages

## Project Structure

- `__init__.py` - Package initialization file
- `requirements.txt` - Lists required packages (requests, beautifulsoup4, mcp, pytest, pytest-asyncio)
- `run_server.py` - Main entry point for starting the tool server in interactive or single query mode
- `src/` - Source code directory
  - `__init__.py` - Package initialization for the source directory
  - `core_logic.py` - Core functions for web search and browsing operations
  - `server.py` - FastMCP server that exposes web operations as tools for the FractFlow framework
- `tests/` - Test directory
  - `__init__.py` - Package initialization for the tests directory
  - `test_core_logic.py` - Unit tests for core web search and browsing functions
  - `test_run_server_integration.py` - Integration tests for the server interface

## Environment Setup with uv

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver that can be used to create isolated environments. Follow these steps to set up an environment for the Web Search Tool:

```bash
# Navigate to the websearch directory
cd tools/websearch

# Create a virtual environment
uv venv

# Activate the virtual environment
# On Unix/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies using uv
uv pip install -r requirements.txt
uv pip install -r ../../requirements.txt

# To install dev dependencies or additional packages
uv pip install pytest pytest-asyncio
```

## Environment Variables

The Web Search Tool requires certain environment variables to be set. Create a `.env` file in the `tools/websearch` directory following the file `.env.example`.


## Testing

The tool includes both unit tests and integration tests. You can run the tests using pytest:

```bash
# Run all tests
python -m pytest tools/websearch/tests/

# Run specific test file
python -m pytest tools/websearch/tests/test_core_logic.py
python -m pytest tools/websearch/tests/test_run_server_integration.py

# Run with verbose output
python -m pytest -v tools/websearch/tests/

# Run a specific test function
python -m pytest tools/websearch/tests/test_core_logic.py::test_web_search
```

## Usage

### Starting the Tool Server

```bash
# 1. Interactive chat mode
python run_server.py
# Enter your question, e.g. "Latest tech industry news"
Enter your question: 


# 2. Single query mode - process a single query and exit automatically
python run_server.py --user_query "Search for Python tutorials"

# 3. Import as an Agent tool
agent.add_tool("./tools/websearch/src/server.py")
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
# Search the web
python run_server.py --user_query "Search for Python tutorials"

# Browse a specific website
python run_server.py --user_query "Browse the website https://www.python.org and extract all the text"

# Extract links from a website
python run_server.py --user_query "Get all links from https://www.python.org"
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
   - Avoid hardcoding values; use parameters.
   - Keep each function small and focused.

5. **README Requirements**
   - Document your tool's main functions.
   - Include a section on environment setup.
   - Include usage examples (minimum 3 queries). 