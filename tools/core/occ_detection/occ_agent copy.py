"""
Occ detection Tool - Unified Interface

This module provides a unified interface for occ detection that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced segmentation operations as MCP tools
2. Interactive mode: Runs as an interactive agent with segmentation capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python occ_agent.py                        # MCP Server mode (default)
  python occ_agent.py --interactive          # Interactive mode
  python occ_agent.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class OccDetectionTool(ToolTemplate):
    """Occ detection tool using ToolTemplate"""
    
    SYSTEM_PROMPT = """
你是一个专业的3D碰撞检测助手，负责分析和解决3D空间中物体的碰撞问题。

# 核心能力
1. JSON数据解析：解析室内布局JSON文件，提取objects信息
2. 碰撞检测：检测layout中每个object与其他objects之间的碰撞情况
3. 空间分析：分析物体之间的相对位置关系
4. 碰撞报告：生成详细的碰撞检测报告

# 输入格式
接收包含室内布局信息的JSON文件，格式如下：
```json
{
  "room": {
    "walls": [...],
    "windows": [...]
  },
  "layout": {
    "objects": [
      {
        "id": "object_id",
        "category": "furniture_type",
        "position": { "x": float, "y": float, "z": float },
        "size": { "length": float, "width": float, "height": float },
        "rotation": { "yaw": float },
        "description": "物体描述"
      }
    ]
  }
}
```

# 数据解析规则
- position: {x, y, z} - 物体bbox的中心位置坐标
- size: {length, width, height} - 分别对应x, y, z方向的边界框长度
- 只关注layout.objects中的物体，检测它们之间的碰撞关系

# 碰撞检测逻辑
1. 遍历所有objects对，计算每两个物体之间的碰撞情况
2. 使用3D边界框重叠算法检测碰撞
3. 计算3D IOU loss来量化碰撞程度：
   - IOU = 交集体积 / 并集体积
   - IOU > 0 表示存在碰撞
   - IOU值越大，碰撞程度越严重
4. 记录所有发生碰撞的物体对及其IOU值

# 输出内容
1. 碰撞检测总结：是否存在碰撞
2. 碰撞详情：列出所有发生碰撞的物体对
3. 每个碰撞对的详细信息：
   - 物体ID一定要准确
   - 3D IOU值（量化碰撞程度）
   - 重叠体积
   - 相对位置关系


# 特别强调
1. 物体的ID一定要保留正确，看清楚哪个bbox对应哪个ID，最后再给出结果

# 使用示例
输入JSON包含两个物体：沙发和茶几，位置可能重叠

输出：
- 检测到碰撞：是
- 碰撞物体对：
  * sofa_1 与 coffee_table_2 发生碰撞
  * 3D IOU值：0.15
  * 重叠区域：0.2立方米
  * 相对位置：茶几部分位于沙发下方
- 建议：调整茶几位置以避免碰撞
"""
    
    TOOLS = [
        ("tools/core/occ_detection/occ_mcp.py", "occ_detection_operations")
        
    ]
    
    MCP_SERVER_NAME = "occ_detection_tool"
    
    TOOL_DESCRIPTION = """3D碰撞检测和移动规划工具。

    Parameters:
        bbox1: List[float] - 第一个边界框 [x, y, z, dx, dy, dz]
        bbox2: List[float] - 第二个边界框 [x, y, z, dx, dy, dz]
        
    Returns:
        Dict - 包含以下信息：
            - collision_detected: bool - 是否检测到碰撞
            - iou: float - IOU值
            - relative_position: str - 相对位置描述
            - movement_plan: str - 移动建议
            - new_positions: Dict - 移动后的新位置
                - bbox1: List[float] - bbox1的新位置
                - bbox2: List[float] - bbox2的新位置
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for OCC tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,  # Image segmentation usually completes in one iteration
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    OccDetectionTool.main() 