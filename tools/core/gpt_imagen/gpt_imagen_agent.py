"""
GPT Image Generation Tool - Unified Interface

This module provides a unified interface for GPT image generation and editing that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced image operations as MCP tools
2. Interactive mode: Runs as an interactive agent with image capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python gpt_imagen_tool.py                        # MCP Server mode (default)
  python gpt_imagen_tool.py --interactive          # Interactive mode
  python gpt_imagen_tool.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class GPTImagenTool(ToolTemplate):
    """GPT image generation and editing tool using ToolTemplate"""
    
    SYSTEM_PROMPT = """
你是一个专业的AI图像生成和编辑助手，使用GPT的图像能力帮助用户创建和修改图像。

# 可用工具选择指南
1. edit_image_with_gpt - 基于现有图像进行编辑和合并，需要参考图像输入
2. create_image_with_gpt - 从零开始生成全新图像，仅需文本描述

# 工具选择策略
- 当用户提供参考图像时：使用edit_image_with_gpt
- 当用户要求修改或合并现有图像时：使用edit_image_with_gpt  
- 当用户需要完全原创的艺术作品时：使用create_image_with_gpt
- 当仅有风格/主题描述但无具体图像时：使用create_image_with_gpt

# 常见工作流程
1. 图像编辑请求：验证图像路径 → 明确修改指令 → 使用edit_image_with_gpt
2. 新图像创建：完善提示词 → 添加风格描述符 → 使用create_image_with_gpt
3. 混合请求：先编辑参考图像 → 再创建补充元素 → 根据需要组合结果

# 错误处理策略
- 图像路径无效：请求正确路径并验证文件权限
- 提示词过于模糊：询问具体细节和风格偏好
- 生成失败：简化提示词，减少参考图像数量，验证模型可用性

# 输出格式要求
你的回复应该包含以下结构化信息：
- image_url: 生成的图像URL或路径
- prompt_used: 实际使用的提示词
- style: 检测到或应用的艺术风格
- resolution: 图像尺寸（宽x高像素）
- success: 操作是否成功完成
- message: 关于生成过程的补充信息

# 最佳实践
1. 生成前确认保存路径存在
2. 复杂请求分解为多个步骤
3. 保持原图特征（除非明确要求修改）
4. 设定合理的生成期望
5. 在回复中包含保存的图像路径
6. 提供相关的生成说明
7. 适时建议后续编辑选项
"""
    
    TOOLS = [
        ("server.py", "gpt_image_generator_operations")
    ]
    
    MCP_SERVER_NAME = "gpt_image_generator_tool"
    
    TOOL_DESCRIPTION = """Generates images from natural language descriptions using GPT models.
    
    Parameters:
        query: str - Natural language description of image to generate
        
    Returns:
        str - Generation result or error message
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for GPT Image tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,  # Image generation and editing
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    GPTImagenTool.main() 