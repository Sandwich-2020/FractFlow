"""
Deep Research Agent - Unified Multi-Modal Research Interface

This module provides a unified interface for comprehensive research that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced deep research as MCP tools
2. Interactive mode: Runs as an interactive agent with deep research capabilities
3. Single query mode: Processes a single query and exits

The agent implements a multi-layered research architecture:
- Information Gathering Layer: Web search, document analysis, visual content processing
- Analysis Layer: Data synthesis, pattern recognition, cross-referencing
- Synthesis Layer: Knowledge integration, insight generation, hypothesis formation
- Output Layer: Structured reporting, visualization, actionable recommendations

Usage:
  python deep_research_agent.py                        # MCP Server mode (default)
  python deep_research_agent.py --interactive          # Interactive mode
  python deep_research_agent.py --query "..."          # Single query mode

Examples:
  # Comprehensive topic research
  python deep_research_agent.py -q "研究人工智能在医疗领域的最新发展趋势"
  
  # Visual content analysis research
  python deep_research_agent.py -q "分析这张图片的技术原理并研究相关背景 Image: /path/to/image.jpg"
  
  # Multi-source information synthesis
  python deep_research_agent.py -q "从多个角度深度研究区块链技术的发展前景"
  
  # Research with structured output
  python deep_research_agent.py -q "研究可持续能源技术并生成完整报告到 sustainable_energy_report.md"
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class DeepResearchAgent(ToolTemplate):
    """Deep research tool using ToolTemplate with multi-layered research methodology"""
    
    SYSTEM_PROMPT = """
你是一个多模态深度研究专家，通过协调多个专业工具进行全面的研究分析。

# 核心研究方法论

## 第一层：信息收集 (Information Gathering)
- **网络搜索**: 使用search_agent获取最新、权威的网络信息
- **文档分析**: 通过file_manager处理和分析各类文档
- **视觉内容处理**: 使用visual_question_answering分析图像、图表和视觉资料
- **多源交叉验证**: 从不同渠道收集信息进行对比验证

## 第二层：深度分析 (Deep Analysis) 
- **数据综合**: 整合来自不同工具的信息，识别关键模式和趋势
- **关联分析**: 发现不同信息源之间的内在联系
- **批判性评估**: 评估信息的可靠性、准确性和相关性
- **问题解构**: 将复杂研究问题分解为可管理的子问题

## 第三层：知识综合 (Knowledge Synthesis)
- **洞察生成**: 基于收集的数据产生原创性见解
- **假设形成**: 提出基于证据的假设和理论框架  
- **趋势预测**: 基于当前数据预测未来发展趋势
- **跨领域连接**: 识别不同领域之间的关联和启发

## 第四层：结构化输出 (Structured Output)
- **报告生成**: 创建结构化、专业的研究报告
- **可视化支持**: 生成图表、图像来支持分析结果
- **行动建议**: 提供具体、可执行的建议和下一步方案
- **知识管理**: 将研究结果系统性地保存和组织

# 工具协调策略

## 智能工具选择
根据研究需求动态选择最适合的工具组合：

### 文献研究型任务
1. search_agent → 搜索相关文献和资料
2. file_manager → 保存和整理研究材料  
3. file_manager → 生成结构化研究报告

### 多模态分析型任务  
1. visual_question_answering → 分析图像/视频内容
2. search_agent → 搜索相关背景信息
3. file_manager → 整合分析结果

### 综合调研型任务
1. search_agent → 多轮深度搜索
2. visual_question_answering → 处理视觉资料
3. file_manager → 数据管理和报告生成

## 迭代研究流程
- **初步调研**: 获取主题的基础信息和概述
- **深度挖掘**: 针对关键方面进行专门研究
- **交叉验证**: 通过多个来源验证关键发现
- **综合分析**: 整合所有信息形成完整认知
- **输出优化**: 创建清晰、有价值的最终产出

# 质量控制标准

## 信息可靠性
- 优先使用权威来源和官方资料
- 交叉验证关键信息的准确性
- 明确标注信息的来源和时效性
- 识别和处理潜在的偏见或不准确信息

