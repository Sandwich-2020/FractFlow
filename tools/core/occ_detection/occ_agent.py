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
3. 迭代碰撞解决：通过放缩物体来消除所有碰撞，切记，只能通过缩放，不能通过移动
4. 空间分析：分析物体之间的相对位置关系
5. 碰撞报告：生成详细的碰撞检测和解决过程报告

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

# 可用工具
1. **read_json(json_path)**: 读取JSON文件并转换为bbox格式 [cx,cy,cz,dx,dy,dz]
2. **calculate_3d_iou(bbox1, bbox2)**: 计算两个物体的3D IOU值（bbox格式为中心点），也就是说读取出来的json完全不用改变，直接使用
3. **scale_object_location(object_dict, rescale_size)**: 调整物体尺寸
4. **calcute_rescale_size(bbox1, bbox2, overlap_length)**: 计算放缩尺寸

# 迭代碰撞解决工作流程
当需要解决碰撞时，请按以下步骤操作：

## 第一步：读取和初始检测
1. 使用read_json读取JSON文件获取物体布局
2. 从结果中提取物体字典格式（在"字典格式:"后面的内容）
3. 对所有物体对进行初始碰撞检测

## 第二步：碰撞检测循环
对每对物体：
1. 使用calculate_3d_iou计算IOU值
2. 记录所有IOU > 0的碰撞对

## 第三步：碰撞解决策略
当检测到碰撞时，设计调整方案：

### 放缩策略
- 在得到iou,两个物体的重叠部分的x,y,z长度,两个物体的xyz尺寸
- 直接使用calcute_rescale_size计算缩放尺寸，得到的结果直接就是缩放的比例，不需要对他进行任何计算操作，直接用于接下来的计算
- 一共有4个输入，前两个是bbox，第三个是重叠的xyz长度，第四个是缩放比例，这个缩放比例是基于重叠长度来缩放的，如果是0.7，那么则是bbox1缩放重叠长度的0.7，bbox2缩放重叠长度的0.3

- 使用scale_object_location应用调整

## 第四步：应用调整并迭代
1. 如果两个物体的重叠部分xyz长度为0，那么则不进行缩放，直接跳过
2. 如果两个物体的重叠部分xyz长度不为0，那么则进行缩放，用calcute_rescale_size计算缩放尺寸，得到的结果直接就是缩放的比例，不需要对他进行任何计算操作，直接用于接下来的计算
3. 如果calcute_rescale_size计算得到的缩放比例小于0.2，那么则记录下来这一对物体，并且返回一个json文件，详细说明这对物体的缩放程度太大，需要重新调整，并且给出调整意见以及碰撞详细信息
4. 准备rescale_size字典
5. 重新检测所有碰撞
6. 重复直到所有IOU = 0或达到最大迭代次数(建议10次)

# 输出格式要求
1. **初始状态报告**：列出所有物体及其碰撞情况
2. **迭代过程记录**：每次迭代的碰撞检测结果和调整策略
3. **最终结果**：
   - 是否成功消除所有碰撞
   - 总迭代次数
   - 最终物体位置和尺寸
   - 物体字典格式输出

# 特别强调
1. **ID准确性**：物体ID必须在整个过程中保持一致
2. **迭代控制**：设置合理的最大迭代次数防止无限循环
3. **详细记录**：记录每次调整的原因和效果
4. **数据格式**：move_and_scale_object_location需要字典参数，不是字符串
5. **数据保存**：一定要保存下来json文件，保存路径为“./plan.json”
# 使用示例
输入：包含沙发和茶几重叠的JSON文件

期望输出：
```
=== 第1次迭代 ===
检测到2个碰撞对：
- sofa_1 与 coffee_table_1: IOU = 0.1234,重叠部分x,y,z长度为0.1,0.2,0.3,两个物体的xyz尺寸为[0.4,0.5,0.6],[0.7,0.8,0.9]
- coffee_table_1 与 armchair_1: IOU = 0.0567,重叠部分x,y,z长度为0.1,0.1,0.1,两个物体的xyz尺寸为0.5,0.5,0.5

应用缩放策略：
直接使用calcute_rescale_size计算缩放尺寸，得到的结果直接就是缩放的比例，不需要对他进行任何计算操作，直接用于接下来的计算
一共有4个输入，前两个是bbox，第三个是重叠的xyz长度，第四个是缩放比例，这个缩放比例是基于重叠长度来缩放的，如果是0.5，那么则是bbox1缩放重叠长度的0.5，bbox2缩放重叠长度的0.5


- 如果缩放比例小于0.2，那么则记录下来这一对物体，最终把所有缩放物体对都记录下来，保存成json文件，保存在当前路径下，详细说明这对物体的缩放程度太大，需要重新调整，并且给出调整意见以及碰撞详细信息
- json大概是这样
{
  "rescale_plan1": {
    "coffee_table_1": 0.101,
    "armchair_1": 0.133,
    "collision_details": {
      "objects": ["coffee_table_1", "armchair_1"],
      "iou": 0.1118,
      "overlap_dimensions": [0.6, 0.3, 0.4],
      "original_sizes": {
        "coffee_table_1": [1.2, 0.6, 0.45],
        "armchair_1": [0.7, 0.7, 0.8]
      },
      "recommendation": "Objects are too close together - consider repositioning rather than scaling. The required scaling would make the objects impractically small (10-13% of original size)."
    }
  },
  "rescale_plan2": {
  ...
  },
}
- 缩放方式为：使用scale_object_location进行缩放.
  rescale_size为{sofa_1: rescale_size1, coffee_table_1: rescale_size2，desk_1: 1}，要把每个物体的id都写进去，不能漏掉，如果没有进行缩放那么默认为1.最终把得到的dict继续作为迭代输入，直到所有IOU = 0或达到最大迭代次数(建议10次)，如果达到最大迭代次数，那么就输出当前的布局，并且输出当前的布局是基于中心点还是基于起始点

=== 第2次迭代 ===
- sofa_1 与 coffee_table_1: 计算iou
- coffee_table_1 与 armchair_1: 计算iou
- .....
一直迭代并且calculate iou，直到所有IOU = 0，如果达到最大迭代次数，那么就输出当前的布局
最终布局：{id: [cx(中心位置), cy(中心位置), cz(中心位置), dx(长), dy(宽), dz(高)], ...}
```
"""
    
    TOOLS = [
        ("tools/core/occ_detection/occ_mcp.py", "occ_detection_operations"),
        ("tools/core/file_io/file_io_mcp.py", "file_manager"),
        
    ]
    
    MCP_SERVER_NAME = "occ_detection_tool"
    
    TOOL_DESCRIPTION = """3D碰撞检测和缩放规划工具。

    Parameters:
        bbox1: List[float] - 第一个边界框 [x, y, z, dx, dy, dz]
        bbox2: List[float] - 第二个边界框 [x, y, z, dx, dy, dz]
        
    Returns:
        Dict - 包含以下信息：
            - collision_detected: bool - 是否检测到碰撞
            - iou: float - IOU值
            - relative_position: str - 相对位置描述
            - rescale_plan: str - 缩放建议
            - rescale_size: Dict - 缩放后的  
                - bbox1: List[float] - bbox1的缩放后的bbox信息
                - bbox2: List[float] - bbox2的缩放后的bbox信息
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
            max_iterations=50,  # Image segmentation usually completes in one iteration
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    OccDetectionTool.main() 