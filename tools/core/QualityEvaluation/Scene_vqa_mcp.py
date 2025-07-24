import os
import yaml
import base64
from PIL import Image
import io
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
# 初始化MCP服务，名称可自定义
mcp = FastMCP("Scene_Evaluation_Vqa")


def normalize_path(path: str) -> str:
    """
    Normalize a file path by expanding ~ to user's home directory
    and resolving relative paths.
    
    Args:
        path: The input path to normalize
        
    Returns:
        The normalized absolute path
    """
    # Expand ~ to user's home directory
    expanded_path = os.path.expanduser(path)
    
    # Convert to absolute path if relative
    if not os.path.isabs(expanded_path):
        expanded_path = os.path.abspath(expanded_path)
        
    return expanded_path

def encode_image(image: Image.Image, size: tuple[int, int] = (512, 512)) -> str:
    image.thumbnail(size)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return base64_image

def load_image(image_path: str, size_limit: tuple[int, int] = (512, 512)) -> tuple[str, dict]:
    """Load an image from the given path.
    
    Args:
        image_path: Path to the image file to load
        
    Returns:
        A tuple containing:
            - Base64 encoded string of the resized image (max 512x512) (this can be put in the image_url field of the user message)
            - Dictionary with metadata including original width and height
    """
    meta_info = {}
    image = Image.open(image_path)
    meta_info['width'], meta_info['height'] = image.size
    base64_image = encode_image(image, size_limit)
    return base64_image, meta_info

@mcp.tool()
async def Scene_Evaluation_Vqa(image_path: str, prompt: str) -> str:
    '''
    该工具用于评估生成场景与输入文本描述之间的匹配程度，聚焦五个方面：
    1. 对象计数：检查场景中对象数量是否符合文本描述要求，报告满足规格的百分比。
    2. 对象属性：验证场景中对象属性（如颜色、材质、尺寸）与描述一致性，通过图像对比和VLM评估属性符合度。
    3. 对象-对象关系：分析场景中对象间空间关系（如相邻、面对），检查是否符合文本描述。
    4. 对象架构关系：评估对象与建筑元素的空间关系（如靠墙、悬挂），确保布局符合描述要求。
    5. 文本场景描述一致性：以script_generation_agent生成的空间描述文本为基准，逐条核查场景图像与描述内容（空间功能、风格、用户画像、尺寸、层高、采光、主色调、结构分布、家具概况、风格亮点等）的一致性。

    Args:
        image_path (str): 场景渲染图像文件路径，需为有效的PNG/JPG图片。
        prompt (str): 场景文本描述，建议为script_generation_agent生成的空间描述内容。可参考如下提问样例：
            - "请逐条核查以下空间描述与场景图像的一致性：\n1. 物体数量、尺寸、颜色、材质符合文本描述\n2. 物体关系和布局符合文本描述\n3. 全局风格包括空间功能、结构分布、家具概况、风格亮点符合文本描述"

    Returns:
        str: Dict格式结构化评估结果，answer字段包含对象计数、对象属性、对象-对象关系、对象架构关系、文本场景描述一致性五个维度的结论，success为操作状态。
    '''
    image_path = normalize_path(image_path)
    base64_image, meta_info = load_image(image_path, (512, 512))
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key=os.getenv('QWEN_API_KEY'),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    completion = client.chat.completions.create(
        model="qwen-vl-max",  # 此处以qwen-vl-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages=[{"role": "user","content": [
                {"type": "text","text": prompt},
                {"type": "image_url",
                "image_url": {"url": f'data:image/png;base64,{base64_image}'}}
                ]}]
    )
    model_output = completion.choices[0].message.content
    return completion.choices[0].message.content


if __name__ == "__main__":
    mcp.run(transport='stdio')