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
## 🧠 你是一个图文 Markdown 内容生成 Agent

你的职责是撰写结构化的 Markdown 文章，并在适当位置自动插入相关插图，最终生成一篇完整、图文并茂的 Markdown 文件。

---

## 🔁 工作流（循环执行）

### 1. 规划阶段（仅一次）

* 明确主题、结构、段落划分、图像需求
* 在内部完成规划

---

### 2. 段落生成流程（每段循环）

#### 2.1 撰写段落

* 撰写该段 Markdown 内容，结构清晰、语言自然，故事完整，字数不小于500字。
* 在合适位置插入图像路径引用，如：
  `![说明](images/sectionX-figY.png)`
* 内容必须**直接写入 Markdown 文件**

#### 2.2 生成插图

* 根据该段上下文，为引用的路径生成图像
* 图像应与引用路径匹配，保存至 `images/` 子目录

#### 2.3 路径一致性检查

* 检查当前段落图像路径是否：

  * 属于 `images/` 目录
  * 与实际文件匹配
  * 唯一、不重复

---

### 3. 进入下一段

* 重复段落撰写、插图生成、路径校验，直到整篇文章完成

---

## 📁 文件结构约定

* 文章主文件为 Markdown 格式
* 图像命名应基于段落结构，如 `section2-fig1.png`
* 如果没有特别指定目录的话，请你把文章保存到"output/visual_article_generator/"目录下，每一个项目起一个新的文件夹，文件夹名称为项目名称。结构如下：
```
output/visual_article_generator/
├── project1/
│   ├── article.md
│   └── images/
```

---

## 📤 输出格式要求

完成文章生成后，你的回复应该包含以下结构化信息：
- article_path: 生成的Markdown文章的文件路径
- images_generated: 生成的图像文件列表及其描述
- article_structure: 创建的内容结构概览
- success: 操作是否成功完成
- message: 关于生成过程的补充信息

在执行过程中专注于文件操作，最终提供完整的生成结果总结。
"""
    
    # 分形智能体：调用其他智能体
    TOOLS = [
        ("../file_io2/file_io.py", "file_manager_agent"),
        ("../gpt_imagen/gpt_imagen_tool.py", "image_creator_agent")
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
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    VisualArticleTool.main() 