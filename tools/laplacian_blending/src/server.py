"""
Image Blender Tool Server

This module provides direct MCP tool implementations for the Image Blender tool.
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
# 源码特定导入部分
import cv2
import numpy as np
import urllib.request
from urllib.parse import urlparse
from uuid import uuid4
from laplacian_blending import load_image, laplacian_blending

# 工具函数定义部分

# Initialize FastMCP server
mcp = FastMCP("image_blender")

@mcp.tool()
def tool_load_image(image_path: str) -> np.ndarray:
    """Load an image from either a local file path or a URL.
    
    Args:
        image_path: Path to the image file or URL of the image
        
    Returns:
        numpy.ndarray: The loaded image as a NumPy array in BGR format
        
    Raises:
        ValueError: If the image cannot be loaded or is invalid
        FileNotFoundError: If local file doesn't exist
    """
    return load_image(image_path)

@mcp.tool()
def tool_laplacian_blend(
    image_a_path: str,
    image_b_path: str,
    mask_path: str,
    output_dir: str = "output",
    pyramid_levels: int = 6
) -> str:
    """Blend two images using Laplacian pyramid blending with a mask.
    
    Args:
        image_a_path: Path/URL to the first input image
        image_b_path: Path/URL to the second input image
        mask_path: Path/URL to the mask image (white=use image A, black=use image B)
        output_dir: Directory to save the blended result (default: "output")
        pyramid_levels: Number of pyramid levels for blending (default: 6)
        
    Returns:
        str: Path to the saved blended image
        
    Raises:
        ValueError: If any input image is invalid or cannot be loaded
    """
    return laplacian_blending(image_a_path, image_b_path, mask_path, output_dir, pyramid_levels)

if __name__ == "__main__":
    mcp.run(transport='stdio') 