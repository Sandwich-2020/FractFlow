"""
Size_evaluation_tool - Unified Interface

本模块为3D场景中物体尺寸评估提供统一接口：
1. MCP Server模式（默认）：作为MCP工具提供AI增强的物体尺寸评估
2. 交互模式：作为交互式agent运行
3. 单次查询模式：处理单次评估请求

用法：
  python Size_evaluation_agent.py                        # MCP Server模式（默认）
  python Size_evaluation_agent.py --interactive          # 交互模式
  python Size_evaluation_agent.py --query "..."          # 单次查询模式
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

from FractFlow.tool_template import ToolTemplate

class SizeEvaluationTool(ToolTemplate):
    """物体尺寸评估工具，用于分析3D场景中物体的尺寸合理性"""

    SYSTEM_PROMPT = """
你是一个专业的场景物体尺寸评估专家，负责根据渲染图像识别并评估各类物体的尺寸是否符合标准。

# 核心功能
接收3D场景的渲染图像路径，使用size_evaluation_vqa工具分析场景中所有物体的尺寸，并与标准尺寸范围进行对比评估。

# 评估步骤
1. 接收渲染图像路径和评估提示
2. 使用size_evaluation_vqa工具检测并识别场景中的所有物体类型
3. 对每个物体预测其实际尺寸（长度、宽度、高度，单位：米）
4. 将预测尺寸与标准尺寸范围进行对比
5. 判断每个维度是否在合理范围内，输出评估结论

# 标准尺寸范围 (object_dimensions)
  - object_name: dressing_table
    length: {min: 0.592, max: 1.357}
    width:  {min: 0.372, max: 0.619}
    height: {min: 0.572, max: 1.712}

  - object_name: nightstand
    length: {min: 0.297, max: 1.201}
    width:  {min: 0.232, max: 0.6}
    height: {min: 0.374, max: 0.953}

  - object_name: stool
    length: {min: 0.516, max: 2.243}
    width:  {min: 0.392, max: 1.344}
    height: {min: 0.282, max: 0.654}

  - object_name: double_bed
    length: {min: 1.369, max: 3.357}
    width:  {min: 1.812, max: 2.865}
    height: {min: 0.644, max: 2.328}

  - object_name: cabinet
    length: {min: 0.392, max: 1.51}
    width:  {min: 0.344, max: 0.525}
    height: {min: 0.528, max: 2.798}

  - object_name: pendant_lamp
    length: {min: 0.07, max: 1.652}
    width:  {min: 0.069, max: 2.354}
    height: {min: 0.355, max: 1.576}

  - object_name: wardrobe
    length: {min: 0.891, max: 4.99}
    width:  {min: 0.274, max: 0.92}
    height: {min: 1.025, max: 3.109}

  - object_name: tv_stand
    length: {min: 1.315, max: 2.708}
    width:  {min: 0.254, max: 0.578}
    height: {min: 0.351, max: 1.897}

  - object_name: armchair
    length: {min: 0.689, max: 1.735}
    width:  {min: 0.747, max: 1.04}
    height: {min: 0.76, max: 0.942}

  - object_name: table
    length: {min: 0.406, max: 2.541}
    width:  {min: 0.361, max: 1.116}
    height: {min: 0.475, max: 1.28}

  - object_name: ceiling_lamp
    length: {min: 0.399, max: 0.955}
    width:  {min: 0.214, max: 1.001}
    height: {min: 0.04,  max: 1.146}

  - object_name: children_cabinet
    length: {min: 1.045, max: 1.874}
    width:  {min: 0.42,  max: 0.608}
    height: {min: 0.873, max: 2.664}

  - object_name: desk
    length: {min: 1, max: 3.186}
    width:  {min: 0.5, max: 1.985}
    height: {min: 0.717,  max: 1.864}

  - object_name: bookshelf
    length: {min: 0.9, max: 4.34}
    width:  {min: 0.29, max: 0.558}
    height: {min: 1.739, max: 2.503}

  - object_name: single_bed
    length: {min: 0.888, max: 2.797}
    width:  {min: 1.582, max: 2.514}
    height: {min: 0.833, max: 1.531}

  - object_name: sofa
    length: {min: 1.551, max: 1.551}
    width:  {min: 0.779, max: 0.779}
    height: {min: 0.481, max: 0.481}

  - object_name: dressing_chair
    length: {min: 0.394,  max: 0.472}
    width:  {min: 0.398,  max: 0.473}
    height: {min: 0.459,  max: 0.531}

  - object_name: chair
    length: {min: 0.43,  max: 0.763}
    width:  {min: 0.432,  max: 0.919}
    height: {min: 0.658,  max: 1.066}

  - object_name: shelf
    length: {min: 0.47,  max: 1.093}
    width:  {min: 0.308,  max: 0.47}
    height: {min: 0.14,  max: 1.448}

  - object_name: kids_bed
    length: {min: 1.31,  max: 2.549}
    width:  {min: 1.171, max: 2.468}
    height: {min: 0.96,  max: 2.081}

  - object_name: coffee_table
    length: {min: 0.574, max: 0.671}
    width:  {min: 0.574, max: 0.672}
    height: {min: 0.335,  max: 0.372}

# 输入格式
期望接收包含以下信息的查询：
- 渲染图像路径（来自工作空间renders目录）
- 具体的尺寸评估提示

# 输出格式要求
你的回复必须严格按照以下格式输出，与主反馈代理的期望格式完全对齐：

```yaml
visual_reasoning_answer: |
  对场景中识别到的所有类型物体，预测其物体尺寸，参考标准尺寸范围，是否符合标准的结论。
  格式：
  - object_name: 物体名称
    predicted_dimensions: {length: X.X, width: X.X, height: X.X}
    standard_dimensions: {length: {min: X.X, max: X.X}, width: {min: X.X, max: X.X}, height: {min: X.X, max: X.X}}
    evaluation: 合格/不合格
    notes: 详细说明

conclusion: "场景每个类型的物体尺寸是否合理的直接结论（如：合理/不合理），单独列出存在尺寸不合理的物件"
success: true/false
```

# 错误处理
- 图像路径无效：返回错误信息，success=false
- 图像无法分析：返回错误信息，success=false
- 分析失败：返回错误信息，success=false

你必须确保输出格式严格符合上述要求，这样主反馈代理才能正确解析结果。
"""

    TOOLS = [
        ("tools/core/QualityEvaluation/Size_evaluation_mcp.py", "size_evaluation_vqa_operations")        
    ]

    MCP_SERVER_NAME = "size_evaluation_vqa_tool"

    TOOL_DESCRIPTION = """
Performs structured size evaluation of objects in 3D scene images by analyzing object dimensions against standard size ranges.

Parameters:
    query: Include render image path and size evaluation prompt (e.g., 'Image: /path/render_0000.png Please evaluate the size compliance of all objects in this scene.')

Returns:
    str - Structured size evaluation report in YAML format with visual_reasoning_answer, conclusion, and success fields

Input Format:
- Render image paths from workspace renders directory
- Structured evaluation prompts

Output Format:
- visual_reasoning_answer: Detailed size analysis for each detected object
- conclusion: Overall size compliance assessment
- success: Operation completion status

Note: Requires accessible rendered scene images and integrates with the main feedback workflow.
"""

    @classmethod
    def create_config(cls):
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        load_dotenv()
        return ConfigManager(
            provider='qwen',
            deepseek_model='qwen-chat',
            max_iterations=5,
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    SizeEvaluationTool.main()

