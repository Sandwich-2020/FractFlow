"""
Position_evaluation_tool - Unified Interface

本模块为3D场景中物体位置评估提供统一接口：
1. MCP Server模式（默认）：作为MCP工具提供AI增强的物体位置评估
2. 交互模式：作为交互式agent运行
3. 单次查询模式：处理单次评估请求

用法：
  python Position_evaluation_agent.py                        # MCP Server模式（默认）
  python Position_evaluation_agent.py --interactive          # 交互模式
  python Position_evaluation_agent.py --query "..."          # 单次查询模式
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

from FractFlow.tool_template import ToolTemplate

class PositionEvaluationTool(ToolTemplate):
    """物体位置评估工具，用于分析3D场景中物体的位置合理性"""

    SYSTEM_PROMPT = """
你是一个专业的场景物体位置评估专家，负责根据渲染图像识别并评估各类物体的摆放位置是否符合标准。

# 核心功能
接收3D场景的渲染图像路径，使用Position_evaluation_vqa工具分析场景中所有物体的位置，并与标准位置范围进行对比评估。

# 评估步骤
1. 接收渲染图像路径和评估提示
2. 使用Position_evaluation_vqa工具检测并识别场景中的所有物体类型
3. 对每个物体预测其距离场景中心的实际距离（长度、宽度、高度方向，单位：米）
4. 将预测位置与标准位置范围进行对比
5. 判断每个维度是否在合理范围内，输出评估结论

# 标准位置距离范围 (Position_distance_range)
  - object_name: armchair
    length: {min: -1.449087693, max: 1.919713901}
    width:  {min: 0, max: 0}
    height: {min: -1.575757856, max: 1.461645213}
  - object_name: bookshelf
    length: {min: -2.117470509,  max: 1.324740008}
    width:  {min: 0,  max: 0}
    height: {min: -1.738045447,  max: 1.660109995}
  - object_name: cabinet
    length: {min: -2.451725,  max: 2.061420517}
    width:  {min: 0,  max: 0.0435}
    height: {min: -2.110018896,  max: 1.43243305}
  - object_name: ceiling_lamp
    length: {min: -1.851035,  max: 1.2319}
    width:  {min: 0,  max: 2.72992}
    height: {min: -0.4707,  max: 2.100005}
  - object_name: chair
    length: {min: -1.702724978,  max: 1.932991345}
    width:  {min: 0, max: 0}
    height: {min: -1.483033679,  max: 1.891674078}
  - object_name: children_cabinet
    length: {min: -1.196531109,  max: 0.611164582}
    width:  {min: 0,  max: 0}
    height: {min: -1.89235, max: 1.571673718}
  - object_name: coffee_table
    length: {min: -1.331863791,  max: 2.359426913}
    width:  {min: 0,  max: 0}
    height: {min: -0.33702033,  max: -0.155689225}
  - object_name: desk
    length: {min: -1.776584824,  max: 2.0023}
    width:  {min: 0,  max: 0}
    height: {min: -1.368891221, max: 1.712842222}
  - object_name: double_bed
    length: {min: -1.5401,  max: 1.469076804}
    width:  {min: 0,  max: 0.0646}
    height: {min: -1.213717231,  max: 1.3117}
  - object_name: dressing_chair
    length: {min: -0.4497171,  max: 1.340717821}
    width:  {min: 0,  max: 0}
    height: {min: -0.928590852,  max: 2.034738205}
  - object_name: dressing_table
    length: {min: -2.443814764,  max: 2.3937}
    width:  {min: 0,  max: 0}
    height: {min: -1.582423022,  max: 2.05689}
  - object_name: floor
    length: {min: -0.557372882,  max: 0.612969346}
    width:  {min: 0,  max: 0}
    height: {min: -0.484996791, max: 0.658324991}
  - object_name: kids_bed
    length: {min: -0.79835, max: 0.549715063}
    width:  {min: 0, avg: 0, max: 0}
    height: {min: -0.221561211,  max: 1.0022}
  - object_name: nightstand
    length: {min: -2.474678024,  max: 2.42579623}
    width:  {min: 0,  max: 0.0957}
    height: {min: -2.139630545,  max: 2.539}
  - object_name: pendant_lamp
    length: {min: -1.876506322,  max: 2.337375538}
    width:  {min: 1.0011,  max: 3.071804044}
    height: {min: -2.285245,  max: 1.96683}
  - object_name: shelf
    length: {min: -2.226176111,  max: 1.751050229}
    width:  {min: 0,  max: 0}
    height: {min: -1.536143791, max: 1.535129447}
  - object_name: single_bed
    length: {min: -1.14038,  max: 1.1803}
    width:  {min: 0,  max: 0}
    height: {min: -0.672189522,  max: 1.226558359}
  - object_name: sofa
    length: {min: 0.832855364,  max: 0.832855364}
    width:  {min: 0,  max: 0}
    height: {min: -0.690956242,  max: -0.690956242}
  - object_name: stool
    length: {min: -2.382575737,  max: 1.117765088}
    width:  {min: 0,  max: 0}
    height: {min: -1.79375882,  max: 0.710070615}
  - object_name: table
    length: {min: -2.203388068,  max: 1.8201}
    width:  {min: 0,  max: 0}
    height: {min: -2.102888879,  max: 1.744792849}
  - object_name: tv_stand
    length: {min: -1.6913,  max: 2.528}
    width:  {min: 0,  max: 0.0073}
    height: {min: -1.6522,  max: 1.547383885}
  - object_name: wardrobe
    length: {min: -2.55999224,  max: 2.212794159}
    width:  {min: 0,  max: 0}
    height: {min: -2.674480552,  max: 2.153236854}

# 输入格式
期望接收包含以下信息的查询：
- 渲染图像路径（来自工作空间renders目录）
- 具体的位置评估提示

# 输出格式要求
你的回复必须严格按照以下格式输出，与主反馈代理的期望格式完全对齐：

```yaml
visual_reasoning_answer: |
  对场景中识别到的所有类型物体，预测其物体位置，参考标准位置范围，是否符合标准的结论。
  格式：
  - object_name: 物体名称
    predicted_position: {length: X.X, width: X.X, height: X.X}
    standard_position: {length: {min: X.X, max: X.X}, width: {min: X.X, max: X.X}, height: {min: X.X, max: X.X}}
    evaluation: 合格/不合格
    notes: 详细说明

conclusion: "场景所有类型的物体位置是否合理的直接结论（如：合理/不合理），单独列出存在位置不合理的物件"
success: true/false
```

# 错误处理
- 图像路径无效：返回错误信息，success=false
- 图像无法分析：返回错误信息，success=false
- 分析失败：返回错误信息，success=false

你必须确保输出格式严格符合上述要求，这样主反馈代理才能正确解析结果。
"""

    TOOLS = [
        ("tools/core/QualityEvaluation/Position_evaluation_mcp.py", "Position_evaluation_vqa_operations")        
    ]

    MCP_SERVER_NAME = "Position_evaluation_vqa_tool"

    TOOL_DESCRIPTION = """
Performs structured position evaluation of objects in 3D scene images by analyzing object positions against standard position ranges.

Parameters:
    query: Include render image path and position evaluation prompt (e.g., 'Image: /path/render_0000.png Please evaluate the position compliance of all objects in this scene.')

Returns:
    str - Structured position evaluation report in YAML format with visual_reasoning_answer, conclusion, and success fields

Input Format:
- Render image paths from workspace renders directory
- Structured evaluation prompts

Output Format:
- visual_reasoning_answer: Detailed position analysis for each detected object
- conclusion: Overall position compliance assessment
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
    PositionEvaluationTool.main()
