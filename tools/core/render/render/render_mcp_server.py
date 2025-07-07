"""
3D Rendering MCP Server - Standard MCP Implementation

This module provides a standard MCP server implementation for 3D rendering using FastMCP.
"""

import os
import sys
from typing import Optional
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import render functions
from render_mcp import render_mesh, detect_3d_files

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("3d_render_tool")

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

@mcp.tool()
def render_3d_file(file_path: str, output_directory: Optional[str] = None) -> str:
    """
    Render a 3D model file to multiple viewpoint images.
    
    This tool takes a 3D model file (obj, glb, gltf, fbx, etc.) and renders it
    from multiple camera angles to create a set of PNG images.
    
    Parameters:
        file_path: str - Path to the 3D model file to render
        output_directory: str - Optional directory to save rendered images
                                If not provided, creates a directory based on the model name
    
    Returns:
        str - Success message with details about the rendering process and output location
    
    Supported formats:
        - OBJ, GLB, GLTF, FBX, DAE, PLY, STL, BLEND, 3DS, X3D
    
    Rendering specifications:
        - Resolution: 1024x1024 pixels
        - Camera angles: 6 viewpoints (0°, 45°, 90°, 180°, 270°, 315°)
        - Elevation: 30° 
        - Output format: PNG with transparent background
        - Lighting: Professional studio environment
    
    Examples:
        render_3d_file("/path/to/model.obj")
        render_3d_file("scene.glb", "/custom/output/directory")
    """
    try:
        # Normalize the file path
        normalized_path = normalize_path(file_path)
        
        # Check if file exists
        if not os.path.exists(normalized_path):
            return f"错误：文件不存在 - {normalized_path}"
        
        # Check if file has supported extension
        supported_extensions = ['.obj', '.glb', '.gltf', '.fbx', '.dae', '.ply', '.stl', '.blend', '.3ds', '.x3d']
        file_ext = os.path.splitext(normalized_path)[1].lower()
        if file_ext not in supported_extensions:
            return f"错误：不支持的文件格式 {file_ext}。支持的格式：{', '.join(supported_extensions)}"
        
        # Render the mesh
        if output_directory:
            output_dir = normalize_path(output_directory)
            result = render_mesh(normalized_path, output_dir)
        else:
            result = render_mesh(normalized_path)
            
        return result
        
    except Exception as e:
        return f"渲染过程中发生错误: {str(e)}"

@mcp.tool()
def detect_3d_files_in_text(text: str) -> str:
    """
    Automatically detect 3D model file paths in text.
    
    This tool analyzes text input to find potential 3D model file paths
    based on file extensions and validates their existence.
    
    Parameters:
        text: str - Text content to analyze for 3D file paths
    
    Returns:
        str - JSON-formatted string containing detected files and their status
    
    Detection criteria:
        - Looks for files with 3D extensions (obj, glb, gltf, fbx, etc.)
        - Validates file existence
        - Supports absolute and relative paths
        - Handles multiple file formats
    
    Examples:
        detect_3d_files_in_text("请渲染这个模型 /path/to/model.obj")
        detect_3d_files_in_text("我有文件 scene.glb 和 car.fbx 需要处理")
    """
    try:
        detected_files = detect_3d_files(text)
        
        if not detected_files:
            return "未在文本中检测到3D文件路径"
            
        result = {
            "detected_files": detected_files,
            "count": len(detected_files),
            "message": f"检测到 {len(detected_files)} 个3D文件"
        }
        
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"文件检测过程中发生错误: {str(e)}"

@mcp.tool()
def render_detected_files(text: str) -> str:
    """
    Automatically detect and render 3D files found in text.
    
    This tool combines file detection and rendering in one step.
    It analyzes the text for 3D file paths and renders each detected file.
    
    Parameters:
        text: str - Text content to analyze and render
    
    Returns:
        str - Detailed report of detection and rendering results
    
    Process:
        1. Detect 3D files in the provided text
        2. Validate file existence
        3. Render each valid file
        4. Generate comprehensive report
    
    Examples:
        render_detected_files("请渲染这个模型 /path/to/model.obj")
        render_detected_files("处理这些文件: scene.glb, car.fbx, house.obj")
    """
    try:
        # Detect 3D files
        detected_files = detect_3d_files(text)
        
        if not detected_files:
            return "未在文本中检测到任何3D文件路径"
        
        results = []
        results.append(f"🎯 检测到 {len(detected_files)} 个3D文件:")
        
        for file_path in detected_files:
            results.append(f"\n📁 处理文件: {file_path}")
            try:
                render_result = render_mesh(file_path)
                results.append(f"✅ 渲染成功: {render_result}")
            except Exception as e:
                results.append(f"❌ 渲染失败: {str(e)}")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"自动渲染过程中发生错误: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the MCP server
    mcp.run(transport='stdio') 