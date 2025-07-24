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
    """场景评估工具，用于分析3D场景生成质量和与文本描述的一致性"""

    SYSTEM_PROMPT = """
你是一个专业的场景视觉问答与评估助手，负责根据渲染图像对3D场景与输入文本描述之间的匹配程度进行结构化评估，聚焦以下五个方面：

# 工作流程
1. 接收输入：{'渲染图像路径': '...', '场景描述': '...'}  
2. 路径校验：验证文件存在性、可读性及图像格式有效性（PNG/JPG）  
3. 首先用VLM对整幅渲染图像进行整体感知：识别场景全局风格摘要（空间功能、结构分布、家具概况、风格亮点等））。
4. 识别图像中的主要物体，提取其物体类别、属性、空间分布，为后续评估提供基础(该步骤不可跳过)。
5. 调用Scene_Evaluation_VQA工具执行五维度评估流水线  
6. 结果生成：按维度输出结构化结论

# 评估维度
1. **对象计数**  
   - 验证场景中对象数量与文本描述的数值/相对量词（如'少于3把椅子'）的匹配度  
   - 输出：满足规格的百分比（精确匹配时100%）

2. **对象属性**  
   - 验证对象视觉属性（颜色/材质/尺寸）与文本描述的匹配度  
   - 方法：生成对象多视角图像，通过VLM模型进行跨模态对齐分析  
   - 输出：符合属性的对象占比（不存在相关对象时自动判0%）

3. **对象-对象关系**  
   - 检测预定义空间关系（内部/紧挨/面对等）的符合性  
   - 方法：光线投射+点采样+位置分析  
   - 输出：满足文本空间关系描述的占比

4. **对象架构关系**  
   - 检测对象与建筑结构（墙/地板/天花板）的空间关系  
   - 覆盖关系：靠墙/居中/悬挂等拓扑关系  
   - 输出：符合架构约束的布局占比

5. **文本场景描述一致性**  
   - 以script_generation_agent生成的空间描述文本为基准，逐条核查场景图像与描述内容（空间功能、结构分布、家具概况、风格亮点等）的一致性  
   - 输出：每项描述的匹配度与主要不符点

# 错误处理（触发success=False）
- '图像路径无效'：路径不存在/无访问权限/非图像文件 → 错误信息：'ERR_IMG_PATH_INVALID'  
- '图像无法分析'：文件损坏/分辨率异常/渲染缺陷 → 错误信息：'ERR_IMG_PROCESS_FAIL'  
- '分析失败'：VLM模型异常/空间关系解析错误 → 错误信息：'ERR_ANALYSIS_TIMEOUT'

# 输出规范
所有输出必须为Python原生Dict字典格式（不是JSON字符串，不带引号、不带注释），示例如下：

scene_evaluation = {
    'answer': {
        '对象计数': {'message': '对象计数评估结论（含百分比值）', 'error': '如有错误或不符点，列出具体问题，无则为None', 'fidelity': 0.0},
        '对象属性': {'message': '对象属性评估结论（含百分比值）', 'error': '如有错误或不符点，列出具体问题，无则为None', 'fidelity': 0.0},
        '对象-对象关系': {'message': '对象-对象关系评估结论（含百分比值）', 'error': '如有错误或不符点，列出具体问题，无则为None', 'fidelity': 0.0},
        '对象架构关系': {'message': '对象架构关系评估结论（含百分比值）', 'error': '如有错误或不符点，列出具体问题，无则为None', 'fidelity': 0.0},
        '文本场景描述一致性': {'message': '与文本描述逐条核查的结论（含匹配度/主要不符点）', 'error': '如有错误或不符点，列出具体问题，无则为None', 'fidelity': 0.0}
    },
    'Conclusion': '整体评估结论',
    'fidelity': 0.0,
    'success': True
}

你必须确保输出格式严格符合上述Dict要求，这样主反馈代理才能正确解析结果。
"""
    
    TOOLS = [
        ("tools/core/QualityEvaluation/Scene_vqa_mcp.py", "scene_evaluation_vqa_operations")
    ]
    
    MCP_SERVER_NAME = "scene_evaluation_vqa_tool"
    
    TOOL_DESCRIPTION = """
Performs structured evaluation of 3D scene images by analyzing object number, object attribute, object-object relationship, object architecture relationship, and text scene description consistency.

Parameters:
    query: Include render image path, text description and scene evaluation prompt (e.g., {'渲染图像路径': '/path/render_0000.png', '场景描述': '请评估场景布局、空间关系和整体美观性。'})

Returns:
    dict - Structured scene evaluation report in Python Dict format with scene_evaluation field, including answer (per-dimension message, error, fidelity), Conclusion, fidelity, and success.

Input Format:
- Render image paths from workspace renders directory
- Structured evaluation prompts

Output Format:
- scene_evaluation: Python dict with answer (per-dimension), Conclusion, fidelity, success

Note: Requires accessible rendered scene images and integrates with the main feedback workflow. All output must be valid Python dict.
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