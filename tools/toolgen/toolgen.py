#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool Generator (toolgen)

Generates FractFlow tools based on user-provided source code.
Uses FractFlow Agent to analyze source code and generate appropriate MCP tools.
"""

import os
import sys
import re
import argparse
import shutil
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
import jinja2
import json

from dotenv import load_dotenv
from FractFlow.agent import Agent

# Constants
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
PROMPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Helper functions for code generation
async def create_code_analysis_agent(system_prompt: str) -> Agent:
    """
    Create and initialize a FractFlow Agent for code analysis.
    
    Args:
        system_prompt: The system prompt to guide the Agent's behavior
        
    Returns:
        Initialized FractFlow Agent
    """
    # Create a new agent
    agent = Agent('code_analysis_agent')
    
    # Configure the agent
    config = agent.get_config()
    config['agent']['provider'] = 'deepseek'  # Default to deepseek
    config['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    config['qwen']['api_key'] = os.getenv('QWEN_API_KEY')  # As fallback
    
    # Use qwen if deepseek key is not available
    if not config['deepseek']['api_key'] and config['qwen']['api_key']:
        config['agent']['provider'] = 'qwen'
        logger.info("Using Qwen as the model provider")
    elif not config['deepseek']['api_key']:
        raise ValueError("No API key found for DeepSeek or Qwen. Please set environment variables.")
    
    # Further configuration
    config['deepseek']['model'] = 'deepseek-chat'
    config['agent']['max_iterations'] = 5
    config['agent']['custom_system_prompt'] = system_prompt
    config['tool_calling']['version'] = 'turbo'
    
    # Apply configuration
    agent.set_config(config)
    
    # Initialize the agent
    logger.info("Initializing code analysis agent...")
    await agent.initialize()
    
    return agent

def extract_code_from_response(response: str) -> str:
    """
    Extract code blocks from an Agent response.
    
    Args:
        response: The Agent's response text
        
    Returns:
        Extracted code, or the original response if no code blocks found
    """
    # Look for Python code blocks
    code_pattern = r'```(?:python)?\s*([\s\S]*?)\s*```'
    matches = re.findall(code_pattern, response)
    
    if matches:
        # Return the largest code block (likely the complete file)
        return max(matches, key=len).strip()
    
    # If no code blocks found, return the original response
    # (after stripping markdown formatting if present)
    return response.strip()

async def extract_function_names(agent: Agent, source_code: str) -> List[str]:
    """
    Analyze source code and identify functions that should be exposed as tools.
    This may involve reorganizing, renaming, or grouping functions for better LLM interaction.
    
    Args:
        agent: Initialized FractFlow Agent
        source_code: Source code to analyze
        
    Returns:
        List of function names (may include new proposed function names)
    """
    query = f"""
    深入分析以下源代码，确定应该作为工具暴露的函数:
    
    ```python
    {source_code}
    ```
    
    请考虑以下几点:
    1. 工具功能应该低耦合、高内聚
    2. 工具名称和功能应该容易被大语言模型理解
    3. 工具接口应该清晰，避免歧义
    4. 可能需要将现有函数分解、组合或重新命名以创建更合理的工具
    
    返回一个逗号分隔的函数名列表，这些函数应该在 server.py 中实现。
    如果建议创建新的工具函数，请提供建议的新函数名和说明。
    仅返回函数名列表，不要包含其他解释。
    """
    
    response = await agent.process_query(query)
    function_list = response.strip()
    
    # Extract and clean function names
    functions = [f.strip() for f in function_list.split(',')]
    # Remove any empty strings
    functions = [f for f in functions if f]
    # Remove duplicates while preserving order
    seen = set()
    unique_functions = []
    for f in functions:
        if f not in seen:
            seen.add(f)
            unique_functions.append(f)
    
    logger.info(f"Identified functions to implement as tools: {unique_functions}")
    return unique_functions

async def generate_server_components(agent: Agent, source_code: str, source_module: str) -> Dict[str, str]:
    """
    Generate components for server.py based on deep analysis of the source code.
    Focuses on creating tools that are optimized for LLM interaction.
    
    Args:
        agent: Initialized FractFlow Agent
        source_code: Source code to analyze
        source_module: Name of the source module to import from
        
    Returns:
        Dictionary with components for server.py template
    """
    logger.info(f"Generating server components for module: {source_module}")
    
    # 1. Extract function names to import - may include proposed new functions
    functions = await extract_function_names(agent, source_code)
    
    # 2. Generate complete import section and tool definitions with deep consideration of LLM interaction patterns
    function_list = ', '.join(functions)
    query = f"""
    为 {source_module} 模块设计和实现高质量的 MCP 工具代码:

    源代码中的相关函数: {function_list}
    
    设计指南:
    1. 每个工具函数应添加 "tool_" 前缀以避免命名冲突
    2. 深入思考如何设计这些工具，使它们:
       - 功能明确、低耦合、高内聚
       - 易于被大语言模型理解和使用
       - 接口清晰，参数直观
       - 组合使用时能高效解决复杂问题
    3. 可以基于原始函数创建新的工具函数，如果这样能提高使用体验
    4. 提供详细的文档，帮助大语言模型理解如何使用这些工具
    5. 重要：源文件 {source_module}.py 和生成的server.py位于同一目录下

    请实现两部分代码：

    1. 完整的导入部分，包括：
       - 正确导入所有必要的模块和库
       - 从同目录下的 {source_module}.py 文件导入所需的函数
       - 根据源代码分析，添加任何其他必要的导入

    2. 工具函数定义部分，包括：
       - 所有工具函数的完整实现
       - 详细的文档字符串
       - 必要的类型提示

    请先思考最佳设计方案，再实现代码。返回完整的导入部分和工具定义部分，不要包括初始化FastMCP或运行服务器的代码。
    """
    
    response = await agent.process_query(query)
    full_code = extract_code_from_response(response)
    
    # 3. Split the code into import section and tool definitions
    import_section = ""
    tool_definitions = ""
    
    # Simple heuristic to split the code at the first function definition
    import_pattern = r'^(.*?)(?=@mcp\.tool\(\)|async\s+def\s+tool_)'
    tool_pattern = r'(@mcp\.tool\(\).*$)'
    
    import_match = re.search(import_pattern, full_code, re.DOTALL | re.MULTILINE)
    tool_match = re.search(tool_pattern, full_code, re.DOTALL | re.MULTILINE)
    
    if import_match:
        import_section = import_match.group(1).strip()
    if tool_match:
        tool_definitions = tool_match.group(1).strip()
    
    # If the regex splitting didn't work, use a fallback approach
    if not import_section or not tool_definitions:
        lines = full_code.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('@mcp.tool()') or (line.startswith('async def tool_')):
                import_section = '\n'.join(lines[:i]).strip()
                tool_definitions = '\n'.join(lines[i:]).strip()
                break
    
    # 4. Extract actual tool names from generated code
    tool_names = set()
    func_name_pattern = r'async\s+def\s+([a-zA-Z0-9_]+)\s*\('
    matches = re.findall(func_name_pattern, tool_definitions)
    tool_names.update(matches)
    
    # Generate available tools list without duplicates
    available_tools = '\n        '.join([f'print("- {name}")' for name in sorted(tool_names)])
    
    return {
        "import_section": import_section,
        "tool_definitions": tool_definitions,
        "available_tools": available_tools
    }

async def generate_system_prompt(agent: Agent, source_code: str, tool_name: str) -> str:
    """
    Generate system prompt for AI_server.py based on the source code.
    
    Args:
        agent: Initialized FractFlow Agent
        source_code: Original source code
        tool_name: Name of the tool being generated
        
    Returns:
        System prompt text
    """
    logger.info(f"Generating system prompt for tool: {tool_name}")
    
    query = f"""
    分析源代码和已优化的工具设计，为 {tool_name} 创建一个高效的系统提示:
    
    ```python
    {source_code}
    ```
    
    你的系统提示应当:
    1. 简洁明了地定义 AI 助手的角色和职责
    2. 清晰介绍可用工具及其用途
    3. 提供选择合适工具的指南
    4. 包含常见工作流程和使用模式
    5. 说明如何处理错误情况
    
    重点放在如何有效使用这些工具，而非它们的实现细节。
    使用简短段落和要点列表，提高可读性。
    
    仅返回系统提示文本，不包含任何代码块或其他格式。
    """
    
    response = await agent.process_query(query)
    return response.strip()

async def generate_tool_docstring(agent: Agent, source_code: str, tool_name: str) -> str:
    """
    Generate docstring for the main AI tool function.
    
    Args:
        agent: Initialized FractFlow Agent
        source_code: Original source code
        tool_name: Name of the tool being generated
        
    Returns:
        Tool docstring text
    """
    logger.info(f"Generating tool docstring for: {tool_name}")
    
    query = f"""
    为 {tool_name} 的主 AI 工具函数创建一个全面但简洁的文档字符串。
    
    函数签名:
    
    async def {tool_name.lower().replace(' ', '_')}_tool(query: str) -> Dict[str, Any]:
    
    文档字符串应当:
    1. 清晰解释工具的总体功能和用途
    2. 描述预期的自然语言查询格式
    3. 说明返回结构和可能的值
    4. 包含 3-5 个多样化的查询示例
    
    避免不必要的冗长，保持信息丰富但简洁。
    仅返回文档字符串文本，不包含函数定义或其他代码。
    """
    
    response = await agent.process_query(query)
    tool_docstring = extract_code_from_response(response)
    if tool_docstring.startswith('"""') and tool_docstring.endswith('"""'):
        tool_docstring = tool_docstring[3:-3].strip()
    
    return tool_docstring

async def generate_run_server_prompt(agent: Agent, source_code: str, tool_name: str) -> str:
    """
    Generate system prompt for run_server.py.
    
    Args:
        agent: Initialized FractFlow Agent
        source_code: Original source code
        tool_name: Name of the tool
        
    Returns:
        System prompt for run_server.py
    """
    logger.info(f"Generating run server prompt for tool: {tool_name}")
    
    query = f"""
    Based on this source code, generate a concise system prompt for the run_server.py script
    that runs {tool_name}:
    
    ```python
    {source_code}
    ```
    
    The system prompt should be shorter than the one for AI_server.py and should:
    1. Briefly describe what the tool does
    2. Include key capabilities
    3. Provide basic usage guidelines
    
    Return only the system prompt text without any code blocks or other formatting.
    """
    
    response = await agent.process_query(query)
    return response.strip()

async def generate_ai_server_components(agent: Agent, source_code: str, tool_name: str) -> Dict[str, str]:
    """
    Generate components for AI_server.py based on analysis of the source code.
    
    Args:
        agent: Initialized FractFlow Agent
        source_code: Source code to analyze
        tool_name: Name of the tool being generated
        
    Returns:
        Dictionary with components for AI_server.py template
    """
    logger.info(f"Generating AI server components for tool: {tool_name}")
    
    # Generate system prompt for the AI server
    system_prompt = await generate_system_prompt(agent, source_code, tool_name)
    
    # Generate tool docstring
    tool_docstring = await generate_tool_docstring(agent, source_code, tool_name)
    
    # Return the components needed for the AI_server.py template
    return {
        "system_prompt": system_prompt,
        "tool_docstring": tool_docstring
    }

async def generate_run_server_components(agent: Agent, source_code: str, tool_name: str) -> Dict[str, str]:
    """
    Generate components for run_server.py based on the source code.
    
    Args:
        agent: Initialized FractFlow Agent
        source_code: Source code to analyze
        tool_name: Name of the tool
        
    Returns:
        Dictionary with components for run_server.py template
    """
    logger.info(f"Generating run server components for tool: {tool_name}")
    
    # Generate system prompt for run_server.py
    run_server_system_prompt = await generate_run_server_prompt(agent, source_code, tool_name)
    
    return {
        "run_server_system_prompt": run_server_system_prompt
    }

async def infer_tool_info(agent: Agent, source_code: str) -> Dict[str, str]:
    """
    Analyze source code and infer appropriate tool name and description.
    
    Args:
        agent: Initialized FractFlow Agent
        source_code: Source code to analyze
        
    Returns:
        Dictionary with inferred tool name and description
    """
    logger.info("Inferring tool name and description from source code")
    
    query = f"""
    分析以下源代码，推断最合适的工具名称和简短描述:
    
    ```python
    {source_code}
    ```
    
    请考虑:
    1. 源代码的整体功能和目的
    2. 模块和函数的名称和文档字符串
    3. 该工具提供的主要功能和用例
    
    以JSON格式返回，仅包含两个字段:
    {{
      "tool_name": "推断的工具名称",
      "description": "简短的工具描述（不超过100个字符）"
    }}
    
    不要包含任何其他文本或解释。
    """
    
    response = await agent.process_query(query)
    
    # 尝试解析JSON响应
    try:
        # 尝试直接解析
        try:
            result = json.loads(response.strip())
        except json.JSONDecodeError:
            # 尝试从文本中提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                raise ValueError("无法解析响应为JSON")
        
        # 验证结果包含必要的字段
        if "tool_name" not in result or "description" not in result:
            raise ValueError("响应缺少必要的字段")
        
        logger.info(f"Inferred tool name: {result['tool_name']}")
        logger.info(f"Inferred description: {result['description']}")
        
        return {
            "tool_name": result["tool_name"], 
            "description": result["description"]
        }
    except Exception as e:
        logger.warning(f"Failed to infer tool info: {str(e)}. Using defaults.")
        # 从源文件名生成默认工具名
        module_name = os.path.basename(os.path.splitext(source_code)[0]) if isinstance(source_code, str) and os.path.exists(source_code) else "unknown"
        default_name = " ".join(word.capitalize() for word in module_name.split("_"))
        
        return {
            "tool_name": default_name,
            "description": f"Tool based on {module_name} module"
        }

# Utility functions
def ensure_dir(directory: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def read_prompt(prompt_name: str) -> str:
    """Read a prompt file from the prompts directory."""
    prompt_path = os.path.join(PROMPT_DIR, prompt_name)
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """Render a Jinja2 template with the given context."""
    template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template(template_name)
    return template.render(**context)

def write_file(path: str, content: str) -> None:
    """Write content to a file, creating directories if needed."""
    ensure_dir(os.path.dirname(path))
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

async def generate_tool_components(source_path: str, tool_name: str, description: str) -> Dict[str, Any]:
    """
    Generate tool components based on source code analysis.
    
    Args:
        source_path: Path to the source file
        tool_name: Name of the tool
        description: Short description of the tool
        
    Returns:
        Dictionary with generated components for templates
    """
    # Read source file
    with open(source_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # Get source module name without extension
    source_module = os.path.basename(source_path).split('.')[0]
    
    # Read prompts
    server_prompt = read_prompt("server_generation.txt")
    ai_server_prompt = read_prompt("ai_server_generation.txt")
    
    # Create basic context
    context = {
        "tool_name": tool_name,
        "description": description,
        "tool_name_snake": tool_name.lower().replace(' ', '_'),
        "tool_name_pascal": ''.join(word.capitalize() for word in tool_name.split(' ')),
        "source_module": source_module
    }
    
    # Create and configure agent for server components
    agent = await create_code_analysis_agent(server_prompt)
    
    try:
        # Generate server components
        server_components = await generate_server_components(agent, source_code, source_module)
        context.update(server_components)
        
        # Extract tool names for run_server components
        tool_names = []
        if "available_tools" in server_components:
            tools_code = server_components["available_tools"]
            tool_names = [line.split('"- ')[1].split('"')[0] for line in tools_code.split("\n") if '"- ' in line]
        
        # Update agent's system prompt for AI server generation
        await agent.shutdown()
        agent = await create_code_analysis_agent(ai_server_prompt)
        
        # Generate AI server components
        ai_server_components = await generate_ai_server_components(agent, source_code, tool_name)
        context.update(ai_server_components)
        
        # Generate run server components
        run_server_components = await generate_run_server_components(agent, source_code, tool_name)
        
        # Add available tools to run_server_components if we have tool names
        if tool_names:
            run_server_components["available_tools"] = "\n        ".join([f'print("- {name}")' for name in sorted(tool_names)])
        
        context.update(run_server_components)
        
        return context
    finally:
        # Ensure agent is shut down properly
        await agent.shutdown()

def generate_tool(target_path: str, tool_name: str, description: str, source_path: str) -> None:
    """
    Generate tool files directly in the target directory (same as source directory).
    Only creates server.py, AI_server.py, and run_server.py in the target directory.
    
    Args:
        target_path: Path where the tool will be generated (same as source directory)
        tool_name: Name of the tool
        description: Short description of the tool
        source_path: Path to the source file with core implementations
    """
    print(f"Generating tool '{tool_name}' in {target_path} based on source: {source_path}")
    
    # Generate files using Agent
    try:
        # Run the async function in the event loop
        loop = asyncio.get_event_loop()
        context = loop.run_until_complete(
            generate_tool_components(source_path, tool_name, description)
        )
        
        # No need to copy the source file as it's already in the directory
        
        # Generate only the essential files from templates
        files_to_generate = [
            # (template_name, output_path, description)
            ("server.py.j2", os.path.join(target_path, "server.py"), "server.py with MCP tools"),
            ("AI_server.py.j2", os.path.join(target_path, "AI_server.py"), "AI_server.py with FractFlow Agent"),
            ("run_server.py.j2", os.path.join(target_path, "run_server.py"), "run_server.py script"),
        ]
        
        for template_name, output_path, description in files_to_generate:
            content = render_template(template_name, context)
            write_file(output_path, content)
            print(f"Created {description} at {output_path}")
        
    except Exception as e:
        print(f"Error generating tool: {str(e)}")
        raise
    
    print(f"\nTool generation complete! Your tool is ready to use in {target_path}")

def main():
    """Main entry point for the toolgen command line interface."""
    # Load environment variables (for API keys)
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Generate FractFlow tools based on source code")
    parser.add_argument("source", help="Path to source file containing core implementations")
    
    args = parser.parse_args()
    
    # Normalize source path
    source_path = os.path.abspath(os.path.expanduser(args.source))
    
    # Check if source file exists
    if not os.path.exists(source_path) or not os.path.isfile(source_path):
        print(f"Error: Source file does not exist or is not a file: {source_path}")
        return 1
    
    # Set target_path to be the same folder as source
    target_path = os.path.dirname(source_path)
    source_name = os.path.basename(source_path).split('.')[0]
    print(f"Target path: {target_path}")
    
    # Infer tool name and description from source code
    print("Inferring tool name and description from source code...")
    # Run the async function in the event loop
    loop = asyncio.get_event_loop()
    with open(source_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # Create basic agent for inference
    server_prompt = read_prompt("server_generation.txt")
    agent = loop.run_until_complete(create_code_analysis_agent(server_prompt))
    
    try:
        inferred_info = loop.run_until_complete(infer_tool_info(agent, source_code))
        tool_name = inferred_info["tool_name"]
        description = inferred_info["description"]
    finally:
        loop.run_until_complete(agent.shutdown())
    
    print(f"Tool name: {tool_name}")
    print(f"Description: {description}")
    
    # Check if server.py, AI_server.py or run_server.py already exist in target directory
    existing_files = []
    for filename in ["server.py", "AI_server.py", "run_server.py"]:
        file_path = os.path.join(target_path, filename)
        if os.path.exists(file_path):
            existing_files.append(file_path)
    
    if existing_files:
        print("The following files already exist:")
        for file_path in existing_files:
            print(f"  - {file_path}")
        response = input("Overwrite these files? [y/N] ")
        if response.lower() not in ["y", "yes"]:
            print("Aborting.")
            return 1
    
    # Generate the tool
    try:
        generate_tool(target_path, tool_name, description, source_path)
        print(f"\nTo use your tool, run:")
        print(f"cd {target_path}")
        print(f"python run_server.py         # For interactive mode with direct tools")
        print(f"python run_server.py --ai    # For interactive mode with AI-enhanced tools")
        print(f"python run_server.py -q \"Your query here\"  # For single query mode")
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 