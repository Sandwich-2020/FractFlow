"""
feedback_agent - 3D模型完整评估工作流程

本模块为3D模型提供完整的质量评估工作流程：
1. MCP Server模式（默认）：作为MCP工具协调物件与场景评估
2. Interactive模式：作为交互式agent运行，直接使用硬编码渲染功能
3. 单次查询模式：处理单次评估请求

完整工作流程：
  3D模型文件 → 多角度渲染 → 尺寸评估 → 位置评估 → 场景评估 → 综合反馈报告

用法：
  python feedback_agent.py                        # MCP Server模式（默认）
  python feedback_agent.py --interactive          # 交互模式
  python feedback_agent.py --query "..."          # 单次查询模式
"""

import os
import sys
import yaml
import re
import time
from pathlib import Path

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../../..'))
sys.path.append(project_root)

from FractFlow.tool_template import ToolTemplate
# 直接导入硬编码的渲染函数
sys.path.append(os.path.join(project_root, 'tools/core/render'))
from render_mcp import render_mesh, detect_3d_files

class FeedbackAgent(ToolTemplate):
    """3D模型完整评估工作流程代理，结合渲染功能与细分评估"""

    SYSTEM_PROMPT = """
你是一个文本结构化输出代理，负责调用目标评估和场景评估结果，智能分析并反馈质量问题。你必须严格按照以下流程执行，不得跳过任何步骤。

# 核心评估流程（严格按顺序执行）

## 阶段1：工作空间准备
- 接收3D场景文件路径作为输入
- 创建标准化工作目录：`./3d_feedback_workspace/{timestamp}_{model_basename}/`
- 设置子目录：`renders/`（渲染输出）、`evaluations/`（评估结果）

## 阶段2：多角度渲染
- 使用内置的render_mesh函数对3D场景进行6个角度渲染
- 生成6张高质量图像（1024x1024，PNG格式）：前视图、45°视图、侧视图、后视图、另一侧视图、315°视图
- 渲染输出保存到工作空间的`renders/`目录

## 阶段3：物体尺寸评估
- 调用SizeEvaluationTool,对场景中识别到的所有类型物体，预测其物体尺寸，参考标准尺寸范围，提供是否符合标准的结论
- 对图片中物体尺寸从visual_reasoning_answer, Conclusion, Success三个维度的分析
- 解析返回结果保存，并提取路径列表

## 阶段4：物体位置评估
- 调用PositionEvaluationTool,对场景中识别到的所有类型物体，预测其物体位置，参考标准位置范围，提供是否符合标准的结论
- 对图片中物体位置从visual_reasoning_answer, Conclusion, Success三个维度的分析
- 解析返回结果保存，并提取路径列表

## 阶段5：场景评估
- 调用SceneEvaluationTool，对场景进行全局理解
- 从物体位置合理性,物体空间关系,场景整体布局三个维度进行分析
- 解析返回结果保存，并提取路径列表

## 阶段6：结构化输出结论
- 从物体尺寸评估, 物体位置评估, 场景评估保存路径提取评估结论进行结构化分析
- 物体尺寸评估, 物体位置评估, 场景评估均以结构化YAML输出(visual_reasoning_answer, Conclusion, Success)
- 根据物体尺寸评估, 物体位置评估, 场景评估三个维度评估结论生成总评估（如：answer，confidence, Success)

# 工具使用规范

1. **SizeEvaluationTool** - 物体尺寸评估
   - 输入：渲染图像路径 + 结构化评估提示
   - 输出：尺寸评估结果（包含visual_reasoning_answer, Conclusion, Success）

2. **PositionEvaluationTool** - 物体位置评估
   - 输入：渲染图像路径 + 结构化评估提示
   - 输出：位置评估结果（包含visual_reasoning_answer, Conclusion, Success）

3. **SceneEvaluationTool** - 场景级质量评估
   - 输入：渲染图像路径 + 结构化评估提示
   - 输出：场景评估结果（包含answer, visual_reference, success）

# 输出格式要求
你的回复必须严格包含以下结构化信息：

```yaml
workflow_execution:
  model_path: "输入的3D场景文件路径"
  workspace: "工作目录路径"
  render_images: ["6张渲染图片路径列表"]
  execution_time: "执行时间(秒)"
  workflow_status: "completed/failed"

size_evaluation:
  visual_reasoning_answer: "对场景中识别到的所有类型物体，预测其物体尺寸，参考标准尺寸范围，是否符合标准的结论"
  conclusion: "场景每个类型的物体尺寸是否合理的直接结论（如：合理/不合理），单独列出存在尺寸不合理的物件"
  success: true/false

position_evaluation:
  visual_reasoning_answer: "对场景中识别到的所有类型物体，预测其物体位置，参考标准位置范围，是否符合标准的结论"
  conclusion: "场景所有类型的物体位置是否合理的直接结论（如：合理/不合理），单独列出存在位置不合理的物件"
  success: true/false

scene_evaluation:
  answer: ["针对每个评估问题的直接结论与判断"]
  visual_reference: ["本结论所依据的场景图像区域、对象或空间关系的简要说明"]
  success: true/false

overall_evaluation:
  answer: ["针对评估结论的简明描述"]
  confidence: [0.0-1.0] # 针对每条结论的确定性分数
  success: true/false
```

# 错误处理
- 如果渲染失败：立即终止，输出错误信息
- 若任一环节失败，需结构化输出失败原因，并建议后续优化方向
- 输出必须简洁、客观、结构化
    """

    TOOLS = [
        ("tools/core/QualityEvaluation/Size_evaluation_agent.py", "SizeEvaluationTool"),
        ("tools/core/QualityEvaluation/Position_evaluation_agent.py", "PositionEvaluationTool"),
        ("tools/core/QualityEvaluation/Scene_vqa_agent.py", "SceneEvaluationTool")
    ]

    MCP_SERVER_NAME = "feedback_agent"

    TOOL_DESCRIPTION = """
Complete 3D model quality evaluation workflow system with built-in rendering.

# Core Workflow
1. **3D Model Rendering**: Multi-angle rendering using built-in bpy-renderer
2. **Size Analysis**: Object size evaluation and assessment
3. **Position Analysis**: Object position evaluation and assessment  
4. **Scene Analysis**: Comprehensive scene-level quality evaluation
5. **Integrated Reporting**: Structured feedback with actionable recommendations

# Built-in Features
- Automatic 3D file detection from user input
- Direct rendering using bpy-renderer (no external tools required)
- Intelligent workspace management
- Structured evaluation workflow with size, position, and scene evaluation

# Input Format
- model_path: Path to 3D model file (obj, fbx, glb, gltf, ply, stl, blend)
- Optional workspace specification

# Output Features
- Standardized workspace creation with organized directory structure
- 6 high-quality render images (1024x1024 PNG, multiple camera angles)
- Structured size evaluation (object dimensions and standards compliance)
- Structured position evaluation (object positioning and standards compliance)
- Comprehensive scene evaluation (layout, relationships, aesthetics)
- Comprehensive YAML feedback report with scores and recommendations
- Complete file path tracking for all intermediate results

# Supported Model Formats
- OBJ files (.obj)
- FBX files (.fbx)
- GLTF/GLB files (.gltf, .glb)
- PLY files (.ply)
- STL files (.stl)
- Blender files (.blend)
- DAE/Collada files (.dae)

# Workspace Structure
```
3d_feedback_workspace/
└── {timestamp}_{model_name}/
    ├── renders/
    │   ├── render_0000.png  # Front view
    │   ├── render_0001.png  # 45° view
    │   ├── render_0002.png  # Side view
    │   ├── render_0003.png  # Back view
    │   ├── render_0004.png  # Other side view
    │   └── render_0005.png  # 315° view
    ├── evaluations/
    │   ├── size_analysis.yaml
    │   ├── position_analysis.yaml
    │   └── scene_analysis.yaml
    └── feedback_report.yaml
```

# Usage Examples
1. "Evaluate 3D model: /path/to/model.obj"
2. "Assess quality of /models/character.fbx"
3. "Generate feedback for scene.glb with detailed analysis"

# Quality Metrics
- Object size compliance with standards
- Object position appropriateness and functionality
- Scene coherence and spatial relationships
- Overall aesthetic and technical quality

Note: Built-in rendering requires bpy-renderer dependencies. Coordinates size, position, and scene evaluation tools.
"""

    @classmethod
    def create_config(cls):
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        load_dotenv()
        return ConfigManager(
            provider='qwen',
            deepseek_model='qwen-plus',
            max_iterations=15,  # Increased for multi-step workflow
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )
    
    @classmethod
    async def _run_interactive(cls):
        """Enhanced interactive mode with auto 3D file detection and built-in rendering"""
        print(f"\n{cls.__name__} Interactive Mode with Built-in Rendering")
        print("Type 'exit', 'quit', or 'bye' to end the conversation.")
        print("Simply mention any 3D file path and it will be automatically detected and evaluated!\n")
        
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
                    print("🚀 Starting automatic evaluation workflow...\n")
                    
                    for file_path in detected_files:
                        try:
                            # Step 1: Create workspace
                            workspace = create_workspace(file_path)
                            render_dir = os.path.join(workspace, "renders")
                            
                            print(f"📁 Created workspace: {workspace}")
                            print(f"📁 Rendering: {file_path}")
                            
                            # Step 2: Render using built-in function
                            result = render_mesh(file_path, render_dir)
                            print(f"✅ {result}\n")
                            
                            # Step 3: Process with agent for evaluation
                            enhanced_query = f"""
我已经自动渲染了3D文件：{file_path}
工作空间：{workspace}
渲染目录：{render_dir}
请继续进行尺寸评估、位置评估和场景评估，生成完整的反馈报告。
用户原始输入：{user_input}
"""
                            agent_result = await agent.process_query(enhanced_query)
                            print(f"Agent: {agent_result}")
                            
                        except Exception as e:
                            print(f"❌ Error processing {file_path}: {str(e)}\n")
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
        """Enhanced single query mode with auto 3D file detection and built-in rendering"""
        print(f"Processing query: {query}")
        
        # Auto-detect 3D files in query
        detected_files = detect_3d_files(query)
        
        if detected_files:
            print(f"\n🎯 Detected 3D files: {detected_files}")
            print("🚀 Starting automatic evaluation workflow...\n")
            
            for file_path in detected_files:
                try:
                    # Step 1: Create workspace
                    workspace = create_workspace(file_path)
                    render_dir = os.path.join(workspace, "renders")
                    
                    print(f"📁 Created workspace: {workspace}")
                    print(f"📁 Rendering: {file_path}")
                    
                    # Step 2: Render using built-in function
                    result = render_mesh(file_path, render_dir)
                    print(f"✅ {result}\n")
                    
                except Exception as e:
                    print(f"❌ Error processing {file_path}: {str(e)}\n")
        
        # Process with agent
        print("\nProcessing with agent...\n")
        agent = await cls.create_agent('agent')
        
        try:
            if detected_files:
                enhanced_query = f"""
我已经自动渲染了检测到的3D文件：{detected_files}
请继续进行尺寸评估、位置评估和场景评估，生成完整的反馈报告。
用户原始查询：{query}
"""
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
        """Custom main entry point that defaults to MCP server mode"""
        import argparse
        import asyncio
        from FractFlow.infra.logging_utils import setup_logging
        
        # Validate configuration
        cls._validate_configuration()
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(description=f'{cls.__name__} - 3D Model Evaluation with Built-in Rendering')
        parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
        parser.add_argument('--query', '-q', type=str, help='Single query mode: process this query and exit')
        parser.add_argument('--log-level', '-l', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Log level')
        args = parser.parse_args()
        
        # Setup logging
        setup_logging(level=args.log_level)
        
        if args.interactive:
            # Interactive mode
            print(f"Starting {cls.__name__} in interactive mode.")
            asyncio.run(cls._run_interactive())
        elif args.query:
            # Single query mode
            print(f"Starting {cls.__name__} in single query mode.")
            asyncio.run(cls._run_single_query(args.query))
        else:
            # Default: MCP server mode
            print(f"Starting {cls.__name__} in MCP server mode.")
            cls._run_mcp_server()

def create_workspace(model_path: str) -> str:
    """
    创建标准化的工作空间目录结构
    
    Args:
        model_path: 3D模型文件路径
        
    Returns:
        workspace_path: 创建的工作空间路径
    """
    model_name = Path(model_path).stem
    timestamp = int(time.time())
    workspace_name = f"{timestamp}_{model_name}"
    
    workspace_path = Path(f"./3d_feedback_workspace/{workspace_name}")
    
    # 创建目录结构
    workspace_path.mkdir(parents=True, exist_ok=True)
    (workspace_path / "renders").mkdir(exist_ok=True)
    (workspace_path / "evaluations").mkdir(exist_ok=True)
    
    return str(workspace_path)

def parse_markdown_feedback_to_yaml(text: str) -> str:
    """
    从 markdown 风格英文评估文本中抽取结构化字段并生成 YAML 字符串。
    字段包括 answer、confidence、visual_reference、success。
    """
    # 提取 Conclusion 段落
    conclusion_match = re.search(r'### Conclusion\n([\s\S]+?)(?:\n###|$)', text)
    if conclusion_match:
        answer = [conclusion_match.group(1).strip().replace('\n', ' ')]
    else:
        answer = ["No conclusion found"]

    # 提取 visual_reference（所有 ### n. **标题**）
    visual_refs = re.findall(r'### [0-9.]*\s*\*\*(.*?)\*\*', text)
    if not visual_refs:
        visual_refs = ["No visual reference found"]

    # confidence 统一设为 0.95
    confidences = [0.95] * len(answer)

    # success 规则：如 answer 含正面关键词则为 True，否则 False
    positive_keywords = ["well-designed", "pleasing", "harmonious", "excellent", "inviting", "stylish", "strong"]
    success = any(any(kw in a.lower() for kw in positive_keywords) for a in answer)

    data = {
        "answer": answer,
        "confidence": confidences,
        "visual_reference": visual_refs,
        "success": success
    }
    return yaml.dump(data, allow_unicode=True, sort_keys=False)

if __name__ == "__main__":
    FeedbackAgent.main() 