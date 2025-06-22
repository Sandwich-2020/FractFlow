"""
Asset Agent - Asset Management and Validation

This module provides a unified interface for Blender asset management that focuses on:
1. Asset source management and status checking
2. Intelligent asset search across multiple sources
3. Asset acquisition from PolyHaven, Sketchfab, and Hyper3D
4. Precise asset placement and comprehensive validation

Usage:
  python asset_agent.py                        # MCP Server mode (default)
  python asset_agent.py --interactive          # Interactive mode
  python asset_agent.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

ASSET_AGENT_SYSTEM_PROMPT = """
你是一个专业的3D资产管理和放置助手，专门负责在Blender场景中基于原始数据分析和管理3D资产。

## 核心能力：原始数据分析
你拥有强大的原始数值分析能力：
- 分析对象位置关系：从坐标数值判断对象间的空间关系
- 理解尺寸匹配：比较数值判断资产是否适合引导线
- 计算空间占用：从位置和尺寸计算对象的实际占用空间
- 识别占用状态：通过位置分析判断引导线是否被占用

## 数值分析示例
- 引导线：位置[2.0, 3.0, 0.0]，尺寸[2.0, 1.5, 0.5]
- 资产对象：位置[2.1, 2.9, 0.0]，尺寸[2.1, 1.6, 0.6]
- 分析结果：资产位置与引导线接近（距离约0.14米），尺寸相似，应该是占用了该引导线

## 空间关系判断
- 距离计算：√[(x2-x1)² + (y2-y1)² + (z2-z1)²]
- 重叠判断：比较对象边界是否有交集
- 尺寸匹配：判断资产尺寸是否符合引导线规格
- 朝向分析：从旋转数值理解对象朝向

## 工作流程
1. 获取引导线原始数据：位置、尺寸、旋转、元数据
2. 分析引导线空间要求：从数值理解空间需求
3. 选择合适资产：基于尺寸和类型匹配
4. 精确放置资产：使用引导线的坐标和旋转
5. 验证放置结果：检查位置和尺寸是否合理

## 可用工具
- `get_guide_info()`: 获取指定引导线的原始数据
- `list_available_guides()`: 获取所有引导线的原始数据
- `place_asset()`: 在指定位置放置资产
- `check_asset_sources_status()`: 检查资产源状态

## 引导线标识符理解
你能理解多种引导线标识符格式：
- 语义ID：bed_1, chair_2, table_1
- 中文描述：床1, 椅子2, 桌子1
- 自然语言：主卧的床, 客厅的椅子
- 完整名称：LAYOUT_GUIDE_bed_1234

## 资产放置原则
- 精确匹配：资产位置应与引导线位置一致
- 尺寸适配：资产尺寸应与引导线尺寸相匹配
- 朝向正确：根据引导线旋转设置资产朝向
- 命名规范：合并后的资产使用有意义的名称

## 数据分析方法
- 直接分析原始数值：不依赖预处理的"解释"
- 比较数值差异：判断对象间的相似性和差异
- 计算空间关系：用数学方法分析空间布局
- 推理占用状态：从位置和尺寸推断使用情况

## 交互示例
用户："把床放到bed_1的位置"
1. 获取bed_1的原始数据：位置[2.0, 3.0, 0.0]，尺寸[2.0, 1.5, 0.5]，旋转[0.0, 0.0, 1.57]
2. 分析空间要求：需要2×1.5米的床，旋转90度（1.57弧度）
3. 选择合适的床资产：尺寸匹配的双人床
4. 放置到精确位置：使用引导线的坐标和旋转
5. 验证结果：检查放置是否准确

## 合并和命名策略
- 智能合并：将多个相关部件合并为一个对象
- 语义命名：根据类型和位置生成有意义的名称
- 保持关联：合并后的对象应与原引导线保持关联

记住：你的优势在于理解和分析原始数值数据，从数值中发现空间关系和放置逻辑！
"""

class AssetAgent(ToolTemplate):
    """Blender asset management agent using ToolTemplate"""
    
    SYSTEM_PROMPT = ASSET_AGENT_SYSTEM_PROMPT
    
    TOOLS = [
        ("tools/core/blender_3/asset_mcp.py", "asset_manager")
    ]
    
    MCP_SERVER_NAME = "asset_agent"
    
    TOOL_DESCRIPTION = """Provides comprehensive asset management and validation for Blender scenes.
    
    This tool integrates multiple asset sources and provides complete asset lifecycle management:
    - Multi-source asset acquisition (PolyHaven, Sketchfab, Hyper3D)
    - Intelligent asset search and recommendations
    - Precise asset placement with validation
    - Comprehensive quality control and optimization
    - Batch asset management and monitoring
    
    Key Features:
        - Asset source status monitoring
        - Smart cross-platform asset search
        - Physics-based placement validation
        - Constraint satisfaction checking
        - Real-time asset optimization
        - Detailed validation reporting
        
    Asset Sources:
        - PolyHaven: High-quality textures, HDRIs, and models
        - Sketchfab: Extensive realistic model library
        - Hyper3D: AI-generated custom models
        
    Requirements:
        - Blender must be running with the MCP addon enabled
        - Asset source APIs configured as needed
        - Compatible with layout_agent for complete workflow
        
    Examples:
        - "Check all asset sources status"
        - "Search for modern chair assets"
        - "Place bed at position [2,3,0] with validation"
        - "Validate all assets in the scene"
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Asset agent"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=20,  # Asset operations might need more iterations
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    AssetAgent.main() 