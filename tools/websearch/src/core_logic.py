"""
Web Search Tool - Core Logic Module

This module implements the core web search and browsing operations for the FractFlow web search tool.
It provides functions for searching the web using various search engines (DuckDuckGo, Bing, Google)
and browsing web pages to extract different types of content.

Author: Xinli Xu (xxu068@connect.hkust-gz.edu.cn) - Envision Lab
Date: 2025-04-28
License: MIT License
"""

import requests
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup


def get_user_agent() -> str:
    """
    Returns a generic User-Agent header for HTTP requests.
    
    Returns:
        str: A browser User-Agent string
    """
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


def make_request(url: str, timeout: int = 15) -> requests.Response:
    """
    Sends an HTTP request and returns the response
    
    Args:
        url (str): The URL to request
        timeout (int): Timeout in seconds
        
    Returns:
        requests.Response: The HTTP response object
    
    Raises:
        requests.exceptions.RequestException: When the request fails
    """
    headers = {"User-Agent": get_user_agent()}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response


async def browse_webpage(url: str, extract_type: str = "full_text") -> str:
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
    """
    try:
        # Check if URL is valid
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return "Invalid URL. Please provide a complete URL including http:// or https://"
        
        # Send request
        response = make_request(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract content based on extract_type
        if extract_type == "full_text":
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text(separator="\n", strip=True)
            return text
            
        elif extract_type == "title":
            title = soup.title.string if soup.title else "No title found"
            return title
            
        elif extract_type == "links":
            links = []
            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    links.append(f"{link.text.strip()} - {href}")
            return "\n".join(links) if links else "No links found"
            
        elif extract_type == "html":
            return response.text
            
        else:
            return f"Invalid extract_type: {extract_type}. Valid options: full_text, title, links, html"
            
    except requests.exceptions.RequestException as e:
        return f"Failed to fetch URL: {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"


async def search_duckduckgo(query: str, num_results: int) -> str:
    """
    Performs a search using the DuckDuckGo search engine
    
    Args:
        query (str): The search query
        num_results (int): Number of results to return
        
    Returns:
        str: Formatted search results string
    """
    url = f"https://html.duckduckgo.com/html/?q={query}"
    response = make_request(url, timeout=15)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    
    # Parse DuckDuckGo search results
    for result in soup.select('.result')[:num_results]:
        title_elem = result.select_one('.result__title')
        if not title_elem:
            continue
            
        title = title_elem.get_text(strip=True)
        link_elem = title_elem.select_one('a')
        link = link_elem.get('href') if link_elem else "Link not found"
        
        # Handle DuckDuckGo's redirect links
        if link.startswith('/'):
            # This is a DuckDuckGo redirect link, try to extract the real URL
            try:
                parsed = parse_qs(link.split('?', 1)[1])
                if 'uddg' in parsed:
                    link = parsed['uddg'][0]
            except:
                pass
        
        snippet_elem = result.select_one('.result__snippet')
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else "No description available"
        
        results.append(f"📌 {title}\n🔗 {link}\n📄 {snippet}\n")
    
    if not results:
        return f"No results found for '{query}' on DuckDuckGo"
        
    return f"🔍 Search results for '{query}':\n\n" + "\n".join(results)


async def search_bing(query: str, num_results: int) -> str:
    """
    Performs a search using the Bing search engine
    
    Args:
        query (str): The search query
        num_results (int): Number of results to return
        
    Returns:
        str: Formatted search results string
    """
    url = f"https://www.bing.com/search?q={query}"
    response = make_request(url, timeout=15)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    
    # Parse Bing search results
    for result in soup.select('.b_algo')[:num_results]:
        title_elem = result.select_one('h2')
        if not title_elem:
            continue
            
        title = title_elem.get_text(strip=True)
        link_elem = title_elem.select_one('a')
        link = link_elem.get('href') if link_elem else "Link not found"
        
        snippet_elem = result.select_one('.b_caption p')
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else "No description available"
        
        results.append(f"📌 {title}\n🔗 {link}\n📄 {snippet}\n")
    
    if not results:
        return f"No results found for '{query}' on Bing"
        
    return f"🔍 Search results for '{query}':\n\n" + "\n".join(results)


async def search_google(query: str, num_results: int) -> str:
    """
    Performs a search using the Google search engine
    
    Args:
        query (str): The search query
        num_results (int): Number of results to return
        
    Returns:
        str: Formatted search results string
    """
    url = f"https://www.google.com/search?q={query}&num={min(num_results, 10)}"
    response = make_request(url, timeout=15)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    
    # Parse Google search results
    # Google structure may change frequently, this uses a common selector
    for result in soup.select('div.g')[:num_results]:
        title_elem = result.select_one('h3')
        if not title_elem:
            continue
            
        title = title_elem.get_text(strip=True)
        
        link_elem = result.select_one('a')
        link = link_elem.get('href') if link_elem else "Link not found"
        if link.startswith('/url?'):
            try:
                parsed = parse_qs(link.split('?', 1)[1])
                if 'q' in parsed:
                    link = parsed['q'][0]
            except:
                pass
        
        snippet_elem = result.select_one('div.VwiC3b')
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else "No description available"
        
        results.append(f"📌 {title}\n🔗 {link}\n📄 {snippet}\n")
    
    if not results:
        return f"No results found for '{query}' on Google"
        
    return f"🔍 Search results for '{query}':\n\n" + "\n".join(results)


async def web_search(query: str, search_engine: str = "duckduckgo", num_results: int = 5) -> str:
    """
    Performs a web search and returns relevant results
    
    Args:
        query (str): The keywords or phrase to search for
        search_engine (str, optional): The search engine to use
                                      Options: "duckduckgo", "bing", "google"
                                      Default is "duckduckgo"
        num_results (int, optional): Number of results to return, default is 5
        
    Returns:
        str: Search results including titles, links and descriptions, or an error message if the search fails
    """
    try:
        # Validate the num_results parameter
        if num_results <= 0:
            return "Number of results must be greater than 0"
        
        if num_results > 20:
            num_results = 20
            
        search_engine = search_engine.lower()
        
        if search_engine == "duckduckgo":
            return await search_duckduckgo(query, num_results)
        elif search_engine == "bing":
            return await search_bing(query, num_results)
        elif search_engine == "google":
            return await search_google(query, num_results)
        else:
            return f"Unsupported search engine: {search_engine}. Supported options: duckduckgo, bing, google"
            
    except requests.exceptions.RequestException as e:
        return f"Search request failed: {str(e)}"
    except Exception as e:
        return f"An error occurred while performing the search: {str(e)}" 