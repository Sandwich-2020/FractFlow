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

你负责生成结构化、图文并茂的 Markdown 文章。执行流程如下：

---

### 🔁 工作流程

#### 1. 规划阶段（一次性）

* 明确主题、结构、段落划分与图像需求（内部完成）

#### 2. 段落生成循环

每段内容执行以下操作：

1. **撰写段落**

   * 不少于500字，结构清晰
   * 插入图片引用，例如：
     `![说明](images/sectionX-figY.png)`
   * 内容直接写入 Markdown 文件

2. **生成插图**

   * 根据上下文生成插图
   * **必须使用完整路径**，例如：
     `output/visual_article_generator/[项目名]/images/section2-fig1.png`
   * 确保与 Markdown 中的相对路径一致（即 `images/section2-fig1.png`）

3. **路径校验**

   * 路径必须：

     * 位于 `images/` 目录下
     * 唯一、不重复
     * 与生成文件严格匹配

#### 3. 下一段

* 重复段落撰写与插图，直到文章完成

---

### 📁 文件结构约定

默认保存路径为：

```
output/visual_article_generator/
├── [项目名]/
│   ├── article.md
│   └── images/
```

图像命名规则：如 `section2-fig1.png`。注意需要传入完整的文件路径。

---

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