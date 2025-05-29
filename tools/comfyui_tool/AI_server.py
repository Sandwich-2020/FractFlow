"""
AI-Enhanced ComfyUI Image Generator Server

This module provides a high-level, natural language interface to comfyui_image_generator operations
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
mcp = FastMCP("comfyui_image_generator_tool")

# System prompt for the agent
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

async def create_agent():
    """Create and initialize the Agent"""
    load_dotenv()
    # Create a new agent
    agent = Agent('comfyui_image_generator_assistant')
    
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
    
    agent.add_tool(server_path, "comfyui_image_generator_operations")
    
    # Initialize the agent
    print("Initializing agent...")
    await agent.initialize()
    
    return agent

@mcp.tool()
async def comfyui_image_generator_tool(query: str) -> str:
    """
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