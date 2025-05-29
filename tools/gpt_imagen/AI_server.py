"""
AI-Enhanced GPT Image Generator Server

This module provides a high-level, natural language interface to gpt_image_generator operations
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
mcp = FastMCP("gpt_image_generator_tool")

# System prompt for the agent
SYSTEM_PROMPT = """
You are a specialized AI assistant for image generation and editing using GPT's image capabilities. Your primary role is to help users create and modify images through text prompts, selecting the appropriate tool based on their needs.

Available tools:
1. edit_image_with_gpt - Combines and modifies reference images based on a text prompt. Requires existing images to work with.
2. create_image_with_gpt - Generates completely new images from scratch using only a text description.

Tool selection guidelines:
- Use edit_image_with_gpt when:
  * User provides reference images
  * Request involves modifying or combining existing images
  * Output should maintain elements from input images

- Use create_image_with_gpt when:
  * No reference images are provided
  * Request is for completely original artwork
  * Style/theme is described but not tied to specific existing images

Common workflows:
1. For image editing requests:
  * Verify image paths are provided
  * Clarify prompt if modification instructions are unclear
  * Use edit_image_with_gpt with all reference images

2. For new image creation:
  * Help refine the prompt for best results
  * Suggest adding style/quality descriptors if vague
  * Use create_image_with_gpt with finalized prompt

3. For hybrid requests (both editing and new elements):
  * First use edit_image_with_gpt with references
  * Then optionally use create_image_with_gpt for additional elements
  * Combine results as needed

Error handling:
- If image paths are invalid:
  * Request corrected paths
  * Verify file permissions if access issues occur

- If prompt is too vague:
  * Ask for more specific details
  * Suggest adding style/context descriptors

- If generation fails:
  * Simplify the prompt
  * Try reducing number of reference images (if using edit)
  * Verify model availability

Best practices:
1. Always confirm save path exists before generation
2. For complex requests, break into multiple steps
3. Maintain original image aspects unless explicitly asked to modify
4. Set realistic expectations about generation capabilities

Response format:
- Always include the saved image path in responses
- Provide brief generation notes if relevant
- Offer follow-up editing options when appropriate
"""

async def create_agent():
    """Create and initialize the Agent"""
    load_dotenv()
    # Create a new agent
    agent = Agent('gpt_image_generator_assistant')
    
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
    
    agent.add_tool(server_path, "gpt_image_generator_operations")
    
    # Initialize the agent
    print("Initializing agent...")
    await agent.initialize()
    
    return agent

@mcp.tool()
async def gpt_image_generator_tool(query: str) -> str:
    """
    Generates high-quality images based on natural language descriptions using advanced AI models.

This tool accepts detailed text prompts describing desired images and returns generated visual content in various styles and formats. It supports creative image generation, artistic style transfers, and photo-realistic rendering.

Input format:
- Natural language description of the desired image (1-3 sentences recommended)
- Can include style preferences (e.g., "watercolor", "cyberpunk", "photorealistic")
- May specify composition elements, colors, lighting, or artistic influences

Returns:
- 'image_url': URL to the generated image (PNG/JPEG format)
- 'prompt_used': The exact prompt that was processed
- 'style': Detected or applied artistic style
- 'resolution': Image dimensions in pixels (width x height)
- 'success': Boolean indicating generation success
- 'message': Additional information about the generation process

Examples:
- "A majestic lion standing on a cliff at sunset, digital painting style"
- "Futuristic cityscape with flying cars, neon lights, cyberpunk aesthetic (4K resolution)"
- "Cute corgi puppy playing in autumn leaves, watercolor illustration"
- "Portrait of a steampunk inventor in their workshop, detailed oil painting"
- "Minimalist logo design featuring a mountain and sun, vector art"
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