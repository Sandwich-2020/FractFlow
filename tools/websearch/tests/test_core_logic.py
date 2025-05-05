"""
Core Logic Unit Tests

This module contains unit tests for the core_logic.py module, testing web search
and browsing operations.

The tests use pytest and the pytest-asyncio plugin to test asynchronous functions.
For web-related tests, most functions use mocking to avoid actual network requests.

Author: Xinli Xu (xxu068@connect.hkust-gz.edu.cn) - Envision Lab
Date: 2025-05-03 (Updated)
License: MIT License
"""

import os
import sys
import pytest
import unittest.mock as mock
from unittest.mock import AsyncMock
from bs4 import BeautifulSoup
import requests
import io

# Add the parent directory to the Python path so we can import modules from there
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.core_logic import (
        crawl,
        web_search_and_browse,
        web_search,
        is_pdf_content,
        extract_text_from_pdf
    )
    from src.search.base import SearchItem
except ImportError as e:
    print(f"Import error: {e}")
    raise

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
def mock_html_response():
    """
    A pytest fixture that creates a mock HTTP response for HTML content.
    """
    mock_resp = mock.Mock()
    mock_resp.text = "<html><head><title>Test Page</title></head><body><p>Hello World</p></body></html>"
    mock_resp.content = b"<html><head><title>Test Page</title></head><body><p>Hello World</p></body></html>"
    mock_resp.headers = {"content-type": "text/html; charset=utf-8"}
    mock_resp.raise_for_status = mock.Mock()
    return mock_resp

@pytest.fixture
def mock_pdf_response():
    """
    A pytest fixture that creates a mock HTTP response for PDF content.
    """
    mock_resp = mock.Mock()
    mock_resp.content = b"%PDF-1.3\nSome fake PDF content"
    mock_resp.headers = {"content-type": "application/pdf"}
    mock_resp.raise_for_status = mock.Mock()
    return mock_resp

def test_is_pdf_content():
    """Test the PDF detection function."""
    # Test with Content-Type header
    assert is_pdf_content("application/pdf", b"some content") == True
    assert is_pdf_content("text/html", b"some content") == False
    
    # Test with PDF signature
    assert is_pdf_content("", b"%PDF-1.5\nsome content") == True
    assert is_pdf_content("", b"not a pdf") == False

@mock.patch('src.core_logic.PyPDF2.PdfReader')
def test_extract_text_from_pdf(mock_pdf_reader):
    """Test PDF text extraction."""
    # Setup mock
    mock_page = mock.Mock()
    mock_page.extract_text.return_value = "Sample PDF text"
    mock_reader_instance = mock.Mock()
    mock_reader_instance.pages = [mock_page, mock_page]  # Two pages
    mock_pdf_reader.return_value = mock_reader_instance
    
    # Test extraction
    result = extract_text_from_pdf(b"%PDF-1.3\nFake PDF content")
    assert "Sample PDF text" in result
    assert mock_page.extract_text.call_count == 2

@pytest.mark.asyncio
@mock.patch('src.core_logic.httpx.AsyncClient')
async def test_crawl_impl_html(mock_async_client):
    """Test crawling HTML content."""
    # Create a proper async mock
    mock_response = mock.Mock()
    mock_response.text = "<html><title>Test Title</title><body>Test Content</body></html>"
    mock_response.content = mock_response.text.encode('utf-8')
    mock_response.headers = {"content-type": "text/html"}
    mock_response.raise_for_status = mock.Mock()
    
    # Create an async mock for the client
    client_instance = AsyncMock()
    client_instance.get.return_value = mock_response
    
    # Make AsyncClient() return our context manager
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = client_instance
    mock_async_client.return_value = context_manager
    
    # Call the function
    result = await crawl({"url": "https://example.com"})
    
    # Verify results
    assert "error" not in result, f"Error in result: {result.get('error')}"
    assert "Test Content" in result["content"]
    assert result["url"] == "https://example.com"

