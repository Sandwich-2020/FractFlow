"""
Visual Question Answering Tool - Unified Interface

This module provides a unified interface for visual question answering that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced VQA operations as MCP tools
2. Interactive mode: Runs as an interactive agent with VQA capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python vqa_tool.py                        # MCP Server mode (default)
  python vqa_tool.py --interactive          # Interactive mode
  python vqa_tool.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class VQATool(ToolTemplate):
    """Visual Question Answering tool using ToolTemplate"""
    
    SYSTEM_PROMPT = """
You are a specialized Visual Question Answering assistant that analyzes images and provides detailed responses based on user prompts. Your primary function is to interpret visual content through the Qwen-VL-Plus model.

AVAILABLE TOOL: Visual_Question_Answering - Processes images and answers questions about their content. Accepts an image path and text prompt, returns detailed analysis.

TOOL USAGE GUIDELINES:
- Use for any task requiring image understanding or analysis
- Image paths must be accessible system paths to valid image files
- Prompts can be questions, description requests, or analytical tasks
- Images are automatically resized to 512x512 pixels maximum

WORKFLOW PATTERNS:
1. Receive user request with image path and question/instruction
2. Validate image path exists and is accessible
3. Process image and prompt through VQA tool
4. Return model's analysis in clear, structured format

ERROR HANDLING:
- If image path is invalid: Request correct path or alternative image
- If prompt is unclear: Ask for clarification or more specific question
- If analysis fails: Inform user and suggest retrying with adjusted parameters

RESPONSE FORMATTING:
- Provide direct answers to specific questions
- For descriptive requests, organize details logically
- Include relevant observations from the image analysis
- Maintain concise yet informative responses
"""
    
    TOOLS = [
        ("server.py", "visual_question_answering_operations")
    ]
    
    MCP_SERVER_NAME = "visual_question_answering_tool"
    
    TOOL_DESCRIPTION = """
    Answers questions about visual content by analyzing images and providing relevant information.

This tool accepts natural language questions about images and returns accurate answers by interpreting both the visual content and the question context. The tool can analyze uploaded images or work with image references provided in the query.

Input format:
- Natural language questions about visual content
- Can include image references (URLs, file descriptions, or contextual references)
- May specify particular aspects of the image to focus on

Returns:
- 'answer': Text response answering the visual question
- 'confidence': Float (0-1) indicating answer certainty
- 'visual_reference': Description of relevant image regions used
- 'success': Boolean indicating operation completion
- 'message': Additional context about the answer when available

Examples:
- "What color is the car in this image?"
- "How many people are visible in the photograph?"
- "Describe the painting style of this artwork"
- "Is there any text visible in the image and what does it say?"
- "Compare the two products shown in these images and highlight key differences"
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for VQA tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,  # Visual analysis usually completes in one iteration
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    VQATool.main() 