"""
ComfyUI Tool - Unified Interface

This module provides a unified interface for ComfyUI image generation that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced ComfyUI operations as MCP tools
2. Interactive mode: Runs as an interactive agent with ComfyUI capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python comfyui_tool.py                        # MCP Server mode (default)
  python comfyui_tool.py --interactive          # Interactive mode
  python comfyui_tool.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class ComfyUITool(ToolTemplate):
    """ComfyUI image generation tool using ToolTemplate"""
    
    SYSTEM_PROMPT = """
You are an AI assistant specialized in image generation using ComfyUI. Your primary role is to help users create high-quality images by effectively utilizing the available tools while following best practices.

Available tool: generate_image_with_comfyui - Creates images based on text prompts using the SDXL-TURBO model. Key parameters: save_path (required), positive_prompt, negative_prompt, width, height, seed. Note: steps, cfg and checkpoint parameters should not be modified as they are optimized for fast generation.

Tool selection guidance: Always use generate_image_with_comfyui when the user requests image generation. For other requests not involving image creation, respond directly without tool usage.

Standard workflow:
1. Receive image generation request with optional parameters
2. Validate required save_path is provided
3. Set default values for unspecified parameters (width=512, height=512, seed=0)
4. Execute generation with optimized fixed parameters (steps=1, cfg=1)
5. Return the saved image path

Error handling:
- If save_path is missing: Request this parameter before proceeding
- If generation fails: Verify ComfyUI server is running and retry once
- For invalid paths: Suggest valid path format and retry
- For non-English prompts: Politely request English text input

Response format:
- Always confirm successful generation and provide the exact file path
- Include brief generation details (dimensions, seed used)
- For errors: Clearly explain the issue and required corrective action

Important rules:
1. Never modify the steps, cfg or checkpoint parameters
2. Always validate paths before generation
3. Ensure prompts are in English
4. Return complete file paths for generated images
5. Maintain fast response times by using the optimized default settings
"""
    
    TOOLS = [
        ("server.py", "comfyui_image_generator_operations")
    ]
    
    MCP_SERVER_NAME = "comfyui_image_generator_tool"
    
    TOOL_DESCRIPTION = """
    Generates images using ComfyUI based on natural language descriptions or style specifications.

This tool accepts text prompts describing desired images and returns generated images along with generation details. It supports various styles, compositions, and can incorporate specific artistic references.

Input format:
- Natural language description of desired image (required)
- Optional style specifications (e.g., "anime style", "photorealistic")
- Can include composition details (e.g., "centered portrait", "wide landscape")
- May reference specific artists or art styles
- Can specify image dimensions (e.g., "1024x768")

Returns:
- 'image_url': URL to generated image (PNG format)
- 'generation_parameters': Dictionary of parameters used (prompt, seed, steps, etc.)
- 'success': Boolean indicating generation success
- 'message': Additional information or error details

Examples:
- "A futuristic cityscape at night with neon lights, cyberpunk style"
- "Portrait of a warrior with golden armor, fantasy art style, 1024x1024"
- "Watercolor painting of autumn forest with vibrant colors"
- "Product photo of a modern smartphone on marble surface, studio lighting"
- "Character design sheet for a steampunk inventor, multiple poses"
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for ComfyUI tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,  # Image generation usually completes in one iteration
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    ComfyUITool.main() 