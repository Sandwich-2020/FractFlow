"""
Web Search Tool - Unified Interface

This module provides a unified interface for web search operations that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced web search as MCP tools
2. Interactive mode: Runs as an interactive agent with web search capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python websearch_tool.py                        # MCP Server mode (default)
  python websearch_tool.py --interactive          # Interactive mode
  python websearch_tool.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class WebSearchTool(ToolTemplate):
    """Web search tool using ToolTemplate"""
    
    SYSTEM_PROMPT = """你会用萌萌哒的语气回复，当调用网页浏览工具无法得出具体或者确切的答案时，请调用网页浏览工具来浏览相关性最强的网页回答"""
    
    TOOLS = [
        ("src/server.py", "web_search")
    ]
    
    MCP_SERVER_NAME = "web_search_tool"
    
    TOOL_DESCRIPTION = """
    Performs web searches and browses web pages to find information based on natural language queries.

This tool can search the web for current information, browse specific websites, and extract relevant content to answer user questions. It supports both general web searches and targeted webpage analysis.

Input format:
- Natural language questions or search queries
- Can include specific websites to search within
- May request recent information or current events
- Can ask for detailed analysis of specific web pages

Returns:
- 'search_results': List of relevant web search results
- 'web_content': Extracted content from browsed pages
- 'sources': URLs and titles of information sources used
- 'success': Boolean indicating operation completion
- 'message': Additional context about the search process

Examples:
- "What are the latest developments in AI technology?"
- "Search for Python tutorials for beginners"
- "Find information about climate change effects in 2024"
- "Browse the official documentation for React framework"
- "What are people saying about the new iPhone model?"
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Web Search tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=10,  # Web search may require multiple rounds
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    WebSearchTool.main() 