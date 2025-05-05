#!/usr/bin/env python
"""
Test script for Web Search Tool

This script tests the web search functionality to ensure it works correctly
with the imported search engines from the search directory.

Author: Xinli Xu
Date: 2025-05-02
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add the src directory to the path
src_dir = Path(__file__).parent / "src"
sys.path.append(str(src_dir))

# Import the web search function
from core_logic import web_search


async def test_with_mocks():
    """Test with mock search engines to avoid dependency issues"""
    # Patch the search engines temporarily
    import unittest.mock as mock
    import sys
    from typing import List
    
    # Create mock search item for testing
    from src.search.base import SearchItem
    
    # Create a mock search result
    def mock_search(*args, **kwargs) -> List[SearchItem]:
        engine_name = args[0].__class__.__name__.replace("SearchEngine", "")
        return [
            SearchItem(
                title=f"{engine_name} Result 1",
                url="https://example.com/result1",
                description="This is a mock search result for testing purposes."
            ),
            SearchItem(
                title=f"{engine_name} Result 2",
                url="https://example.com/result2",
                description="Another mock result from the search engine."
            )
        ]
    
    # Apply the mock to all search engines
    with mock.patch('src.search.google_search.GoogleSearchEngine.perform_search', mock_search):
        with mock.patch('src.search.baidu_search.BaiduSearchEngine.perform_search', mock_search):
            with mock.patch('src.search.duckduckgo_search.DuckDuckGoSearchEngine.perform_search', mock_search):
                # Test query
                query = "Python programming"
                
                print(f"Testing search with MOCK engines and query: '{query}'")
                print("-" * 50)
                
                # Test with DuckDuckGo
                print("\n[DuckDuckGo Search (Mocked)]\n")
                result = await web_search(query, search_engine="duckduckgo", num_results=2)
                print(result)
                print("-" * 50)
                
                # Test with Google
                print("\n[Google Search (Mocked)]\n")
                result = await web_search(query, search_engine="google", num_results=2)
                print(result)
                print("-" * 50)
                
                # Test with Baidu
                print("\n[Baidu Search (Mocked)]\n")
                result = await web_search(query, search_engine="baidu", num_results=2)
                print(result)
                print("-" * 50)
                
                print("\nMocked tests completed successfully!")


async def test_with_real_engines():
    """Test the web search functionality with real search engines"""
    
    # Test search query
    query = "Python programming"
    
    print(f"Testing search with query: '{query}'")
    print("-" * 50)
    
    # Test with DuckDuckGo (default)
    print("\n[DuckDuckGo Search]\n")
    result = await web_search(query, search_engine="duckduckgo", num_results=3)
    print(result)
    print("-" * 50)
    
    # Test with Google
    print("\n[Google Search]\n")
    result = await web_search(query, search_engine="google", num_results=3)
    print(result)
    print("-" * 50)
    
    # Test with Baidu
    print("\n[Baidu Search]\n")
    result = await web_search(query, search_engine="baidu", num_results=3)
    print(result)
    print("-" * 50)
    
    print("\nAll tests completed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Web Search Tool')
    parser.add_argument('--mock', action='store_true', help='Use mock search engines instead of real ones')
    args = parser.parse_args()
    
    if args.mock:
        asyncio.run(test_with_mocks())
    else:
        asyncio.run(test_with_real_engines()) 