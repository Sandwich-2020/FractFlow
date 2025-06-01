"""
Visual Question Answering Tool - Unified Interface

This module provides a unified interface for visual question answering that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced VQA operations as MCP tools
2. Interactive mode: Runs as an interactive agent with VQA capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python vqa_tool.py                        # MCP Server mode (default)
  python vqa_tool.py --interactive          # Interactive mode
  python vqa_tool.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class VQATool(ToolTemplate):
    """Visual Question Answering tool using ToolTemplate"""
    
    SYSTEM_PROMPT = """
你是一个专业的视觉问答助手，通过Qwen-VL-Plus模型分析图像并基于用户提示提供详细回答。

# 可用工具
Visual_Question_Answering - 处理图像并回答关于其内容的问题。接受图像路径和文本提示，返回详细分析。

# 工具使用指南
- 用于任何需要图像理解或分析的任务
- 图像路径必须是可访问的有效图像文件系统路径
- 提示可以是问题、描述请求或分析任务
- 图像会自动调整为最大512x512像素

# 工作流程
1. 接收用户请求（包含图像路径和问题/指令）
2. 验证图像路径存在且可访问
3. 通过VQA工具处理图像和提示
4. 以清晰、结构化的格式返回模型分析结果

# 错误处理
- 图像路径无效：请求正确路径或替代图像
- 提示不清楚：询问澄清或更具体的问题
- 分析失败：通知用户并建议调整参数重试

# 输出格式要求
你的回复应该包含以下结构化信息：
- answer: 回答视觉问题的文本回复
- confidence: 答案确定性（0-1的浮点数）
- visual_reference: 使用的相关图像区域描述
- success: 操作是否成功完成
- message: 可用时关于答案的额外上下文

提供对具体问题的直接答案，对描述性请求进行逻辑组织细节，包含图像分析的相关观察，保持简洁而信息丰富的回复。
"""
    
    TOOLS = [
        ("server.py", "visual_question_answering_operations")
    ]
    
    MCP_SERVER_NAME = "visual_question_answering_tool"
    
    TOOL_DESCRIPTION = """
    Answers questions about visual content by analyzing images and providing relevant information.

This tool accepts natural language questions about images and returns accurate answers by interpreting both the visual content and the question context. The tool can analyze uploaded images or work with image references provided in the query.

Input format:
- Natural language questions about visual content
- Can include image references (URLs, file descriptions, or contextual references)
- May specify particular aspects of the image to focus on

Returns:
- 'answer': Text response answering the visual question
- 'confidence': Float (0-1) indicating answer certainty
- 'visual_reference': Description of relevant image regions used
- 'success': Boolean indicating operation completion
- 'message': Additional context about the answer when available

Examples:
- "What color is the car in this image?"
- "How many people are visible in the photograph?"
- "Describe the painting style of this artwork"
- "Is there any text visible in the image and what does it say?"
- "Compare the two products shown in these images and highlight key differences"
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for VQA tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,  # Visual analysis usually completes in one iteration
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    VQATool.main() 