"""
Run Server Integration Tests

This module contains integration tests for the run_server.py module and the server interface.
It tests the integration between the server and the core logic, and how the server handles
different types of requests.

The tests use pytest and the pytest-asyncio plugin to test asynchronous functions.
For integration tests, we use mocks to avoid actual network requests but still test
the flow between components.

Author: Xinli Xu (xxu068@connect.hkust-gz.edu.cn) - Envision Lab
Date: 2025-04-28
License: MIT License
"""

import os
import sys
import pytest
import unittest.mock as mock
import asyncio
from pathlib import Path

# Add the parent directory to the Python path so we can import modules from there
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the run_server module
import run_server
from src.server import web_browse, search
from src.core_logic import browse_webpage, web_search

# Mock Agent class for testing
class MockAgent:
    def __init__(self, name):
        self.name = name
        self.config = {
            'agent': {
                'provider': 'test',
                'max_iterations': 5
            },
            'deepseek': {
                'model': 'test-model'
            }
        }
        self.tools = []
    
    def get_config(self):
        return self.config
    
    def set_config(self, config):
        self.config = config
    
    def add_tool(self, tool_path):
        self.tools.append(tool_path)
    
    async def initialize(self):
        return True
    
    async def process_query(self, query):
        if "search" in query.lower():
            return f"Search results for: {query}"
        elif "browse" in query.lower():
            return f"Browsing results for: {query}"
        else:
            return f"Processed: {query}"
    
    async def shutdown(self):
        return True


@pytest.fixture
def mock_agent():
    """
    A pytest fixture that creates a mock agent for testing.
    """
    return MockAgent("test_agent")


@pytest.mark.asyncio
@mock.patch('run_server.Agent', return_value=MockAgent("test_agent"))
async def test_create_agent(mock_agent_class):
    """Test the create_agent function properly initializes and configures the agent."""
    agent = await run_server.create_agent()
    
    assert agent.name == "test_agent"
    assert agent.config['agent']['provider'] == 'deepseek'
    assert agent.config['deepseek']['model'] == 'deepseek-chat'
    assert agent.config['agent']['max_iterations'] == 5
    assert "./tools/websearch/src/server.py" in agent.tools


@pytest.mark.asyncio
async def test_single_query_mode(mock_agent):
    """Test the single_query_mode function properly processes a query."""
    query = "Search for Python tutorials"
    result = await run_server.single_query_mode(mock_agent, query)
    
    assert result == "Search results for: Search for Python tutorials"


@pytest.mark.asyncio
@mock.patch('run_server.Agent', return_value=MockAgent("test_agent"))
@mock.patch('run_server.input', side_effect=["Search query", "exit"])
@mock.patch('run_server.print')
async def test_interactive_mode(mock_print, mock_input, mock_agent_class):
    """
    Test the interactive_mode function properly handles user input and processes queries.
    This test simulates a user entering a search query and then exiting.
    """
    agent = await run_server.create_agent()
    
    # Run the interactive mode function (will exit after processing "exit" input)
    await run_server.interactive_mode(agent)
    
    # Check that print was called with the expected results
    assert any("Search results for: Search query" in str(call) for call in mock_print.call_args_list)


@pytest.mark.asyncio
@mock.patch('src.core_logic.browse_webpage')
async def test_web_browse_integration(mock_browse_webpage):
    """Test the integration between the server web_browse function and core logic."""
    mock_browse_webpage.return_value = "Webpage content"
    url = "https://example.com"
    extract_type = "full_text"
    
    result = await web_browse(url, extract_type)
    
    mock_browse_webpage.assert_called_once_with(url, extract_type)
    assert result == "Webpage content"


@pytest.mark.asyncio
@mock.patch('src.core_logic.web_search')
async def test_search_integration(mock_web_search):
    """Test the integration between the server search function and core logic."""
    mock_web_search.return_value = "Search results"
    query = "test query"
    search_engine = "duckduckgo"
    num_results = 5
    
    result = await search(query, search_engine, num_results)
    
    mock_web_search.assert_called_once_with(query, search_engine, num_results)
    assert result == "Search results"


@pytest.mark.asyncio
@mock.patch('run_server.Agent', return_value=MockAgent("test_agent"))
@mock.patch('run_server.argparse.ArgumentParser.parse_args')
@mock.patch('run_server.single_query_mode')
async def test_main_single_query(mock_single_query_mode, mock_parse_args, mock_agent_class):
    """Test the main function in single query mode."""
    # Set up the mock to simulate command-line arguments for single query mode
    mock_args = mock.Mock()
    mock_args.user_query = "Search for Python"
    mock_parse_args.return_value = mock_args
    
    # Set up the expected return value for single_query_mode
    mock_single_query_mode.return_value = "Search results for: Search for Python"
    
    # Run the main function
    await run_server.main()
    
    # Check that single_query_mode was called with the expected arguments
    mock_single_query_mode.assert_called_once()
    agent = mock_single_query_mode.call_args[0][0]
    query = mock_single_query_mode.call_args[0][1]
    assert agent.name == "test_agent"
    assert query == "Search for Python"


@pytest.mark.asyncio
@mock.patch('run_server.Agent', return_value=MockAgent("test_agent"))
@mock.patch('run_server.argparse.ArgumentParser.parse_args')
@mock.patch('run_server.interactive_mode')
async def test_main_interactive(mock_interactive_mode, mock_parse_args, mock_agent_class):
    """Test the main function in interactive mode."""
    # Set up the mock to simulate command-line arguments for interactive mode
    mock_args = mock.Mock()
    mock_args.user_query = None
    mock_parse_args.return_value = mock_args
    
    # Run the main function
    await run_server.main()
    
    # Check that interactive_mode was called with the expected arguments
    mock_interactive_mode.assert_called_once()
    agent = mock_interactive_mode.call_args[0][0]
    assert agent.name == "test_agent" 