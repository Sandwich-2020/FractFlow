"""
3D Rendering Tool - Unified Interface with Auto-Detection

This module provides a unified interface for 3D rendering that can run in multiple modes:
1. Interactive mode: Runs as an interactive agent with automatic 3D file detection
2. Single query mode: Processes a single query and exits
3. Auto-render mode: Automatically detects and renders 3D files in user input

Usage:
  python render_agent.py --interactive          # Interactive mode
  python render_agent.py --query "..."          # Single query mode
"""

import os
import sys
import re
import argparse
import asyncio

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate and render functions
from FractFlow.tool_template import ToolTemplate
from FractFlow.infra.logging_utils import setup_logging
from render_mcp import render_mesh, detect_3d_files

class RenderTool(ToolTemplate):
    """3D Rendering tool with automatic file detection"""
    
    SYSTEM_PROMPT = """
你是一个专业的3D渲染助手，具有自动检测和渲染3D模型文件的能力。

# 核心功能
1. **自动3D文件检测**: 自动识别用户输入中的3D模型文件路径
2. **智能渲染**: 检测到3D文件时自动进行渲染
3. **多格式支持**: 支持 obj, glb, gltf, fbx, dae, ply, stl, blend, 3ds, x3d 等格式

# 工作流程
1. 分析用户输入，自动检测3D文件路径
2. 验证文件是否存在且可访问
3. 自动调用渲染功能生成多角度图像
4. 报告渲染结果和输出位置

# 自动检测规则
- 当用户输入包含3D文件路径时，自动触发渲染
- 支持绝对路径和相对路径
- 文件必须真实存在才会进行渲染
- 自动为每个检测到的文件创建渲染输出目录

# 渲染设置
- 分辨率: 800x800像素
- 相机角度: 8个方位角（0°-315°，45°间隔）
- 仰角: 0°（水平视角）
- 输出格式: PNG图像
- 自动创建以模型名称命名的渲染目录

# 交互模式
- 支持连续对话和多次渲染
- 每次检测到3D文件时自动渲染
- 提供清晰的渲染状态和结果反馈
- 支持同时处理多个3D文件

# 输出格式
对于每次渲染，提供以下信息：
- 检测到的3D文件路径
- 渲染输出目录
- 渲染进度和完成状态
- 生成的图像数量和文件名

# 错误处理
- 文件不存在：提示正确的文件路径
- 渲染失败：提供详细错误信息和解决建议
- 格式不支持：列出支持的文件格式

# 示例交互
用户: "请渲染这个模型 /path/to/model.obj"
系统: 自动检测到obj文件，开始渲染，报告结果

用户: "我有一个场景文件 scene.glb 需要查看"
系统: 自动检测到glb文件，进行渲染，提供输出位置
"""
    
    TOOLS = []  # 不使用外部MCP工具，使用硬编码功能
    
    TOOL_DESCRIPTION = """3D模型自动检测和渲染系统

# 核心特性
1. 自动3D文件检测：智能识别用户输入中的3D模型文件路径
2. 即时渲染：检测到3D文件时自动触发渲染过程
3. 多格式支持：obj, glb, gltf, fbx, dae, ply, stl, blend, 3ds, x3d
4. 智能输出：自动创建以模型名称命名的渲染目录

# 自动检测机制
- 基于文件扩展名的智能模式识别
- 路径验证确保文件真实存在
- 支持绝对路径和相对路径
- 批量处理多个3D文件

# 渲染规格
- 引擎：基于render_utils的高质量渲染
- 分辨率：800x800像素
- 相机设置：8个方位角，水平视角
- 输出：PNG格式，透明背景支持

# 输入示例
1. "渲染这个模型 model.obj"
2. "我有文件 /path/to/scene.glb 需要查看"
3. "处理这些文件：car.fbx, house.obj"

# 输出信息
- 检测结果：发现的3D文件列表
- 渲染状态：进度和完成情况
- 输出位置：生成图像的保存路径
- 错误处理：详细的问题诊断和建议

注意：系统会自动检测和处理3D文件，无需显式调用渲染命令。
"""
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Render tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='qwen',
            deepseek_model='qwen-plus',
            max_iterations=10,
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )
    
    @classmethod
    async def _run_interactive(cls):
        """Enhanced interactive mode with auto 3D file detection"""
        print(f"\n{cls.__name__} Interactive Mode with Auto 3D Detection")
        print("Type 'exit', 'quit', or 'bye' to end the conversation.")
        print("Simply mention any 3D file path and it will be automatically rendered!\n")
        
        agent = await cls.create_agent('agent')
        
        try:
            while True:
                user_input = input("You: ")
                if user_input.lower() in ('exit', 'quit', 'bye'):
                    break
                
                # Auto-detect 3D files in user input
                detected_files = detect_3d_files(user_input)
                
                if detected_files:
                    print(f"\n🎯 Detected 3D files: {detected_files}")
                    print("🚀 Starting automatic rendering...\n")
                    
                    for file_path in detected_files:
                        try:
                            print(f"📁 Rendering: {file_path}")
                            result = render_mesh(file_path)
                            print(f"✅ {result}\n")
                        except Exception as e:
                            print(f"❌ Error rendering {file_path}: {str(e)}\n")
                    
                    # Also process with agent for additional context
                    enhanced_query = f"我已经自动渲染了检测到的3D文件：{detected_files}。用户原始输入：{user_input}"
                    agent_result = await agent.process_query(enhanced_query)
                    print(f"Agent: {agent_result}")
                else:
                    # No 3D files detected, process normally with agent
                    print("\nProcessing...\n")
                    result = await agent.process_query(user_input)
                    print(f"Agent: {result}")
                    
        finally:
            await agent.shutdown()
            print("\nAgent session ended.")
    
    @classmethod
    async def _run_single_query(cls, query: str):
        """Enhanced single query mode with auto 3D file detection"""
        print(f"Processing query: {query}")
        
        # Auto-detect 3D files in query
        detected_files = detect_3d_files(query)
        
        if detected_files:
            print(f"\n🎯 Detected 3D files: {detected_files}")
            print("🚀 Starting automatic rendering...\n")
            
            for file_path in detected_files:
                try:
                    print(f"📁 Rendering: {file_path}")
                    result = render_mesh(file_path)
                    print(f"✅ {result}\n")
                except Exception as e:
                    print(f"❌ Error rendering {file_path}: {str(e)}\n")
        
        # Also process with agent
        print("\nProcessing with agent...\n")
        agent = await cls.create_agent('agent')
        
        try:
            if detected_files:
                enhanced_query = f"我已经自动渲染了检测到的3D文件：{detected_files}。用户原始查询：{query}"
                result = await agent.process_query(enhanced_query)
            else:
                result = await agent.process_query(query)
            print(f"Result: {result}")
            return result
        finally:
            await agent.shutdown()
            print("\nAgent session ended.")
    
    @classmethod
    def main(cls):
        """Custom main entry point that defaults to interactive mode"""
        # Validate configuration
        cls._validate_configuration()
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(description=f'{cls.__name__} - 3D Rendering with Auto-Detection')
        parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode (default)')
        parser.add_argument('--query', '-q', type=str, help='Single query mode: process this query and exit')
        parser.add_argument('--log-level', '-l', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Log level')
        args = parser.parse_args()
        
        # Setup logging
        setup_logging(level=args.log_level)
        
        if args.query:
            # Single query mode
            print(f"Starting {cls.__name__} in single query mode.")
            asyncio.run(cls._run_single_query(args.query))
        else:
            # Default: Interactive mode (changed from MCP server mode)
            print(f"Starting {cls.__name__} in interactive mode.")
            asyncio.run(cls._run_interactive())

if __name__ == "__main__":
    RenderTool.main() 