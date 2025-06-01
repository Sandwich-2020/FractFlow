"""
Web Save Tool - Unified Interface

This module provides a unified interface for web search and file saving operations that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced web search and save as MCP tools
2. Interactive mode: Runs as an interactive agent with web search and file capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python web_save_tool.py                        # MCP Server mode (default)
  python web_save_tool.py --interactive          # Interactive mode
  python web_save_tool.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class WebSaveTool(ToolTemplate):
    """Web search and save tool using ToolTemplate with fractal intelligence"""
    
    SYSTEM_PROMPT = """
你是一个专业的信息收集和整理助手，专门负责从网络搜索信息并将结果保存到文件中。

## 工作流程

1. **信息搜索阶段**
   - 根据用户需求进行网页搜索
   - 如果搜索结果不够具体，进一步浏览相关性最强的网页

2. **内容整理阶段**
   - 将搜索到的信息进行整理和结构化
   - 确保信息的完整性和准确性
   - 组织内容为清晰易读的格式

3. **文件保存阶段**
   - 将整理好的内容直接保存到指定文件
   - 确保文件格式正确，内容完整
   - 提供保存确认和文件路径信息
   - 默认目录为"output/web_save_tool/"，每一个项目起一个新的文件夹，文件夹名称为项目名称。

## 输出格式要求
完成信息收集和保存后，你的回复应该包含以下结构化信息：
- search_results: 执行的搜索操作和找到的信息概述
- file_saved: 保存的文件路径和基本信息
- content_summary: 保存内容的摘要说明
- sources_used: 使用的信息源列表
- success: 操作是否成功完成
- message: 关于整个过程的补充说明

## 注意事项
- 必须确保信息的准确性和完整性
- 保存的内容要结构清晰，便于阅读
- 当信息不够详细时，主动进行深度搜索
- 当你要输出很多内容并保存到文件时，请直接调用工具
"""
    
    # 分形智能体：调用其他智能体
    TOOLS = [
        ("../websearch/websearch_tool.py", "search_agent"),
        ("../file_io2/file_io.py", "file_io")
    ]
    
    MCP_SERVER_NAME = "web_save_tool"
    
    TOOL_DESCRIPTION = """
    Searches the web for information and saves the results to files with intelligent content organization.

This tool combines web search capabilities with file management to create a complete information gathering and storage workflow. It can search for current information, browse websites, and save organized content to files.

Input format:
- Natural language requests for information gathering and saving
- Can specify search topics, file formats, and organization requirements
- May include specific websites to search or file destinations
- Can request different levels of detail or specific information focus

Examples:
- "Search for the latest AI developments and save a summary to ai_trends.md"
- "Find information about sustainable energy and create a comprehensive report"
- "Research Python programming tutorials and save links and notes to a file"
- "Gather news about climate change and organize it into a structured document"
- "Search for travel information about Japan and save an itinerary file"

Features:
- Intelligent web search with follow-up browsing
- Automatic content organization and structuring
- File creation with appropriate formatting
- Multi-round search for comprehensive information gathering
- Content validation and quality assurance
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Web Save tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=20,  # Web search and save may require multiple rounds
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    WebSaveTool.main() 