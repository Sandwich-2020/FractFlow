#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool Generator (toolgen)

Generates template code for FractFlow tools based on Jinja2 templates.
Users only need to implement the functional part of the code.
"""

import os
import sys
import argparse
import shutil
from typing import Dict, Any, List, Optional
import jinja2

# Constants
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def ensure_dir(directory: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)


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


def generate_tool(target_path: str, tool_name: str, description: str) -> None:
    """Generate a complete tool structure at the target path."""
    print(f"Generating tool '{tool_name}' at {target_path}...")
    
    # Create context for templates
    context = {
        "tool_name": tool_name,
        "description": description,
        "tool_name_snake": tool_name.lower().replace(' ', '_'),
        "tool_name_pascal": ''.join(word.capitalize() for word in tool_name.split(' ')),
    }
    
    # Create directory structure
    ensure_dir(os.path.join(target_path, "src"))
    ensure_dir(os.path.join(target_path, "tests"))
    ensure_dir(os.path.join(target_path, "docs"))
    
    # Create files from templates
    files_to_generate = [
        # (template_name, output_path)
        ("__init__.py.j2", os.path.join(target_path, "src", "__init__.py")),
        ("AI_server.py.j2", os.path.join(target_path, "src", "AI_server.py")),
        ("server.py.j2", os.path.join(target_path, "src", "server.py")),
        ("run_server.py.j2", os.path.join(target_path, "run_server.py")),
        ("requirements.txt.j2", os.path.join(target_path, "requirements.txt")),
        ("__init__.py.j2", os.path.join(target_path, "tests", "__init__.py")),
        ("test_unit.py.j2", os.path.join(target_path, "tests", f"test_{context['tool_name_snake']}_unit.py")),
        ("test_integration.py.j2", os.path.join(target_path, "tests", f"test_{context['tool_name_snake']}_integration.py")),
        ("User-Intention.md.j2", os.path.join(target_path, "docs", "User-Intention.md")),
    ]
    
    for template_name, output_path in files_to_generate:
        content = render_template(template_name, context)
        write_file(output_path, content)
        print(f"Created {output_path}")
    
    # Create placeholder for operations file
    operations_placeholder = os.path.join(target_path, "src", f"{context['tool_name_snake']}_operations.py")
    operations_content = f'''
# -*- coding: utf-8 -*-
"""
{tool_name} Operations

This file contains the core functionality for the {tool_name} tool.
YOU NEED TO IMPLEMENT YOUR TOOL LOGIC HERE.
"""

# TODO: 在此实现您的核心功能代码
# 您可以根据需求自由设计函数和数据结构
# 建议返回一个包含"success"字段的字典，以便调用方判断操作是否成功

def example_operation(param1: str, param2: int = 0) -> dict:
    """示例操作函数"""
    return {{
        "success": True,
        "message": f"示例操作，参数：{{param1}}, {{param2}}",
        "result": "这是一个示例返回值，请替换为实际功能实现"
    }}
'''
    write_file(operations_placeholder, operations_content)
    print(f"Created placeholder for operations file at {operations_placeholder}")
    print(f"\nTool generation complete! Now implement your tool's core functionality in {operations_placeholder}")


def main():
    """Main entry point for the toolgen command line interface."""
    parser = argparse.ArgumentParser(description="Generate template code for FractFlow tools")
    parser.add_argument("target_path", help="Path where the tool will be generated")
    parser.add_argument("--name", "-n", required=True, help="Name of the tool")
    parser.add_argument("--description", "-d", default="A FractFlow tool", help="Short description of the tool")
    
    args = parser.parse_args()
    
    # Normalize and validate path
    target_path = os.path.abspath(os.path.expanduser(args.target_path))
    
    # Check if target directory already exists and is not empty
    if os.path.exists(target_path) and os.listdir(target_path):
        response = input(f"Target directory {target_path} is not empty. Continue anyway? [y/N] ")
        if response.lower() not in ["y", "yes"]:
            print("Aborting.")
            sys.exit(1)
    
    # Generate the tool
    generate_tool(target_path, args.name, args.description)


if __name__ == "__main__":
    main() 