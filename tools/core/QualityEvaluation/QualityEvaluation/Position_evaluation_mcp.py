import os
import yaml
import base64
from PIL import Image
import io
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
# 初始化MCP服务，名称为Position_Evaluation
mcp = FastMCP("Position_Evaluation_vqa")

def normalize_path(path: str) -> str:
    expanded_path = os.path.expanduser(path)
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
    meta_info = {}
    image = Image.open(image_path)
    meta_info['width'], meta_info['height'] = image.size
    base64_image = encode_image(image, size_limit)
    return base64_image, meta_info

@mcp.tool()
async def Position_Evaluation_Vqa(image_path: str, prompt: str) -> str:
    '''
    使用Qwen-VL-Plus模型对3D单物体渲染图进行多维度质量评估。
    Args:
        image_path (str): 3D物体渲染图像路径
        prompt (str): 文本评估提示，聚焦一致性、生成质量、功能性
    Returns:
        str: A detailed text response from the VLM model analyzing the image according to the prompt.
             The response format depends on the nature of the prompt.
    '''
    image_path = normalize_path(image_path)
    base64_image, meta_info = load_image(image_path, (512, 512))
    client = OpenAI(
        api_key=os.getenv('QWEN_API_KEY'),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    completion = client.chat.completions.create(
        model="qwen-vl-max",
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