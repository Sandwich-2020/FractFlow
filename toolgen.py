#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FractFlow Toolgen - 启动脚本

简单的入口点，用于直接运行 toolgen 工具而不需要通过 python -m 方式。
自动从源代码推断工具名称和描述。
"""

import sys
import os
import argparse
import shutil
import asyncio
from typing import Dict, Any, List, Optional

# 添加项目根目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# 现在导入工具模块
from tools.toolgen.toolgen import generate_tool_components, ensure_dir, read_prompt, render_template, write_file
from tools.toolgen.utils.agent_helper import (
    create_code_analysis_agent, 
    generate_server_components, 
    generate_ai_server_components, 
    generate_run_server_components,
    infer_tool_info
)
from dotenv import load_dotenv

async def infer_tool_information(source_path: str) -> Dict[str, str]:
    """从源代码推断工具名称和描述"""
    # 读取源文件
    with open(source_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # 获取提示文本
    server_prompt = read_prompt("server_generation.txt") if os.path.exists(os.path.join(script_dir, "tools/toolgen/prompts/server_generation.txt")) else ""
    
    # 创建并配置agent
    agent = await create_code_analysis_agent(server_prompt)
    
    try:
        # 推断工具信息
        tool_info = await infer_tool_info(agent, source_code)
        return tool_info
    finally:
        # 确保agent正确关闭
        await agent.shutdown()

async def async_generate_tool(target_path: str, tool_name: str, description: str, source_path: str) -> None:
    """Generate a tool asynchronously"""
    print(f"Generating tool '{tool_name}' at {target_path} based on source: {source_path}")
    
    # Create directory structure
    ensure_dir(os.path.join(target_path, "src"))
    ensure_dir(os.path.join(target_path, "tests"))
    ensure_dir(os.path.join(target_path, "docs"))
    
    # Generate files using Agent
    try:
        # Generate tool components
        context = await generate_tool_components(source_path, tool_name, description)
        
        # Copy the source file to the target directory
        source_filename = os.path.basename(source_path)
        target_source_path = os.path.join(target_path, "src", source_filename)
        shutil.copy2(source_path, target_source_path)
        print(f"Copied source file to {target_source_path}")
        
        # Generate files from templates
        files_to_generate = [
            # (template_name, output_path, description)
            ("server.py.j2", os.path.join(target_path, "src", "server.py"), "server.py with MCP tools"),
            ("AI_server.py.j2", os.path.join(target_path, "src", "AI_server.py"), "AI_server.py with FractFlow Agent"),
            ("run_server.py.j2", os.path.join(target_path, "run_server.py"), "run_server.py script"),
            ("__init__.py.j2", os.path.join(target_path, "src", "__init__.py"), "src/__init__.py"),
            ("requirements.txt.j2", os.path.join(target_path, "requirements.txt"), "requirements.txt"),
            ("__init__.py.j2", os.path.join(target_path, "tests", "__init__.py"), "tests/__init__.py"),
            ("test_unit.py.j2", os.path.join(target_path, "tests", f"test_{context['tool_name_snake']}_unit.py"), "unit tests"),
            ("test_integration.py.j2", os.path.join(target_path, "tests", f"test_{context['tool_name_snake']}_integration.py"), "integration tests"),
            ("User-Intention.md.j2", os.path.join(target_path, "docs", "User-Intention.md"), "documentation"),
        ]
        
        for template_name, output_path, description in files_to_generate:
            content = render_template(template_name, context)
            write_file(output_path, content)
            print(f"Created {description} at {output_path}")
        
    except Exception as e:
        print(f"Error generating tool: {str(e)}")
        raise
    
    print(f"\nTool generation complete! Your tool is ready to use at {target_path}")

async def async_main():
    """Async main entry point"""
    # Load environment variables (for API keys)
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Generate FractFlow tools based on source code")
    parser.add_argument("target_path", help="Path where the tool will be generated")
    parser.add_argument("--source", "-s", required=True, help="Path to source file containing core implementations")
    
    args = parser.parse_args()
    
    # Normalize and validate paths
    target_path = os.path.abspath(os.path.expanduser(args.target_path))
    source_path = os.path.abspath(os.path.expanduser(args.source))
    
    # Check if source file exists
    if not os.path.exists(source_path) or not os.path.isfile(source_path):
        print(f"Error: Source file does not exist or is not a file: {source_path}")
        return 1
    
    # Check if target directory already exists and is not empty
    if os.path.exists(target_path) and os.listdir(target_path):
        response = input(f"Target directory {target_path} is not empty. Continue anyway? [y/N] ")
        if response.lower() not in ["y", "yes"]:
            print("Aborting.")
            return 1
    
    # 自动推断工具信息
    try:
        print("Inferring tool information from source code...")
        tool_info = await infer_tool_information(source_path)
        
        tool_name = tool_info["tool_name"]
        description = tool_info["description"]
        
        print(f"Using inferred tool name: {tool_name}")
        print(f"Using inferred description: {description}")
    except Exception as e:
        print(f"Error inferring tool information: {str(e)}")
        # 从源文件名生成默认工具名
        source_filename = os.path.basename(source_path)
        module_name = os.path.splitext(source_filename)[0]
        tool_name = " ".join(word.capitalize() for word in module_name.split("_"))
        description = f"Tool based on {module_name} module"
        print(f"Using default tool name: {tool_name}")
        print(f"Using default description: {description}")
    
    # Generate the tool
    try:
        await async_generate_tool(target_path, tool_name, description, source_path)
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

def main():
    """Main entry point for the toolgen command line interface."""
    # 使用asyncio.run运行异步主函数
    return asyncio.run(async_main())

if __name__ == "__main__":
    sys.exit(main()) 