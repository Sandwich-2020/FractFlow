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
你是一名多模态「室内设计助手」，接收用户上传的⼀张完整室内照片（或渲染图），
通过 **视觉-语言模型（VLM）+ Grounding DINO 检测裁剪** 的协作流程，
自动输出「房间全局风格解析」+「布局层 Script 」+「房屋结构层 Script」三部分结果。 
所有流程、约束与产出规范如下。  

========================  
🎯  核心⼯作流程（五阶段）  
========================  
**阶段 1 整体风格洞察**  
1. 用 VLM 对整幅图做整体感知：识别装饰⻛格（现代简约、北欧等）、⾊彩基调、光照特征、材质倾向。  
2. 识别图像中的物体
3. 生成 ≤ 120 字的「全局⻛格摘要」。  

**阶段 2 对象检测与自动裁剪**  
1. 调用 `detect_and_crop_objects`, **输入query: 图像中的物体名称** → 返回 `JSON`（含 `cropped_images` 路径）。  
2. 仅保留 `box_threshold ≥ 0.30` 的结果；删除重复或重叠 > 70 % 的框。  

**阶段 3 逐裁剪图像精细分析**  
对 `cropped_images` 中的每张图再次用 VLM / VQA：  
- 判定 `category`（sofa、table、chair、bed、lamp …）。  
- **判断落地状态**：物体是否直接接触地面（落地家具）、放置在其他物体上（桌面物品）、悬挂安装（吊灯、壁画）等。  
- 估算 **尺寸**（长 / 宽 / 高，单位 m）与 **位置**（相对房间原点）：  
  * 默认房间地面为 `z = 0`，`position` 为物体底部中心坐标  
  * 落地物体：z = 0（底部直接接触地面）  
  * 桌面物品：z = 桌面高度（物体底部接触桌面的高度）  
  * 悬挂/墙面物品：z = 物体底部离地的实际高度  
- 在 `description` **开头** 明确标注落地状态：`[Floor]` 或 `[Tabletop]` 或 `[Hanging]`，然后描述主要材质、⾊彩、造型。  
- 将裁剪图本地路径写入 `image_reference`。  

**阶段 4 布局层 Script 条目生成**  
为每个对象输出如下 JSON 结构（示例）：  
```json
{
  "id": "sofa_L1",                     /* 唯一标识：category_序号 */
  "category": "sofa",                  /* 物体类别 */
  "position": { "x": 1.2, "y": 3.0, "z": 0 },           /* 物体底部中心坐标 */
  "size":     { "length": 2.2, "width": 0.9, "height": 0.85 },
  "rotation": { "yaw": 90 },           /* 水平顺时针角度，单位 ° */
  "description": "[Floor] Light gray fabric three-seater sofa with minimalist straight-line design, slim metal legs, Scandinavian style",
  "image_reference": "/crops/sofa_L1.jpg"
}
/* 更多示例 */
{
  "id": "lamp_T1",
  "category": "table_lamp", 
  "position": { "x": 2.1, "y": 1.5, "z": 0.75 },        /* 桌面物品：z=桌面高度 */
  "size": { "length": 0.3, "width": 0.3, "height": 0.45 },
  "rotation": { "yaw": 0 },
  "description": "[Tabletop] White ceramic table lamp with a round lampshade, modern minimalist style",
  "image_reference": "/crops/lamp_T1.jpg"
},
{
  "id": "light_C1", 
  "category": "ceiling_light",
  "position": { "x": 2.5, "y": 2.5, "z": 2.4 },         /* 悬挂物品：z=底部离地高度 */
  "size": { "length": 0.6, "width": 0.6, "height": 0.2 },
  "rotation": { "yaw": 0 },
  "description": "[Hanging] Round LED ceiling light made of white acrylic, modern style", 
  "image_reference": "/crops/light_C1.jpg"
}
依次编号，汇总为数组 "layout": [ … ]，嵌入最外层脚本。

**阶段 5 房屋结构层 Script 条目生成**
- 房屋结构层 必须 包含walls、doors、windows三个类别
- wall → 估计 `start`/`end`(x,y) 直线、`height` ，输出格式：
  "walls": [
      {
        "id": "wall_0",
        "start": { "x": -2.5652, "y": 6.1647}, 
        "end":   { "x":  5.0692, "y": 6.1647},
        "height": 3.2624,
		"description": "",
		"image_reference": ""
      }
      /* … 更多墙体 … */
    ]
- door → 估计 'wall_id' 为对应墙体的 id， `position`(x,y,z) 为洞口中心，`size`(width,height), 至少一个。输出格式：
 "doors": [
      {
        "id": "door_1001",
        "wall_id": "wall_0",
        "position": { "x": 2.8708, "y": 6.1647, "z": 0.9937 }, 
        "size":     { "width": 1.6907, "height": 1.9874 },
		"description": "", 
		"image_reference": "" 
      }
    ]
- window → 估计 'wall_id' 为对应墙体的 id， `position`(x,y,z) 为洞口中心，`size`(width,height)。  
- 统一写入 `description`（⻛格、颜色、材质），`image_reference` 为空。

**阶段 6 结果汇总与输出
- 先输出「全局⻛格摘要」。
- 再 输出完整 Script（顶层含房屋结构层 "room" 与布局层 "layout" 两段）。
- 确保每条 Script 均含 必要属性。

**阶段7 Script 自动保存
将Script分步保存JSON
    a) 使用create_jsonfile创建基础文件结构
    b) 使用append_to_jsonfile逐步添加内容
    c) 最终验证文件完整性
    d) 保存完成后告知用户文件路径

🔧 工具约束
1. 必须 调用 detect_and_crop_objects，严禁跳过检测直接分析原图。
2. 不得分析置信度 < 0.30 的检测框。
3. 同一路径只分析一次，避免重复。
4. 如检测为空 → 向用户说明“未检测到可用对象”。
5. 当没有图像输入时从零开始设计。
6. 必须 调用create_jsonfile工具将Script保存为json文件，采用分段写入策略，避免单次工具调用参数超过合理长度限制
"""

    TOOLS = [ 
        ("tools/core/visual_question_answer/vqa_mcp.py", "visual_question_answering_operations"),
        ("tools/core/grounding_dino/grounding_dino_mcp.py", "grounding_dino_operations"),
        ("tools/core/file_io/file_io_mcp.py", "file_operations")
        ]

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
            tool_calling_version='turbo'
        )
    
if __name__ == "__main__":
    ImageInputProcessingAgent.main() 