## 分析深度
- 不满足于表面信息，持续深入挖掘
- 寻找数据背后的深层含义和规律
- 考虑多个角度和利益相关者的观点
- 提供基于证据的结论和建议

## 输出质量
- 结构清晰、逻辑严密的报告格式
- 适当的可视化支持和数据呈现
- 具体、可操作的建议和结论
- 专业的语言表达和学术规范

# 特殊场景处理

## 紧急研究请求
- 快速定位最权威的信息源
- 并行处理多个研究维度
- 优先输出核心发现和建议

## 争议性话题研究
- 寻求多元化的观点和立场
- 客观呈现不同观点的论据
- 基于事实进行中性分析

## 技术性深度研究
- 重点关注最新的技术发展和趋势
- 结合理论基础和实际应用案例
- 提供技术实现的可行性分析

# 输出要求

✅ 必须完成的任务：
- 使用工具进行实际的信息收集和分析
- 生成结构化、专业的研究输出
- 提供明确的信息来源引用
- 包含具体的发现和建议

❌ 严禁的行为：
- 直接输出未经工具验证的信息
- 仅基于训练数据的回答，不进行实际搜索
- 跳过工具调用步骤
- 提供模糊、不具体的分析结果

# 协作模式
作为深度研究专家，我会：
- 主动使用工具获取最新、准确的信息
- 系统性地分析和综合研究结果
- 创建有价值的知识产品
- 支持用户的学习和决策需求
"""
    
    TOOLS = [
        ("tools/core/websearch/websearch_agent.py", "search_agent"),
        ("tools/core/file_io/file_io_mcp.py", "file_manager"),
        ("tools/core/visual_question_answer/vqa_mcp.py", "visual_question_answering")
        ]
    
    MCP_SERVER_NAME = "deep_research_agent"
    
    TOOL_DESCRIPTION = """
多模态深度研究系统，整合网络搜索、文档分析、视觉处理和报告生成能力。

# 研究能力矩阵

## 信息收集维度
- **网络调研**: 实时搜索最新信息、权威资料和专业文献
- **文档处理**: 读取、分析和整理各类研究材料
- **视觉分析**: 处理图像、图表、视频等多媒体内容
- **数据验证**: 多源交叉验证确保信息准确性

## 分析处理维度  
- **趋势分析**: 识别发展趋势和变化模式
- **关联挖掘**: 发现概念、事件之间的深层联系
- **批判评估**: 客观评价信息质量和可信度
- **洞察生成**: 产生原创性的分析观点

## 输出创作维度
- **结构化报告**: 专业格式的研究报告和分析文档
- **可视化图表**: 支持分析的图像、图表和概念图
- **知识图谱**: 系统性的知识结构和关系图
- **行动建议**: 具体可执行的建议和方案

# 适用研究场景

## 学术研究
- 文献综述和前沿动态调研
- 跨学科知识整合和分析
- 研究方法论和理论框架构建

## 商业智能
- 市场分析和竞争对手研究  
- 行业趋势和商业机会识别
- 战略规划和决策支持

## 技术调研
- 新兴技术发展现状和趋势
- 技术可行性和应用场景分析
- 技术选型和实施建议

## 政策分析
- 政策影响和实施效果评估
- 国际对比和最佳实践研究
- 政策建议和改进方案

# 输入格式
直接描述您的研究需求，例如：
- "深度研究人工智能在教育领域的应用现状和发展趋势"
- "分析可持续发展目标的全球实施进展，生成完整报告"
- "研究区块链技术的最新突破，包括技术分析和市场应用"
- "Image: /path/to/chart.jpg 分析这个图表并研究相关的行业背景"

# 输出保证
- 基于实际工具调用的最新信息
- 结构化的专业分析报告
- 明确的信息来源和引用
- 具体的发现总结和建议
- 必要时包含可视化支持材料
"""
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Deep Research Agent"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=30,  # Deep research requires extensive iterations
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    DeepResearchAgent.main()
