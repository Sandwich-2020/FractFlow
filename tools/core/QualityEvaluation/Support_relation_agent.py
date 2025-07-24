"""
Support_relation_evaluation_tool - Unified Interface

本模块为3D场景中物体位置评估提供统一接口：
1. MCP Server模式（默认）：作为MCP工具提供AI增强的物体位置评估
2. 交互模式：作为交互式agent运行
3. 单次查询模式：处理单次评估请求

用法：
  python Support_relation_agent.py                        # MCP Server模式（默认）
  python Support_relation_agent.py --intractive          # 交互模式
  python Support_relation_agent.py --query path/to/scene.json  # 单次查询模式
"""

import os
import sys


# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)


# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class Support_relation_DetectionTool(ToolTemplate):
  """Support_relation_detection tool using ToolTemplate"""
  
  SYSTEM_PROMPT = """
你是一个专业的3D场景物理关系检测助手，负责分析和报告场景中物体的物理合理性问题。

# 核心能力
1. 支撑关系检测：推断每个物体的支撑对象（地面/墙体/其他物体），输出支撑类型与距离
2. 悬空检测：判断物体与地面距离是否超标，输出悬空物体及距离
3. 表面重叠检测：检测物体间2D/3D重叠，输出重叠物体对及重叠比例
4. 支撑错误检测：如支撑面积比例不合理、对墙面悬挂物体位置的合理性进行检测等
5. 物体与门窗重合检测：如物体与门或窗的2D投影重叠，输出type为‘overlap_door_window’；或物体与门距离过近，输出type为‘traffic_space_blocked’;或物体与窗距离过近，输出type为‘lighting_blocked’

# 可用工具
1.collect_all_bboxes：收集所有物体的bbox信息，包括2D和3D bbox（[]）。
2.initialize_support_relation：现在会判断每个物体的支撑对象，优先级为：地面>墙>其他物体>门>窗。
3.compute_physical_error：基于详细的支撑关系，检测物理合理性（悬空、弱支撑、重叠等），返回详细错误报告。
4.analyze_physical_relations：物理关系检测主函数，输入为场景布局JSON，输出详细物理错误报告（字典格式）。

# 输入格式
期望接收包含以下信息的查询：
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
  {
    "id": "sofa_L1",                     /* 唯一标识：category_序号 */
    "category": "sofa",                  /* 物体类别 */
    "position": { "x": 1.2, "y": 3.0, "z": 0 },           /* 物体底部中心坐标 */
    "size":     { "length": 2.2, "width": 0.9, "height": 0.85 },
    "rotation": { "yaw": 90 },           /* 水平顺时针角度，单位 ° */
    "description": "[Floor] Light gray fabric three-seater sofa with minimalist straight-line design, slim metal legs, Scandinavian style",
    "image_reference": "/crops/sofa_L1.jpg"
  }
}

# 数据解析规则
- position: {x, y, z} - 物体bbox的中心位置坐标，x,y中心点，z是底部最低点，也就是说这个xyz是底部中心点
- size: {length, width, height} - 分别对应x, y, z方向的边界框长度
- 只关注layout中的物体，检测物体和地面，其他物体，墙，门，窗的关系


# 工作流程
1. 用户输入 json_path，JSON 文件需包含 layout 字段，内含所有物体的 id、position、size 等信息。
2. 解析 JSON，提取物体列表，并调用collect_all_bboxes收集所有物体的bbox信息，包括2D和3D bbox。
3. 调用 initialize_support_relation，推断每个物体的支撑对象，输出 object_id、support_type、support_id、distance、intersect_ratio。
4. 基于支撑信息，调用 compute_physical_error，检测悬空、弱支撑、重叠等物理错误，输出详细错误列表
5. 汇总支撑信息与错误报告，生成结构化 Dict 字符串作为最终输出。


# 输出格式-Dict
support_info:
  - object_id: "sofa_L1"
    support: "floor"
    distance: 0.02
  # ... 其他物体
errors:
  floating:
    - object_id: "sofa_L1"
      type: "floating"
      desc: "sofa_L1 悬空 0.12m，未与地面接触"
      distance: 0.12
  floating_overlap_door_window:
    - object_id: "sofa_L1"
      type: "floating_overlap_door_window"
      desc: "悬空物体 sofa_L1 与门重合，位置不合理。"
  unsupported:
    - object_id: "light_C1"
      type: "unsupported"
      desc: "light_C1 离地过高，推断为靠墙支撑，需检查合理性"
      distance: 2.40
  intersect:
    - object_id: "sofa_L1|door_1"
      type: "overlap_door"
      desc: "sofa_L1 与门 door_1 重合，位置不合理。"
    - object_id: "sofa_L1|window_1"
      type: "overlap_window"
      desc: "sofa_L1 与窗 window_1 重合，位置不合理。"
summary:
  total_errors: 4
  floating: 1
  floating_overlap_door_window: 1
  unsupported: 1
  overlap_door: 1
  overlap_window: 1
  message: "共检测到4处物理关系异常。"
success: true/false

# 错误处理
- 输入文件无效或无法解析：返回{'success': False, 'error': ...}
- 检测流程异常：返回{'success': False, 'error': ...}

你必须确保输出格式严格为Python字典对象，便于主反馈代理自动解析。
"""
    
  TOOLS = [
      ("tools/core/QualityEvaluation/Support_relation_mcp.py", "Support_relation_detection"),
      ("tools/core/file_io/file_io_mcp.py", "file_manager"),
  ]
  
  MCP_SERVER_NAME = "Support_relation_Error_Detection_tool"
  
  TOOL_DESCRIPTION = """Analyzes the physical support relations and errors in a 3D scene layout described by a JSON file.

Parameters:
    json_path: str - Path to the scene layout JSON file. The file should contain a list of objects, each with unique id, position, and size.

Returns:
    dict - A detailed report as a Python dictionary, including support relations for each object (object_id, support_type, support_id, distance, intersect_ratio) and a list of detected physical errors (such as floating, unstable support, or 3D intersection).

Note: The tool checks for physical plausibility of object placement, including ground/object support, support stability, and intersection errors. The output is suitable for direct analysis or further processing by upper-level agents or users.
"""


  @classmethod
  def create_config(cls):
      """Custom configuration for Support_relation_Error_Detection tool"""
      from FractFlow.infra.config import ConfigManager
      from dotenv import load_dotenv
      
      load_dotenv()
      return ConfigManager(
          provider='deepseek',
          deepseek_model='deepseek-chat',
          max_iterations=5,  # Object detection usually completes in one iteration
          custom_system_prompt=cls.SYSTEM_PROMPT,
          tool_calling_version='stable'
      )

if __name__ == "__main__":
    Support_relation_DetectionTool.main() 
