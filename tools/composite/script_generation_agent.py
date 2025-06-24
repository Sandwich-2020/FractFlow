"""
Room Script Generation Agent

#  This agent helps architects or hobbyists design interior rooms. It accepts
#  TEXT descriptions, a SINGLE‑OBJECT image (e.g. a sofa) or a FULL‑ROOM photo
#  and returns:
#   1.  A rich natural‑language summary of the space.
#   2.  Cropped/segmented images of relevant elements (walls, doors, windows,
#       furniture) for downstream reference.
#   3.  A structured Scene‑Script file in the required JSON format and saves it
#       locally for further CAD / 3‑D use.

"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class ScriptGenerationAgent(ToolTemplate):
    """Multimodal room‑design agent with progressive perception‑to‑layout flow."""

    SYSTEM_PROMPT = """
Role: RoomLayoutGPT – 专产 JSON 场景脚本

要求：
• 2D 空间→ 3D JSON (room + layout)  
• 通道≥0.80 m，家具距≥0.30 m  
• 所有 description 写明风格/材质  
• 先生成200字以上中文描述，再基于这个描述输出唯一```json```代码块
• 利用file_operations保存json代码。块若没有指定路径，则将json代码块保存到当前工作路径下，并返回文件路径

工具流程：
一、如果没有图：
1. 解析用户输入文本需求，提取空间功能、风格、用户画像（如年龄）、特殊限制。
2. 生成空间描述：
   - 包含尺寸、层高、采光、主色调、结构分布、家具概况与风格亮点。
   - 校验空间合理性（通道 ≥ 0.8m、无重叠遮挡、尺度一致等）。
   - 若推断冲突，优先保持功能与安全，其次考虑风格一致性。
3. 3D JSON生成
二、如果有图
1. VQA_TOOL → 全局信息  
2. GROUNDING_DINO(conf>0.3) → 结构/家具检测  
3. 对裁剪图再 VQA_TOOL → 尺寸/旋转  
2. 生成空间描述：
   - 包含尺寸、层高、采光、主色调、结构分布、家具概况与风格亮点。
   - 校验空间合理性（通道 ≥ 0.8m、无重叠遮挡、尺度一致等）。
   - 若推断冲突，优先保持功能与安全，其次考虑风格一致性。
3. 3D JSON生成

3D JSON格式：
{
  /* ========== 1. 房间结构层 ========== */
  "room": {
    "walls": [
      /* 一面墙 = 起点/终点 + 高度（单位 m） */
      {
        "id": "wall_0",
        "start": { "x": -2.5652, "y": 6.1647},    /*表示墙面地面投影点 默认"z": 0.0*/
        "end":   { "x":  5.0692, "y": 6.1647},
        "height": 3.2624,
		"description": "", /*包含风格、形态等*/
		"image_reference": "" /*参考图像地址*/
      }
      /* … 更多墙体 … */
    ],

    "doors": [
      /* 门锚定在某面墙上，位置 = 洞口中心 */
      {
        "id": "door_1001",
        "wall_id": "wall_0",
        "position": { "x": 2.8708, "y": 6.1647, "z": 0.9937 }, /*中心点的坐标 绝对坐标 应该满足 2*z = height 即门底端位于地面 */
        "size":     { "width": 1.6907, "height": 1.9874 },
		"description": "", /*包含风格、形态等*/
		"image_reference": "" /*参考图像地址*/
      }
    ],

    "windows": [
      {
        "id": "window_2000",
        "wall_id": "wall_0",
        "position": { "x": 4.4478, "y": 6.1647, "z": 1.6448 }, /*中心点的坐标 绝对坐标*/
        "size":     { "width": 1.0080, "height": 2.1189 },
		"description": "", /*包含风格、形态等*/
		"image_reference": "" /*参考图像地址*/
      }
    ]
  },

  /* ========== 2. 布局层 ========== */
  "layout": {
    "objects": [
      {
        "id": "sofa_L1",
        "category": "sofa",
        "position": { "x": 1.2, "y": 3.0, "z": 0.425 },   /* 物体几何中心 */
        "size":     { "length": 2.2, "width": 0.9, "height": 0.85 },
        "rotation": { "yaw": 90 },                      /* 仅水平旋转 */
		"description": "", /*包含风格、形态等*/
		"image_reference": "" /*参考图像地址*/
      }
      /* … 更多物体 … */
    ]
  }
}

坐标：
• 原点=左下角，m，4小数  
• position = 物体几何中心

思考：
在脑中核对动线&尺寸→确保无冲突→生成
"""

    # ------------------------------------------------------------------
    # 2️⃣  TOOL REGISTRY – plug‑in adapters registered in FractFlow
    # ------------------------------------------------------------------
    TOOLS = [
        ("tools/core/visual_question_answer/vqa_mcp.py", "visual_question_answering_operations"),
        ("tools/core/grounding_dino/grounding_dino_mcp.py", "grounding_dino_operations"),
        ("tools/core/file_io/file_io_mcp.py", "file_operations")
    ]

    MCP_SERVER_NAME = "script_generation_tool"

    TOOL_DESCRIPTION = (
        "多模态房间设计助手，结合 VQA + 目标检测 + 语义分割，自动生成房间结构脚本。\n\n"
        "# 关键能力\n"
        "1. 功能与风格分析：根据年龄段/主题输出空间需求清单\n"
        "2. 构件检测与裁剪：自动提取 walls / doors / windows / furniture\n"
        "3. 元素参数化：尺寸、方位、风格标签\n"
        "4. Scene‑Script 生成：输出 JSON\n"
    )

    @classmethod
    def create_config(cls):
        """Custom configuration for Script Generation tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=20,  # Increased for multimodal tool coordination
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    ScriptGenerationAgent.main() 