"""
Visual Article Generator Tool - Unified Interface

This module provides a unified interface for visual article generation that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced visual article generation as MCP tools
2. Interactive mode: Runs as an interactive agent with visual article capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python visual_article_tool.py                        # MCP Server mode (default)
  python visual_article_tool.py --interactive          # Interactive mode
  python visual_article_tool.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class VisualArticleTool(ToolTemplate):
    """Visual article generator tool using ToolTemplate with fractal intelligence"""
    
    SYSTEM_PROMPT = """
你是一个图文并茂的文章生成智能体。

【严格约束】
❌ 绝对禁止：在对话中直接输出或显示任何文章内容
❌ 绝对禁止：使用代码块显示文章文本
✅ 必须执行：所有内容必须通过工具调用完成

【强制工具调用流程】
1. 规划文章结构（内部完成，不输出内容）
2. 对每个段落执行：
   a) 调用 file_manager_agent 写入段落内容到 article.md
      - 段落内容必须包含图片引用：![说明](images/sectionX-figY.png)
      - 内容不少于500字，结构清晰
      - 先预留图片位置，后生成图片
   b) 调用 image_creator_agent 生成对应插图
   c) 确认操作成功后继续下一段

【工具使用规范】
- file_manager_agent：专门用于文件写入操作
- image_creator_agent：专门用于图片生成操作

【文件路径规范】
- 文章路径：output/visual_article_generator/[项目名]/article.md
- 图片路径：output/visual_article_generator/[项目名]/images/sectionX-figY.png
- 图片引用：![说明](images/sectionX-figY.png)

【操作验证】
每次工具调用后必须确认：
- file_manager_agent：文件是否成功创建/写入
- image_creator_agent：图片是否成功生成

【错误处理】
如果工具调用失败：
1. 报告具体的工具和错误信息
2. 尝试修正参数
3. 重新调用相应工具

"""
    
    # 分形智能体：调用其他智能体
    TOOLS = [
        ("../file_io2/file_io.py", "file_manager_agent"),
        ("../gpt_imagen/server.py", "image_creator_agent")
    ]
    
    MCP_SERVER_NAME = "visual_article_tool"
    
    TOOL_DESCRIPTION = """
    Generates comprehensive visual articles with integrated text and images in Markdown format.

This tool creates complete articles by coordinating file operations and image generation. It writes structured Markdown content and automatically generates relevant images for each section, creating a cohesive visual narrative.

Input format:
- Natural language description of the article topic and requirements
- Can specify writing style, target audience, or content focus
- May include specific image requirements or visual themes
- Can request specific article structure or section organization

Returns:
- 'article_path': Path to the generated Markdown article
- 'images_generated': List of generated image files and their descriptions
- 'article_structure': Overview of the created content structure
- 'success': Boolean indicating successful article generation
- 'message': Additional information about the generation process

Examples:
- "Write a comprehensive article about renewable energy with illustrations"
- "Create a visual guide to machine learning concepts for beginners"
- "Generate an article about sustainable travel with scenic images"
- "Write a technical overview of blockchain technology with diagrams"
- "Create a lifestyle article about urban gardening with how-to images"

Features:
- Automatic image generation for each article section
- Structured Markdown formatting with proper headings
- Consistent file organization in project directories
- Image path validation and consistency checking
- Multi-section article workflow with visual coherence
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Visual Article tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=50,  # Visual article generation requires many steps
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    VisualArticleTool.main() 