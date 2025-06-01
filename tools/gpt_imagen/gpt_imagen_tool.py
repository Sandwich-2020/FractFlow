"""
GPT Image Generation Tool - Unified Interface

This module provides a unified interface for GPT image generation and editing that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced image operations as MCP tools
2. Interactive mode: Runs as an interactive agent with image capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python gpt_imagen_tool.py                        # MCP Server mode (default)
  python gpt_imagen_tool.py --interactive          # Interactive mode
  python gpt_imagen_tool.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class GPTImagenTool(ToolTemplate):
    """GPT image generation and editing tool using ToolTemplate"""
    
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
    
    TOOLS = [
        ("server.py", "gpt_image_generator_operations")
    ]
    
    MCP_SERVER_NAME = "gpt_image_generator_tool"
    
    TOOL_DESCRIPTION = """
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
    
    @classmethod
    def create_config(cls):
        """Custom configuration for GPT Image tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,  # Image generation and editing
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    GPTImagenTool.main() 