"""
Deep Visual Reasoning Agent - Unified Interface

This module provides a unified interface for deep visual reasoning that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced deep visual analysis as MCP tools
2. Interactive mode: Runs as an interactive agent with deep visual reasoning capabilities
3. Single query mode: Processes a single query and exits

The agent implements a four-layer progressive analysis architecture:
- Perception Layer: Basic visual elements identification
- Comprehension Layer: Element relationships and scene understanding  
- Interpretation Layer: Emotional expression and symbolic meaning
- Insight Layer: Deep cultural and philosophical implications

Usage:
  python deep_visual_reasoning_agent.py                        # MCP Server mode (default)
  python deep_visual_reasoning_agent.py --interactive          # Interactive mode
  python deep_visual_reasoning_agent.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class DeepVisualReasoningAgent(ToolTemplate):
    """Deep visual reasoning tool using ToolTemplate with four-layer progressive analysis"""
    
    SYSTEM_PROMPT = """
你是一个深度视觉推理专家，通过注意力引导的动态聚焦进行图像分析。

工作方式：
1. 先进行全局观察，理解图像整体
2. 基于用户问题和图像特点，选择值得深入的聚焦点
3. 对每个聚焦点进行详细分析
4. 根据发现决定是否需要新的聚焦点
5. 当充分回答用户问题时自然结束

约束：
❌ 禁止直接输出分析内容
✅ 必须通过VQA工具完成所有分析
✅ 展示完整推理过程和最终答案

每次VQA调用格式：
- 全局观察："请描述这张图像的整体内容、主要元素和基本特征"
- 聚焦分析："基于前面的观察[插入结果]，请深入分析[具体聚焦点]"
"""
    
    TOOLS = [
        ("tools/core/visual_question_answer/vqa_mcp.py", "visual_question_answering_operations")
    ]
    
    MCP_SERVER_NAME = "deep_visual_reasoning_tool"
    
    TOOL_DESCRIPTION = """
通过注意力引导的动态聚焦进行深度视觉推理。

输入格式：
"Image: /path/to/image.jpg [您的问题或分析需求]"

工作机制：
- 全局观察图像整体特征
- 动态选择聚焦点进行深入分析  
- 基于发现决定是否需要进一步聚焦
- 自适应控制分析深度

返回：
- 完整的推理过程轨迹
- 针对用户问题的直接答案
- 关键发现和洞察

适用场景：艺术作品、摄影作品、复杂场景等各类图像分析
"""
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Deep Visual Reasoning tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=15,  # Reduced to reasonable range for dynamic focusing
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    DeepVisualReasoningAgent.main() 