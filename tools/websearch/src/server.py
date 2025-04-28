"""
Web Search Tool Server Module

This module provides a FastMCP server that exposes web search and browsing operations as tools.
It wraps the core web search logic in a server interface that can be used by the FractFlow
framework. Each tool is exposed as an endpoint that can be called by the FractFlow agent.
The web search functionality is inspired by OpenManus (https://github.com/mannaandpoem/OpenManus).

The server provides tools for:
- Searching the web using different search engines (DuckDuckGo, Bing, Google)
- Browsing web pages and extracting different types of content (text, title, links, HTML)

Author: Xinli Xu (xxu068@connect.hkust-gz.edu.cn) - Envision Lab
Date: 2025-04-28
License: MIT License
"""

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
import os


# Add the parent directory to the python path so we can import the core_logic module
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from src.core_logic import browse_webpage, web_search

# Initialize MCP server
mcp = FastMCP("web_search_browse_tool")

@mcp.tool()
async def web_browse(url: str, extract_type: str = "full_text") -> str:
    """
    Retrieves and extracts content from a webpage
    
    Args:
        url (str): The URL of the webpage to browse
        extract_type (str, optional): The type of content to extract. Options:
                                      "full_text" - Extract all text content
                                      "title" - Extract only the page title
                                      "links" - Extract all links on the page
                                      "html" - Return the raw HTML
                                      Default is "full_text"
        
    Returns:
        str: The extracted webpage content according to extract_type, or an error message if the URL is invalid or the request fails
        
    Example:
        web_browse("https://www.example.com", extract_type="full_text")
    """
    return await browse_webpage(url, extract_type)

@mcp.tool()
async def search_from_web(query: str, search_engine: str = "duckduckgo", num_results: int = 5) -> str:
    """
    Performs a web search and returns relevant results and the url of the webpage
    
    Args:
        query (str): The keywords or phrase to search for
        search_engine (str, optional): The search engine to use
                                      Options: "duckduckgo", "bing", "google"
                                      Default is "duckduckgo"
        num_results (int, optional): Number of results to return, default is 5
        
    Returns:
        str: Search results including titles, links and descriptions, or an error message if the search fails
        
    Example:
        search("Python programming tutorial", search_engine="duckduckgo", num_results=3)
    """
    return await web_search(query, search_engine, num_results)

# If this module is run directly, start the MCP server
if __name__ == "__main__":
    mcp.run(transport="stdio") 