"""
scene_evaluation_vqa_tool - Unified Interface

本模块为3D场景评估提供统一接口：
1. MCP Server模式（默认）：作为MCP工具提供AI增强的场景质量评估
2. 交互模式：作为交互式agent运行
3. 单次查询模式：处理单次评估请求

用法：
  python scene_evaluation_tool.py                        # MCP Server模式（默认）
  python scene_evaluation_tool.py --interactive          # 交互模式
  python scene_evaluation_tool.py --query "..."          # 单次查询模式
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class SceneEvaluationTool(ToolTemplate):
    """场景评估工具，用于分析3D场景的整体质量和布局合理性"""

    SYSTEM_PROMPT = """
你是一个专业的场景视觉问答与评估助手，负责根据渲染图像对3D场景进行结构化评估，主要聚焦于场景空间布局、空间关系、场景风格方面。

# 核心功能
接收3D场景的渲染图像路径，使用scene_evaluation_vqa工具对场景图像进行结构化评估，提供全面的场景质量分析反馈。

# 工作流程
1. 接收渲染图像路径和评估提示
2. 验证图像路径的可用性与有效性
3. 使用Scene_Evaluation_VQA工具处理场景图像和提示，基于以下标准自动分析：
   - 场景空间布局合理性
   - 物体空间关系（如接近、碰撞、分离等）
   - 场景整体美观性和风格一致性
4. 结果输出：对场景空间布局、空间关系、场景风格给出详细判断和简要说明

# 评估维度
1. **物体位置合理性** - 物体摆放位置是否符合空间逻辑和功能需求
2. **物体空间关系** - 物体间距离、碰撞检测、相互关系的协调性
3. **场景整体布局** - 整体场景的完整性、美观性和风格统一性

# 输入格式
期望接收包含以下信息的查询：
- 渲染图像路径（来自工作空间renders目录）
- 具体的场景评估提示

# 输出格式要求
你的回复必须严格按照以下格式输出，与主反馈代理的期望格式完全对齐：

```yaml
answer: 
  - "针对场景空间布局的评估结论"
  - "针对物体空间关系的评估结论"
  - "针对场景整体美观性的评估结论"

visual_reference: 
  - "场景中支撑布局评估结论的关键区域或对象"
  - "场景中体现空间关系问题的具体位置"
  - "场景中影响美观性的关键元素"

success: true/false
```

# 错误处理
- 图像路径无效：返回错误信息，success=false
- 图像无法分析：返回错误信息，success=false
- 分析失败：返回错误信息，success=false

你必须确保输出格式严格符合上述要求，这样主反馈代理才能正确解析结果。
"""
    
    TOOLS = [
        ("tools/core/QualityEvaluation/QualityEvaluation/Scene_vqa_mcp.py", "scene_evaluation_vqa_operations")
    ]
    
    MCP_SERVER_NAME = "scene_evaluation_vqa_tool"
    
    TOOL_DESCRIPTION = """
Performs structured evaluation of 3D scene images by analyzing object placement, spatial relationships, and overall layout quality.
    
Parameters:
    query: Include render image path and scene evaluation prompt (e.g., "Image: /path/render_0000.png Please evaluate the scene layout, spatial relationships, and overall aesthetic quality.")
        
Returns:
    str - Structured scene evaluation report in YAML format with answer, visual_reference, and success fields
        
Input Format:
- Render image paths from workspace renders directory
- Structured evaluation prompts

Output Format:
- answer: List of evaluation conclusions for different scene aspects
- visual_reference: List of visual evidence supporting the conclusions
- success: Operation completion status

Note: Requires accessible rendered scene images and integrates with the main feedback workflow.
"""
    
    @classmethod
    def create_config(cls):
        """Custom configuration for the 3D scene evaluation VQA tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv

        load_dotenv()
        return ConfigManager(
            provider='qwen',
            deepseek_model='qwen-chat',
            max_iterations=5,  # Scene evaluation usually completes in one iteration
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    SceneEvaluationTool.main()