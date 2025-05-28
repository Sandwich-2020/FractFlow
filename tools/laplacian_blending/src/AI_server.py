"""
AI-Enhanced Image Blender Server

This module provides a high-level, natural language interface to image_blender operations
by wrapping the low-level MCP tools with a FractFlow Agent. The agent interprets
user requests and selects the appropriate operations to execute.
"""

import asyncio
import os
import sys
import logging
import argparse
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import os.path as osp

# Import the FractFlow Agent
from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager
from FractFlow.infra.logging_utils import setup_logging, get_logger

# Setup logging
setup_logging(level=logging.INFO)

# Initialize FastMCP server
mcp = FastMCP("image_blender_tool")

# System prompt for the agent
SYSTEM_PROMPT = """
You are an Image Blending Assistant specialized in creating seamless image blends using Laplacian pyramid blending techniques. Your primary function is to help users combine images with smooth transitions using provided masks.

AVAILABLE TOOLS:
1. laplacian_blending - Combines two images using a mask with multi-resolution blending
   Parameters:
   - path_A: First image path/URL
   - path_B: Second image path/URL  
   - path_mask: Mask image path/URL (white=use image A, black=use image B)
   - output_dir: Directory to save result (default: "output")
   - levels: Pyramid levels (default: 6)

TOOL SELECTION GUIDELINES:
- Use laplacian_blending when:
  - User wants to merge two images seamlessly
  - User provides or can create a blending mask
  - Smooth transitions between images are needed
- Don't use when:
  - Simple overlays or basic composites would suffice
  - No mask is available or specified

WORKFLOW PATTERNS:
1. Standard blending:
   - Receive two images and mask from user
   - Execute laplacian_blending with all inputs
   - Return blended result path

2. URL-based blending:
   - Verify URLs are accessible image files
   - Process remote images directly
   - Return local path to downloaded result

3. Multi-level adjustment:
   - For complex blends, adjust pyramid levels
   - Higher levels for smoother transitions
   - Lower levels for sharper edges

ERROR HANDLING:
- For invalid inputs:
  - Check image URLs/paths exist
  - Verify images are loadable
  - Confirm mask dimensions match
- On failure:
  - Identify specific error (download, size mismatch, etc.)
  - Suggest corrective actions
  - Never proceed with invalid inputs

RESPONSE FORMATTING:
- Always return:
  - Confirmation of received inputs
  - Processing status updates
  - Final output path when complete
  - Clear error messages if issues occur

BEST PRACTICES:
1. Validate all inputs before processing
2. Suggest optimal pyramid levels based on image sizes
3. Maintain original aspect ratios during resizing
4. Provide clear instructions for mask creation if needed
5. Store results in organized output directory
"""

async def create_agent():
    """Create and initialize the Agent"""
    load_dotenv()
    # Create a new agent
    agent = Agent('image_blender_assistant')
    
    # Configure the agent
    config = agent.get_config()
    config['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    config['agent']['provider'] = 'deepseek'
    config['deepseek']['model'] = 'deepseek-chat'
    config['agent']['max_iterations'] = 5
    config['agent']['custom_system_prompt'] = SYSTEM_PROMPT
    config['tool_calling']['version'] = 'turbo'
    
    # Apply configuration
    agent.set_config(config)
    
    # Add tools to the agent
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "server.py")
    
    agent.add_tool(server_path, "image_blender_operations")
    
    # Initialize the agent
    print("Initializing agent...")
    await agent.initialize()
    
    return agent

@mcp.tool()
async def image_blender_tool(query: str) -> str:
    """
    Blends and manipulates images based on natural language instructions.

This tool accepts free-form requests for image blending, transformation, and enhancement operations, and returns processed images with metadata. Supports combining multiple images, applying filters, adjusting properties, and generating creative compositions.

Input format:
- Natural language describing the desired image operation
- Can reference multiple images to blend or modify
- May include specific parameters (blend modes, opacity, positioning)
- Can request artistic filters or style transfers

Returns:
- 'blended_image': Base64 encoded result image
- 'operation_details': Description of performed operations  
- 'success': Boolean indicating operation completion status
- 'message': Additional information or error details
- 'parameters': Dictionary of applied parameters (blend_mode, opacity, etc.)

Examples:
- "Blend image1.jpg and image2.png with 50% opacity using multiply mode"
- "Create a double exposure effect with portrait.jpg and cityscape.png"
- "Apply a watercolor filter to sunset.jpg with intensity 0.7"
- "Combine these three product images into a collage with equal spacing"
- "Merge the foreground from photo1.png with the background of photo2.jpg using alpha matting"
    """
    # Create and initialize the agent
    agent = await create_agent()
    
    try:
        # Process the query with the agent
        result = await agent.process_query(query)
        return result
    finally:
        # Ensure the agent is properly shut down
        await agent.shutdown()

if __name__ == "__main__":
    # Run the MCP server
    mcp.run(transport='stdio') 