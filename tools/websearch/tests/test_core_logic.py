"""
Core Logic Unit Tests

This module contains unit tests for the core_logic.py module, testing web search
and browsing operations.

The tests use pytest and the pytest-asyncio plugin to test asynchronous functions.
For web-related tests, most functions use mocking to avoid actual network requests.

Author: Xinli Xu (xxu068@connect.hkust-gz.edu.cn) - Envision Lab
Date: 2025-04-28
License: MIT License
"""

import os
import sys
import pytest
import unittest.mock as mock
from bs4 import BeautifulSoup
import requests

# Add the parent directory to the Python path so we can import modules from there
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core_logic import (
    get_user_agent,
    make_request,
    browse_webpage,
    search_duckduckgo,
    search_bing,
    search_google,
    web_search
)

# ===== PYTEST EXPLANATIONS =====
# 
# pytest is a testing framework for Python that makes it easy to write simple
# and scalable test cases. Here's how it works in this file:
#
# 1. FIXTURES (@pytest.fixture):
#    - Fixtures are functions that provide a fixed baseline for tests
#    - They set up any required resources before tests and clean up after tests
#    - They're defined using the @pytest.fixture decorator
#    - Fixtures can be requested by test functions by adding their names as parameters
#
# 2. ASYNCIO TESTING (@pytest.mark.asyncio):
#    - This marker tells pytest that the test function is an async function
#    - It enables proper async/await execution and handling in the test
#    - Requires the pytest-asyncio plugin to be installed
#    - Allows testing of async functions using the "await" keyword
#
# 3. MOCKING:
#    - We use unittest.mock to create mock objects to simulate responses
#    - This allows us to test network operations without actually making HTTP requests
#    - It makes tests faster, more reliable, and independent of network conditions
#

@pytest.fixture
def mock_response():
    """
    A pytest fixture that creates a mock HTTP response for testing.
    """
    mock_resp = mock.Mock()
    mock_resp.text = "<html><head><title>Test Page</title></head><body><p>Hello World</p></body></html>"
    mock_resp.raise_for_status = mock.Mock()
    return mock_resp

def test_get_user_agent():
    """Test the get_user_agent function returns a non-empty string."""
    user_agent = get_user_agent()
    assert isinstance(user_agent, str)
    assert len(user_agent) > 0
    assert "Mozilla" in user_agent  # Common string found in user agent strings

@mock.patch('src.core_logic.requests.get')
def test_make_request(mock_get, mock_response):
    """Test that make_request calls requests.get with the right parameters and returns the response."""
    mock_get.return_value = mock_response
    url = "https://example.com"
    timeout = 30
    
    response = make_request(url, timeout)
    
    mock_get.assert_called_once()
    call_args = mock_get.call_args[0]
    call_kwargs = mock_get.call_args[1]
    assert call_args[0] == url
    assert call_kwargs['timeout'] == timeout
    assert 'headers' in call_kwargs
    assert call_kwargs['headers']['User-Agent'] == get_user_agent()
    assert response == mock_response

@pytest.mark.asyncio
@mock.patch('src.core_logic.make_request')
async def test_browse_webpage_full_text(mock_make_request, mock_response):
    """Test browsing a webpage and extracting full text content."""
    mock_make_request.return_value = mock_response
    url = "https://example.com"
    
    result = await browse_webpage(url, extract_type="full_text")
    
    mock_make_request.assert_called_once_with(url, timeout=10)
    assert "Hello World" in result

@pytest.mark.asyncio
@mock.patch('src.core_logic.make_request')
async def test_browse_webpage_title(mock_make_request, mock_response):
    """Test browsing a webpage and extracting the title."""
    mock_make_request.return_value = mock_response
    url = "https://example.com"
    
    result = await browse_webpage(url, extract_type="title")
    
    mock_make_request.assert_called_once_with(url, timeout=10)
    assert result == "Test Page"

@pytest.mark.asyncio
@mock.patch('src.core_logic.make_request')
async def test_browse_webpage_invalid_url(mock_make_request):
    """Test browsing with an invalid URL."""
    url = "invalid-url"
    
    result = await browse_webpage(url)
    
    mock_make_request.assert_not_called()
    assert "Invalid URL" in result

@pytest.mark.asyncio
@mock.patch('src.core_logic.search_duckduckgo')
async def test_web_search_duckduckgo(mock_search_duckduckgo):
    """Test web search with DuckDuckGo search engine."""
    mock_search_duckduckgo.return_value = "Mock DuckDuckGo results"
    query = "test query"
    
    result = await web_search(query, search_engine="duckduckgo", num_results=5)
    
    mock_search_duckduckgo.assert_called_once_with(query, 5)
    assert result == "Mock DuckDuckGo results"

@pytest.mark.asyncio
@mock.patch('src.core_logic.search_bing')
async def test_web_search_bing(mock_search_bing):
    """Test web search with Bing search engine."""
    mock_search_bing.return_value = "Mock Bing results"
    query = "test query"
    
    result = await web_search(query, search_engine="bing", num_results=5)
    
    mock_search_bing.assert_called_once_with(query, 5)
    assert result == "Mock Bing results"

@pytest.mark.asyncio
@mock.patch('src.core_logic.search_google')
async def test_web_search_google(mock_search_google):
    """Test web search with Google search engine."""
    mock_search_google.return_value = "Mock Google results"
    query = "test query"
    
    result = await web_search(query, search_engine="google", num_results=5)
    
    mock_search_google.assert_called_once_with(query, 5)
    assert result == "Mock Google results"

@pytest.mark.asyncio
async def test_web_search_invalid_engine():
    """Test web search with an invalid search engine."""
    query = "test query"
    
    result = await web_search(query, search_engine="invalid_engine", num_results=5)
    
    assert "Unsupported search engine" in result

@pytest.mark.asyncio
async def test_web_search_invalid_num_results():
    """Test web search with an invalid number of results."""
    query = "test query"
    
    result = await web_search(query, search_engine="duckduckgo", num_results=0)
    
    assert "Number of results must be greater than 0" in result 