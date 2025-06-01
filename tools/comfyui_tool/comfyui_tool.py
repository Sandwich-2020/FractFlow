"""
ComfyUI Tool - Unified Interface

This module provides a unified interface for ComfyUI image generation that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced ComfyUI operations as MCP tools
2. Interactive mode: Runs as an interactive agent with ComfyUI capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python comfyui_tool.py                        # MCP Server mode (default)
  python comfyui_tool.py --interactive          # Interactive mode
  python comfyui_tool.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class ComfyUITool(ToolTemplate):
    """ComfyUI image generation tool using ToolTemplate"""
    
    SYSTEM_PROMPT = """
你是一个专门使用ComfyUI进行图像生成的AI助手。你的主要职责是通过有效利用可用工具并遵循最佳实践来帮助用户创建高质量图像。

# 可用工具
generate_image_with_comfyui - 基于文本提示使用SDXL-TURBO模型创建图像。关键参数：save_path（必需）、positive_prompt、negative_prompt、width、height、seed。注意：steps、cfg和checkpoint参数不应修改，因为它们已针对快速生成进行了优化。

# 工具选择指导
当用户请求图像生成时，始终使用generate_image_with_comfyui。对于不涉及图像创建的其他请求，直接回复而不使用工具。

# 标准工作流程
1. 接收带有可选参数的图像生成请求
2. 验证提供了必需的save_path
3. 为未指定的参数设置默认值（width=512, height=512, seed=0）
4. 使用优化的固定参数执行生成（steps=1, cfg=1）
5. 返回保存的图像路径

# 错误处理
- 如果缺少save_path：在继续之前请求此参数
- 如果生成失败：验证ComfyUI服务器正在运行并重试一次
- 对于无效路径：建议有效路径格式并重试
- 对于非英文提示：礼貌地请求英文文本输入

# 输出格式要求
你的回复应该包含以下结构化信息：
- image_url: 生成图像的URL（PNG格式）
- generation_parameters: 使用的参数字典（提示、种子、步数等）
- success: 表示生成是否成功的布尔值
- message: 附加信息或错误详情

# 重要规则
1. 永远不要修改steps、cfg或checkpoint参数
2. 生成前始终验证路径
3. 确保提示为英文
4. 返回生成图像的完整文件路径
5. 通过使用优化的默认设置保持快速响应时间

始终确认成功生成并提供准确的文件路径，包括简要的生成详情（尺寸、使用的种子），对于错误要清楚解释问题和所需的纠正措施。
"""
    
    TOOLS = [
        ("server.py", "comfyui_image_generator_operations")
    ]
    
    MCP_SERVER_NAME = "comfyui_image_generator_tool"
    
    TOOL_DESCRIPTION = """
    Generates images using ComfyUI based on natural language descriptions or style specifications.

This tool accepts text prompts describing desired images and returns generated images along with generation details. It supports various styles, compositions, and can incorporate specific artistic references.

Input format:
- Natural language description of desired image (required)
- Optional style specifications (e.g., "anime style", "photorealistic")
- Can include composition details (e.g., "centered portrait", "wide landscape")
- May reference specific artists or art styles
- Can specify image dimensions (e.g., "1024x768")

Returns:
- 'image_url': URL to generated image (PNG format)
- 'generation_parameters': Dictionary of parameters used (prompt, seed, steps, etc.)
- 'success': Boolean indicating generation success
- 'message': Additional information or error details

Examples:
- "A futuristic cityscape at night with neon lights, cyberpunk style"
- "Portrait of a warrior with golden armor, fantasy art style, 1024x1024"
- "Watercolor painting of autumn forest with vibrant colors"
- "Product photo of a modern smartphone on marble surface, studio lighting"
- "Character design sheet for a steampunk inventor, multiple poses"
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for ComfyUI tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,  # Image generation usually completes in one iteration
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    ComfyUITool.main() 