@pytest.mark.asyncio
@mock.patch('src.core_logic.httpx.AsyncClient')
@mock.patch('src.core_logic.extract_text_from_pdf')
async def test_crawl_impl_pdf(mock_extract_text, mock_async_client):
    """Test crawling PDF content."""
    # Create a proper mock response for PDF
    mock_response = mock.Mock()
    mock_response.content = b"%PDF-1.3\nFake PDF content"
    mock_response.headers = {"content-type": "application/pdf"}
    mock_response.raise_for_status = mock.Mock()
    
    # Create an async mock for the client
    client_instance = AsyncMock()
    client_instance.get.return_value = mock_response
    
    # Make AsyncClient() return our context manager
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = client_instance
    mock_async_client.return_value = context_manager
    
    # Setup PDF extraction mock
    mock_extract_text.return_value = "Extracted PDF text"
    
    # Call the function
    result = await crawl({"url": "https://example.com/document.pdf"})
    
    # Verify results
    assert "error" not in result, f"Error in result: {result.get('error')}"
    assert result["content"] == "Extracted PDF text"
    assert result["url"] == "https://example.com/document.pdf"

@pytest.mark.asyncio
@mock.patch('src.core_logic.httpx.AsyncClient')
async def test_crawl_invalid_url(mock_async_client):
    """Test crawling with an invalid URL."""
    result = await crawl({"url": "invalid-url"})
    assert "error" in result
    assert "无效的URL" in result["error"]

@pytest.mark.asyncio
@mock.patch('src.core_logic.web_search')
async def test_web_search_and_browse_search_only(mock_web_search):
    """Test web search and browse with search-only mode."""
    mock_web_search.return_value = "Mock search results"
    query = "test query"
    
    # Test with max_browse=-1 (search only)
    result = await web_search_and_browse(query, search_engine="google", num_results=5, max_browse=-1)
    
    mock_web_search.assert_called_once_with(query, "google", 5)
    assert result == "Mock search results"

@pytest.mark.asyncio
@mock.patch('src.core_logic.web_search')
@mock.patch('src.core_logic.crawl')
async def test_web_search_and_browse_with_browsing(mock_crawl, mock_web_search):
    """Test web search and browse with browsing results."""
    # Setup search mock
    mock_web_search.return_value = """🔍 Search results for 'test query' from Google:

📌 Test Result 1
🔗 https://example.com/1
📄 Description 1

📌 Test Result 2
🔗 https://example.com/2
📄 Description 2"""

    # Setup crawl mock to return different results for different URLs
    async def mock_crawl_side_effect(args):
        url = args["url"]
        return {
            "content": f"Content from {url}",
            "url": url,
            "is_pdf": False
        }
    mock_crawl.side_effect = mock_crawl_side_effect
    
    # Test with max_browse=1 (browse first result only)
    result = await web_search_and_browse("test query", search_engine="google", num_results=5, max_browse=1)
    
    # Verify search was called
    mock_web_search.assert_called_once_with("test query", "google", 5)
    
    # Verify crawl was called for the first URL
    assert mock_crawl.call_count == 1
    assert mock_crawl.call_args[0][0]["url"] == "https://example.com/1"
    
    # Verify result contains both search results and content
    assert "搜索结果:" in result
    assert "Content from https://example.com/1" in result

@pytest.mark.asyncio
@mock.patch('src.core_logic.web_search')
async def test_web_search_and_browse_no_urls(mock_web_search):
    """Test web search and browse when no URLs are found in search results."""
    mock_web_search.return_value = "No results found"
    
    result = await web_search_and_browse("test query", max_browse=1)
    
    assert "无法从搜索结果中提取URL" in result

@pytest.mark.asyncio
@mock.patch('src.core_logic.DuckDuckGoSearchEngine.perform_search')
async def test_web_search_duckduckgo(mock_search):
    """Test web search with DuckDuckGo search engine."""
    # 设置mock返回值
    mock_search.return_value = [
        SearchItem(title='Test Result', url='https://example.com', description='Test Description')
    ]
    
    # 执行测试
    result = await web_search("test query", search_engine="duckduckgo", num_results=5)
    
    # 验证mock被调用
    mock_search.assert_called_once()
    
    # 验证结果包含期望的内容
    assert "Search results for 'test query'" in result
    assert "Test Result" in result
    assert "https://example.com" in result
    assert "Test Description" in result

@pytest.mark.asyncio
@mock.patch('src.core_logic.GoogleSearchEngine.perform_search')
async def test_web_search_google(mock_search):
    """Test web search with Google search engine."""
    # 设置mock返回值
    mock_search.return_value = [
        SearchItem(title='Test Result', url='https://example.com', description='Test Description')
    ]
    
    # 执行测试
    result = await web_search("test query", search_engine="google", num_results=5)
    
    # 验证mock被调用
    mock_search.assert_called_once()
    
    # 验证结果包含期望的内容
    assert "Search results for 'test query'" in result
    assert "Test Result" in result
    assert "https://example.com" in result
    assert "Test Description" in result

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