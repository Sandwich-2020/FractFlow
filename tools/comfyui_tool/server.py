"""
ComfyUI Image Generator Tool Server

This module provides direct MCP tool implementations for the ComfyUI Image Generator tool.
These functions are designed to be exposed as MCP tools and used by the AI server.
"""

# Standard library imports
import os
import sys
from typing import Dict, Any, List, Optional

# MCP framework imports
from mcp.server.fastmcp import FastMCP

# Add current directory to Python path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Source-specific imports (generated based on source code analysis)
# 1. 源码特定导入部分
import websocket
import uuid
import json
import urllib.request
import urllib.parse
import base64
import io
import shutil
from PIL import Image
from dotenv import load_dotenv

# 2. 工具函数定义部分

# Initialize FastMCP server
mcp = FastMCP("comfyui_image_generator")

@mcp.tool()
async def tool_normalize_path(path: str) -> str:
    """
    Normalize a file path by expanding ~ to user's home directory and resolving relative paths.
    
    Args:
        path: The input path to normalize (can contain ~ or be relative)
        
    Returns:
        The normalized absolute path as string
    """
    expanded_path = os.path.expanduser(path)
    if not os.path.isabs(expanded_path):
        expanded_path = os.path.abspath(expanded_path)
    return expanded_path

@mcp.tool()
async def tool_queue_prompt(prompt: Dict[str, Any], client_id: str) -> Dict[str, Any]:
    """
    Queue a prompt for execution in ComfyUI and return the prompt ID.
    
    Args:
        prompt: The prompt workflow to execute (as dictionary)
        client_id: Unique client identifier for tracking
        
    Returns:
        Dictionary containing prompt_id of the queued prompt
    """
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{server_address}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

@mcp.tool()
async def tool_get_image(filename: str, subfolder: str, folder_type: str) -> bytes:
    """
    Retrieve an image from ComfyUI by its filename and location.
    
    Args:
        filename: Name of the image file
        subfolder: Subfolder where image is stored
        folder_type: Type of folder ('input' or 'output')
        
    Returns:
        Image data as bytes
    """
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"http://{server_address}/view?{url_values}") as response:
        return response.read()

@mcp.tool()
async def tool_get_history(prompt_id: str) -> Dict[str, Any]:
    """
    Get execution history for a specific prompt ID.
    
    Args:
        prompt_id: ID of the prompt to get history for
        
    Returns:
        Dictionary containing execution history and outputs
    """
    with urllib.request.urlopen(f"http://{server_address}/history/{prompt_id}") as response:
        return json.loads(response.read())

@mcp.tool()
async def tool_encode_image(image_data: bytes, size: tuple = (512, 512)) -> str:
    """
    Encode image data to base64 string with optional resizing.
    
    Args:
        image_data: Raw image bytes data
        size: Optional target size as (width, height) tuple
        
    Returns:
        Base64 encoded image string
    """
    image = Image.open(io.BytesIO(image_data))
    image.thumbnail(size)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

@mcp.tool()
async def tool_generate_image(
    save_path: str,
    positive_prompt: str = "masterpiece best quality",
    negative_prompt: str = "bad hands",
    width: int = 512,
    height: int = 512,
    seed: int = 0,
    steps: int = 1,
    cfg: float = 1,
    checkpoint: str = "SDXL-TURBO/sd_xl_turbo_1.0_fp16.safetensors"
) -> str:
    """
    Generate an image using ComfyUI with specified parameters and save to path.
    
    Args:
        save_path: Full path where image will be saved
        positive_prompt: Text prompt for desired image
        negative_prompt: Text prompt for undesired elements
        width: Image width in pixels
        height: Image height in pixels
        seed: Random seed for reproducibility
        steps: Number of sampling steps (keep as 1 for turbo models)
        cfg: Guidance scale (keep as 1 for turbo models)
        checkpoint: Model checkpoint name
        
    Returns:
        Path where the generated image was saved
    """
    save_path = await tool_normalize_path(save_path)
    is_file_path = os.path.splitext(save_path)[1] != ''
    
    if not is_file_path:
        os.makedirs(save_path, exist_ok=True)
    else:
        parent_dir = os.path.dirname(save_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
    
    prompt = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "cfg": cfg,
                "denoise": 1,
                "latent_image": ["5", 0],
                "model": ["4", 0],
                "negative": ["7", 0],
                "positive": ["6", 0],
                "sampler_name": "euler",
                "scheduler": "normal",
                "seed": seed,
                "steps": steps
            }
        },
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": checkpoint}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"batch_size": 1, "height": height, "width": width}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": positive_prompt}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": negative_prompt}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]}}
    
    client_id = str(uuid.uuid4())
    ws = websocket.WebSocket()
    ws.connect(f"ws://{server_address}/ws?clientId={client_id}")
    
    try:
        prompt_info = await tool_queue_prompt(prompt, client_id)
        prompt_id = prompt_info['prompt_id']
        
        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing' and message['data']['node'] is None and message['data']['prompt_id'] == prompt_id:
                    break
        
        history = await tool_get_history(prompt_id)
        outputs = history[prompt_id]['outputs']
        
        for node_id in outputs:
            if 'images' in outputs[node_id]:
                for image in outputs[node_id]['images']:
                    image_path = os.path.join(comfyui_path, image['type'], image['subfolder'], image['filename']) if image['subfolder'] else os.path.join(comfyui_path, image['type'], image['filename'])
                    
                    if is_file_path:
                        dest_path = save_path
                    else:
                        dest_path = os.path.join(save_path, image['filename'])
                    
                    shutil.copy2(image_path, dest_path)
                    return dest_path
        
        return "No image generated"
    finally:
        ws.close()

if __name__ == "__main__":
    mcp.run(transport='stdio') 