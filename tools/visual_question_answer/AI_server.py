"""
AI-Enhanced Visual Question Answering Server

This module provides a high-level, natural language interface to visual_question_answering operations
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
mcp = FastMCP("visual_question_answering_tool")

# System prompt for the agent
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

async def create_agent():
    """Create and initialize the Agent"""
    load_dotenv()
    # Create a new agent
    agent = Agent('visual_question_answering_assistant')
    
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
    
    agent.add_tool(server_path, "visual_question_answering_operations")
    
    # Initialize the agent
    print("Initializing agent...")
    await agent.initialize()
    
    return agent

@mcp.tool()
async def visual_question_answering_tool(query: str) -> str:
    """
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