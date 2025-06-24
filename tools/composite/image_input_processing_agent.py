import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class ImageInputProcessingAgent(ToolTemplate):
    """Image Input Processing Agent using ToolTemplate"""

    SYSTEM_PROMPT = """
你是一名室内场景解析专家。目标：基于输入的图像，输出 JSON，包括
1）scene_style：整体风格的描述；
2）objects：数组，每个对象字段如下
    {
    "id": "sofa_L1",
    "category": "sofa",
    "position": { "x": 1.2, "y": 3.0, "z": 0.425 },   /* 物体几何中心 */
    "size":     { "length": 2.2, "width": 0.9, "height": 0.85 },
    "rotation": { "yaw": 90 },                      /* 仅水平旋转 */
    "description": "", /*包含风格、形态等*/
    "image_reference": "" /*参考图像地址*/
    }

# 分层流程
## 阶段1：VQA 全局 → 获取 scene_style
## 阶段2：detect_and_crop_objects → 得到每个 bbox / crop_path / category
## 阶段3：遍历 detections
   - 计算中心点与尺寸
   - 对 crop_path 做 VQA：获取 description / 如果需要推断朝向获取 yaw
   - 组装对象字段
## 阶段4：输出 JSON，其中 objects 只输出置信度大于0.3的对象
"""

    TOOLS = [ ("tools/composite/deep_visual_reasoning_agent.py", "multimodal_deep_visual_reasoning_tool")]

    MCP_SERVER_NAME = "image_input_processing_tool"

    TOOL_DESCRIPTION = """
    解析输入图像，输出室内场景风格和所有主要对象的详细信息。

    参数:
        query: str - 图像路径，以及可选的额外说明（如“请分析此卧室的风格和主要物品”）

    返回:
        str - JSON 字符串，包含：
            - scene_style: 场景整体风格的自然语言描述
            - objects: 主要对象数组，每个对象包含类别、中心点、尺寸、朝向、简要描述、裁剪图像路径等字段

    工作流程:
        1. 首先通过视觉问答（VQA）分析整体场景风格
        2. 检测并裁剪所有主要对象，获取每个对象的类别、位置、尺寸等
        3. 对每个对象裁剪图像进行进一步分析，补充描述和朝向信息
        4. 仅输出置信度大于0.3的对象
        5. 最终输出结构化 JSON，便于后续智能体理解和处理

    注意事项:
        - 支持多种室内场景类型（如卧室、客厅、厨房等）
        - 仅需提供原始图像路径，工具会自动完成分层推理和对象分析
        - 输出结果适合用于下游空间理解、三维重建、家居推荐等任务
"""

    @classmethod
    def create_config(cls):
        """Custom configuration for Image Input Processing tool"""
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
    ImageInputProcessingAgent.main() 