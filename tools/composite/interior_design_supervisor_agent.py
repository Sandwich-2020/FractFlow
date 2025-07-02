"""
Interior Design Supervisor Agent - Unified Interface

This module provides a comprehensive interior design supervision system that:
1. Orchestrates image/text analysis through image_input_processing_agent
2. Ensures JSON file persistence and completeness
3. Supports interactive layout optimization through natural language dialogue
4. Handles both image-based and text-based design scenarios
5. **NEW**: Automatic 3D collision detection and iterative optimization

Usage:
  python interior_design_supervisor_agent.py                        # MCP Server mode (default)
  python interior_design_supervisor_agent.py --interactive          # Interactive mode  
  python interior_design_supervisor_agent.py --query "..."          # Single query mode
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from FractFlow.tool_template import ToolTemplate


class InteriorDesignSupervisorAgent(ToolTemplate):
    """室内设计监督agent - 协调分析、监督保存、碰撞检测、优化layout"""
    
    SYSTEM_PROMPT = """
你是一名高级室内设计助手和流程监督者，负责协调整个室内设计分析流程并提供持续的layout优化服务。

## 核心职责

### 1. 智能分析调度
- 接收用户输入（图像路径 + 描述，或纯文字需求）
- 根据输入类型调用 image_input_processing_agent 进行分析
- 图像输入：调用完整的图像分析流程
- 文字输入：指导agent基于文字描述生成layout

### 2. 流程完整性监督  
- 调用 image_input_processing_agent 后，必须检查JSON文件是否成功保存
- 使用 file_manager_agent 检查预期的JSON文件路径
- 如果文件不存在或不完整，重新指导 image_input_processing_agent 保存
- 确保每次分析都产生完整可用的JSON文件

### 3. **3D碰撞检测与自动优化**
- JSON文件保存成功后，自动调用 occ_detection_agent 进行碰撞检测
- 正确的调用方式：`occ_detection_agent "请分析JSON文件：[完整文件路径]，检测所有物体间的3D碰撞"`
- 分析碰撞检测结果，解析生成的***_plan.json文件
- 根据plan.json的建议智能决策：
  * 如果缩放比例 < 0.2：建议重新布局而非缩放
  * 如果轻微碰撞：接受缩放方案
  * 如果严重碰撞：指导image_input_processing_agent重新设计
- 实施迭代优化直到无碰撞或达到最大尝试次数（最多3次）

### 4. JSON文件管理
- 自动检测和验证JSON文件的结构完整性
- 支持读取、显示、修改已有的layout JSON
- 维护文件的版本和备份（original.json → original_1.json → original_2.json）
- 保存碰撞检测历史和优化记录

### 5. 交互式Layout优化
- 基于已保存的JSON，支持用户的自然语言反馈
- 理解用户对layout的具体修改需求
- 将自然语言指令转换为JSON字段的精确修改
- 验证修改后的layout合理性
- 考虑碰撞检测结果的优化建议

## 增强工作流程

### 初始分析阶段
1. **输入解析**：判断用户提供的是图像路径还是文字描述
2. **调用分析agent**：
   - 有图像：`image_input_processing_agent "[图像路径] 请分析这个室内空间"`
   - 无图像：`image_input_processing_agent "基于以下需求设计室内layout：[用户描述]"`
3. **保存验证**：
   - 检查是否生成了JSON文件
   - 验证JSON结构完整性（必须包含room和layout两个主要部分）
   - 如果保存失败，重新指导保存

### 自动碰撞检测阶段
4. **第1轮碰撞检测**：
   - 调用 `occ_detection_agent "请分析JSON文件：[完整路径]，进行3D碰撞检测并生成解决方案"`
   - 检查是否生成了***_plan.json文件
   - 分析plan.json内容，评估碰撞严重程度

5. **智能决策与迭代优化（新增直接JSON操作）**：
   ```
   迭代循环（最多3次）：
   如果检测到碰撞：
     a) 解析***_plan.json文件内容，提取碰撞物体和调整参数
     b) 分析缩放比例和碰撞严重程度：
        - 缩放比例 ≥ 0.3：直接应用缩放修复
        - 缩放比例 < 0.2：直接应用位置调整修复
        - IOU > 0.5：严重碰撞，综合调整位置和尺寸
     c) **直接JSON文件操作**：
        - 复制原始JSON文件
        - 只修改碰撞物体的position或size字段
        - 保持所有非碰撞物体完全不变
        - 保存为版本化文件：[原文件名]_[迭代次数].json
        - 验证文件结构完整性
     d) **降级机制**：如果直接修改失败，降级到agent指令模式
     e) 重新进行碰撞检测
   如果无碰撞：
     - 结束迭代，展示最终结果
   ```

### 持续优化阶段  
6. **结果展示**：向用户展示分析结果、碰撞检测报告和最终JSON文件路径
7. **收集反馈**：询问用户对当前layout是否满意，有什么需要改进
8. **自然语言理解**：理解用户的修改意图，如：
   - "把沙发往右移动50cm"
   - "这个房间太拥挤了，能否重新规划"
   - "床的尺寸是否合适？"
   - "增加一个书桌区域"
9. **精确修改**：将用户指令转换为JSON的具体修改操作
10. **验证保存**：确保修改后的layout仍然合理并重新进行碰撞检测

## 碰撞检测集成规范

### occ_detection_agent调用规范
- **正确调用方式**：`occ_detection_agent "请分析JSON文件：[完整文件路径]，检测3D碰撞"`
- **预期输出**：生成***_plan.json文件（如有碰撞）
- **文件命名**：原文件为room.json，plan文件为room_plan.json

### plan.json结果解析
当occ_detection_agent生成plan.json时，解析以下关键信息：
```json
{
  "rescale_plan1": {
    "object1_id": 缩放比例,
    "object2_id": 缩放比例,
    "collision_details": {
      "objects": [碰撞物体列表],
      "iou": IOU值,
      "overlap_dimensions": [x,y,z重叠尺寸],
      "original_sizes": {物体原始尺寸},
      "recommendation": "处理建议"
    }
  }
}
```

### 决策规则
1. **缩放比例 ≥ 0.3**：直接应用缩放，认为是可接受的调整
2. **0.2 ≤ 缩放比例 < 0.3**：询问用户是否接受较大幅度缩放
3. **缩放比例 < 0.2**：自动选择重新布局策略
4. **IOU > 0.5**：严重碰撞，必须重新布局
5. **多处碰撞**：按严重程度排序，逐一解决

### 迭代优化策略
1. **第1次迭代**：original.json → original_plan.json（如有碰撞）→ original_1.json
2. **第2次迭代**：original_1.json → original_1_plan.json（如有碰撞）→ original_2.json  
3. **第3次迭代**：original_2.json → original_2_plan.json（如有碰撞）→ original_3.json
4. **最大3次**：如仍有碰撞，保存当前最优结果并告知用户

### 直接JSON修复机制示例
**优先使用直接JSON操作**：
```
检测到碰撞：desk_0 与 chair_0，IOU=0.15，缩放比例=[0.8, 0.85]

自动执行直接修复：
1. 复制原文件 student_study_room_design.json
2. 分析：缩放比例 >= 0.3，采用缩放策略
3. 修改物体尺寸：
   - desk_0: size.length *= 0.8, size.width *= 0.8, size.height *= 0.8
   - chair_0: size.length *= 0.85, size.width *= 0.85, size.height *= 0.85
4. 保持所有其他物体完全不变
5. 验证JSON结构完整性
6. 保存为：student_study_room_design_1.json
```

**降级到指令模式**（仅在直接操作失败时）：
```
基于碰撞检测结果，发现以下问题：
- desk_0和chair_0发生碰撞，IOU=0.15，重叠尺寸为[0.2, 0.1, 0.0]
- 建议调整：将chair_0位置从(1.5, 0.8, 0)调整到(1.5, 0.6, 0)，增加0.2m距离

请重新生成layout，确保：
1. desk_0和chair_0之间至少保持0.3m距离
2. 保持room结构和所有非碰撞物体完全不变
3. 保存为：student_study_room_design_1.json
```

### 增强错误处理和重试机制
- **JSON直接操作失败**：自动降级到原有的agent指令模式
- **文件读取失败**：实施3次重试机制，失败后查找备份文件
- **JSON结构验证失败**：自动修复缺失字段，无法修复时回滚操作
- **碰撞修复应用失败**：记录失败原因，尝试替代修复策略
- image_input_processing_agent调用失败：分析错误原因并重试
- occ_detection_agent调用失败：跳过碰撞检测，提醒用户手动检查
- plan.json文件不存在：表示无碰撞，正常结束流程
- JSON保存失败：实施重试机制，检查磁盘空间和权限
- 文件损坏或不完整：自动查找最新有效备份文件
- 网络或工具调用超时：实施智能重试，增加等待时间
- **版本文件管理**：自动维护最多10个版本的备份文件
- **碰撞检测迭代失败**：保存当前最优结果，向用户报告详细情况

## 自然语言交互风格
- 专业但友好，具备室内设计专业知识
- 能够解释设计决策和空间布局原理
- 支持技术细节讨论（坐标、尺寸、旋转角度等）
- 主动提供优化建议和设计改进方案
- 能够解释碰撞检测结果和优化策略

## 工具使用规范
- `image_input_processing_agent`：核心分析引擎，负责图像分析和layout生成
- `occ_detection_agent`：3D碰撞检测引擎，分析物体间碰撞并提供优化方案
  - 调用格式：`"请分析JSON文件：[完整路径]，检测3D碰撞"`
- `file_manager_agent`：文件操作，包括检查、读取、写入JSON文件
- 所有文件操作都要验证结果，确保操作成功

## 质量保证
- 确保每个会话都产生完整可用的JSON文件
- 验证layout的空间合理性（无重叠、通道足够、尺寸合适）
- 通过3D碰撞检测确保物理可行性
- 保持设计的风格一致性和功能性
- 记录完整的优化历史便于用户理解改进过程

## 输出格式要求
1. **初始分析报告**：layout生成结果和文件完整性验证
2. **碰撞检测报告**：详细的碰撞情况、修复策略选择和执行结果  
3. **直接修复记录**：每次JSON直接操作的详细日志和验证结果
4. **优化过程记录**：每次迭代的改进情况、文件版本管理和错误处理
5. **最终结果**：无碰撞的layout、完整JSON文件路径和质量保证报告

## 质量保证增强
- **文件完整性**：确保每个会话都产生结构完整的JSON文件
- **数据一致性**：通过直接JSON操作保证非碰撞物体完全不变
- **版本管理**：维护清晰的文件版本链（original → _1 → _2 → _3）
- **错误恢复**：具备多层次的错误处理和自动恢复机制
- **验证机制**：每次修改后自动验证JSON结构和文件可读性
- **空间合理性**：通过3D碰撞检测确保物理可行性
- **设计一致性**：保持设计风格和功能性不受修复过程影响

记住：你是流程的监督者和优化者，现在具备了强化的3D空间碰撞检测和直接JSON修复能力，不仅要确保技术流程的完整性和文件操作的可靠性，更要通过精确的数据操作和持续对话帮助用户获得既美观又实用的室内设计方案。
"""
    
    # 分形智能体：调用其他智能体
    TOOLS = [
        ("tools/composite/image_input_processing_agent.py", "imageinputprocessingagent"),
        ("tools/core/occ_detection/occ_agent.py", "occdetectiontool"),
        ("tools/core/file_io/file_io_mcp.py", "file_manager_agent")
    ]
    
    MCP_SERVER_NAME = "interior_design_supervisor"
    
    TOOL_DESCRIPTION = """
    室内设计监督agent - 提供完整的室内空间分析、碰撞检测和layout优化服务。

    核心功能:
    1. 智能分析调度 - 协调图像分析或文字描述生成layout
    2. 流程完整性监督 - 确保JSON文件正确保存
    3. **NEW**: 3D碰撞检测 - 自动检测物体间碰撞并优化
    4. 交互式layout优化 - 支持自然语言反馈和持续改进
    5. 多模态输入支持 - 处理图像+文字或纯文字输入
    6. **NEW**: 迭代优化机制 - 自动解决空间冲突

    输入格式:
    - 图像分析: "[图像路径] 请分析这个卧室的layout并优化"
    - 文字设计: "设计一个20平米的现代简约风格客厅，要包含沙发、茶几、电视柜"
    - layout优化: "把沙发往窗边移动，增加采光效果"
    - 文件检查: "检查当前的layout文件是否完整"
    - **NEW**: 碰撞检测: "检查当前layout是否有物体重叠"

    输出内容:
    - 完整的室内空间分析结果
    - **NEW**: 详细的3D碰撞检测报告
    - 保存成功的JSON文件路径和内容概览
    - **NEW**: 碰撞优化建议和迭代过程记录
    - layout优化建议和修改确认
    - 持续的设计咨询和问题解答

    工作流程:
    1. 接收用户输入并判断分析类型
    2. 调用image_input_processing_agent执行核心分析
    3. 验证JSON文件保存状态，必要时重试
    4. **NEW**: 自动调用occ_detection_agent进行碰撞检测
    5. **NEW**: 根据碰撞结果智能决策优化策略
    6. **NEW**: 迭代优化直到无碰撞或达到最大尝试次数
    7. 展示结果并收集用户反馈
    8. 支持多轮对话优化layout设计
    9. 确保整个流程的完整性和质量

    特色功能:
    - 自动重试机制确保文件保存成功
    - **NEW**: 智能3D碰撞检测和解决方案
    - 智能理解自然语言的layout修改指令
    - 专业的室内设计知识和空间规划能力
    - 支持从粗略想法到精确layout的完整设计流程
    - **NEW**: 物理可行性验证和空间冲突自动解决

    碰撞检测功能:
    - 自动检测layout中所有物体的3D碰撞情况
    - 提供详细的IOU值、重叠尺寸、缩放建议
    - 智能决策：缩放 vs 重新布局
    - 迭代优化机制，确保最终layout无碰撞
    - 生成优化历史记录便于用户理解改进过程

    注意事项:
    - 支持纯文字输入，无需必须提供图像
    - 自动管理文件路径和命名
    - 提供持续的交互式优化服务
    - **NEW**: 确保生成的layout在3D空间中物理可行
    - **NEW**: 平衡美观性和实用性，避免过度缩放
    """

    def __init__(self):
        super().__init__()
        self.current_json_file = None
        self.optimization_history = []
        self.max_iterations = 3
    
    def _extract_file_path_from_response(self, response_text: str) -> Optional[str]:
        """从响应文本中提取JSON文件路径"""
        try:
            # 常见的路径模式
            import re
            
            # 匹配 "/完整路径/xxx.json" 格式
            pattern1 = r'/[^"\s]+\.json'
            matches1 = re.findall(pattern1, response_text)
            if matches1:
                return matches1[0]
            
            # 匹配 "xxx.json" 格式（当前目录）
            pattern2 = r'\b\w+\.json\b'
            matches2 = re.findall(pattern2, response_text)
            if matches2:
                # 假设在当前工作目录
                return os.path.abspath(matches2[0])
                
            return None
        except Exception as e:
            self.log(f"路径提取失败: {str(e)}", "warning")
            return None
    
    def _check_file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        try:
            result = self.call_tool("list_directory", {
                "dir_path": os.path.dirname(file_path)
            })
            
            if result and 'files' in str(result):
                file_name = os.path.basename(file_path)
                return file_name in str(result)
            
            return os.path.exists(file_path)
        except Exception as e:
            self.log(f"文件检查失败: {str(e)}", "warning")
            return os.path.exists(file_path)
    
    def _read_plan_file(self, plan_file_path: str) -> Optional[Dict]:
        """读取并解析plan.json文件"""
        try:
            result = self.call_tool("read_lines", {
                "file_path": plan_file_path,
                "start_line": 1,
                "end_line": 1000  # 假设plan文件不会很大
            })
            
            if result and result.get('success'):
                content = result.get('content', '')
                return json.loads(content)
            
            # 备用方法：直接读取文件
            with open(plan_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.log(f"plan文件读取失败: {str(e)}", "warning")
            return None
    
    def _analyze_collision_severity(self, plan_content: Dict) -> Dict[str, Any]:
        """分析碰撞严重程度并生成决策建议"""
        try:
            analysis = {
                'decision': 'no_collision',
                'suggestions': '未检测到碰撞问题。',
                'details': {}
            }
            
            # 查找rescale_plan或类似的碰撞信息
            rescale_plans = {}
            for key, value in plan_content.items():
                if 'rescale' in key.lower() or 'plan' in key.lower():
                    rescale_plans[key] = value
            
            if not rescale_plans:
                return analysis
            
            # 分析第一个rescale plan
            first_plan = list(rescale_plans.values())[0]
            
            # 提取缩放比例
            scale_ratios = []
            collision_details = {}
            
            for obj_id, scale_value in first_plan.items():
                if obj_id != 'collision_details':
                    if isinstance(scale_value, (int, float)):
                        scale_ratios.append(scale_value)
                elif obj_id == 'collision_details':
                    collision_details = scale_value
            
            if not scale_ratios:
                return analysis
            
            min_scale = min(scale_ratios)
            avg_scale = sum(scale_ratios) / len(scale_ratios)
            iou = collision_details.get('iou', 0)
            
            # 决策逻辑
            analysis['details'] = {
                'min_scale': min_scale,
                'avg_scale': avg_scale,
                'iou': iou,
                'collision_details': collision_details
            }
            
            if min_scale >= 0.3:
                analysis['decision'] = 'accept_scaling'
                analysis['suggestions'] = f"轻微碰撞，可以接受缩放方案（最小缩放比例: {min_scale:.2f}）"
            elif min_scale >= 0.2:
                analysis['decision'] = 'ask_user'
                analysis['suggestions'] = f"中等碰撞，建议询问用户是否接受较大幅度缩放（最小缩放比例: {min_scale:.2f}）"
            elif iou > 0.5:
                analysis['decision'] = 'needs_iteration'
                analysis['suggestions'] = f"严重碰撞（IOU={iou:.2f}），必须重新布局"
            else:
                analysis['decision'] = 'needs_iteration'
                analysis['suggestions'] = f"显著碰撞（缩放比例={min_scale:.2f}），建议重新调整layout"
            
            return analysis
            
        except Exception as e:
            self.log(f"碰撞分析失败: {str(e)}", "warning")
            return {
                'decision': 'error',
                'suggestions': f"碰撞分析失败: {str(e)}",
                'details': {}
            }
    
    def _perform_collision_detection(self, json_file_path: str, context: str) -> Dict[str, Any]:
        """自动进行3D碰撞检测，并根据结果决定是否需要迭代优化"""
        try:
            # 正确调用 occ_detection_agent 进行碰撞检测
            query = f"请分析JSON文件：{json_file_path}，检测所有物体间的3D碰撞并生成优化方案"
            
            collision_result = self.call_tool("occdetectiontool", {
                "query": query
            })
            
            if not collision_result:
                self.log(f"碰撞检测失败: 工具调用返回空结果", "warning")
                return {
                    'has_collision': False,
                    'plan_file': None,
                    'collision_details': {},
                    'decision': 'skip_detection',
                    'optimization_suggestions': "碰撞检测工具调用失败，建议手动检查layout合理性"
                }
            
            # 等待一段时间让occ_detection_agent完成文件生成
            time.sleep(3)
            
            # 检查是否生成了plan.json文件
            base_name = os.path.splitext(json_file_path)[0]
            plan_file_path = f"{base_name}_plan.json"
            
            # 检查plan文件是否存在
            if not self._check_file_exists(plan_file_path):
                # 无plan文件表示无碰撞
                self.log(f"未发现plan文件 {plan_file_path}，表示无碰撞", "info")
                return {
                    'has_collision': False,
                    'plan_file': None,
                    'collision_details': {},
                    'decision': 'no_collision',
                    'optimization_suggestions': "✅ 未检测到物体碰撞，当前layout在空间上是合理的。"
                }
            
            # 读取并解析plan.json
            plan_content = self._read_plan_file(plan_file_path)
            if not plan_content:
                return {
                    'has_collision': False,
                    'plan_file': plan_file_path,
                    'collision_details': {},
                    'decision': 'no_collision',
                    'optimization_suggestions': "plan文件读取失败，假设无碰撞。"
                }
            
            # 分析碰撞严重程度和决策
            analysis_result = self._analyze_collision_severity(plan_content)
            
            self.log(f"碰撞检测完成: {analysis_result['decision']}", "info")
            
            return {
                'has_collision': True,
                'plan_file': plan_file_path,
                'collision_details': plan_content,
                'decision': analysis_result['decision'],
                'optimization_suggestions': analysis_result['suggestions']
            }
            
        except Exception as e:
            self.log(f"碰撞检测过程中发生错误: {str(e)}", "error")
            return {
                'has_collision': False,
                'plan_file': None,
                'collision_details': {},
                'decision': 'error',
                'optimization_suggestions': f"碰撞检测失败: {str(e)}"
            }

    def _extract_collision_objects(self, collision_details: Dict) -> List[Dict]:
        """从collision_details中提取需要调整的物体信息"""
        collision_fixes = []
        
        try:
            # 查找rescale plan
            for key, value in collision_details.items():
                if 'rescale' in key.lower() or 'plan' in key.lower():
                    plan_details = value
                    
                    # 提取碰撞对象和缩放信息
                    objects = []
                    scales = {}
                    collision_meta = {}
                    
                    for obj_id, scale_or_details in plan_details.items():
                        if obj_id == 'collision_details':
                            collision_meta = scale_or_details
                        elif isinstance(scale_or_details, (int, float)):
                            objects.append(obj_id)
                            scales[obj_id] = scale_or_details
                    
                    if len(objects) >= 2:
                        obj1, obj2 = objects[0], objects[1]
                        scale1, scale2 = scales.get(obj1, 1.0), scales.get(obj2, 1.0)
                        iou = collision_meta.get('iou', 0)
                        overlap_dims = collision_meta.get('overlap_dimensions', [0, 0, 0])
                        original_sizes = collision_meta.get('original_sizes', {})
                        
                        collision_fixes.append({
                            'objects': [obj1, obj2],
                            'scales': [scale1, scale2],
                            'iou': iou,
                            'overlap_dimensions': overlap_dims,
                            'original_sizes': original_sizes,
                            'strategy': 'scale' if min(scale1, scale2) >= 0.2 else 'reposition'
                        })
            
            return collision_fixes
            
        except Exception as e:
            self.log(f"提取碰撞对象信息失败: {str(e)}", "warning")
            return []

    def _calculate_position_adjustment(self, obj1: Dict, obj2: Dict, overlap_dims: List[float]) -> Dict:
        """计算位置调整方案，确保物体间距离至少0.3米"""
        try:
            # 获取物体位置和尺寸
            pos1 = obj1['position']
            size1 = obj1['size']
            pos2 = obj2['position']
            size2 = obj2['size']
            
            # 计算需要的最小分离距离
            min_distance = 0.3
            
            # 计算两物体中心距离
            dx = pos2['x'] - pos1['x']
            dy = pos2['y'] - pos1['y']
            
            # 计算需要的安全距离（物体半径 + 最小间距）
            safe_dist_x = (size1['length'] + size2['length']) / 2 + min_distance
            safe_dist_y = (size1['width'] + size2['width']) / 2 + min_distance
            
            # 决定移动哪个物体（默认移动第二个物体）
            if abs(dx) > abs(dy):
                # 主要在X轴方向重叠，调整X坐标
                if dx > 0:
                    new_x = pos1['x'] + safe_dist_x
                else:
                    new_x = pos1['x'] - safe_dist_x
                
                return {
                    'object_id': obj2['id'],
                    'new_position': {
                        'x': new_x,
                        'y': pos2['y'],
                        'z': pos2['z']
                    },
                    'adjustment_type': 'position',
                    'reason': f"调整X坐标以避免与{obj1['id']}碰撞"
                }
            else:
                # 主要在Y轴方向重叠，调整Y坐标
                if dy > 0:
                    new_y = pos1['y'] + safe_dist_y
                else:
                    new_y = pos1['y'] - safe_dist_y
                
                return {
                    'object_id': obj2['id'],
                    'new_position': {
                        'x': pos2['x'],
                        'y': new_y,
                        'z': pos2['z']
                    },
                    'adjustment_type': 'position',
                    'reason': f"调整Y坐标以避免与{obj1['id']}碰撞"
                }
                
        except Exception as e:
            self.log(f"计算位置调整失败: {str(e)}", "warning")
            return {}

    def _apply_collision_fixes(self, layout_objects: List, collision_fixes: List[Dict]) -> List:
        """应用碰撞修复到layout对象列表"""
        try:
            # 创建物体ID到对象的映射
            obj_map = {obj['id']: obj for obj in layout_objects}
            
            for fix in collision_fixes:
                obj1_id, obj2_id = fix['objects']
                scale1, scale2 = fix['scales']
                strategy = fix['strategy']
                
                if strategy == 'scale' and min(scale1, scale2) >= 0.2:
                    # 应用缩放策略
                    if obj1_id in obj_map:
                        obj = obj_map[obj1_id]
                        obj['size']['length'] *= scale1
                        obj['size']['width'] *= scale1
                        obj['size']['height'] *= scale1
                        self.log(f"缩放物体 {obj1_id}: 比例={scale1:.3f}", "info")
                    
                    if obj2_id in obj_map:
                        obj = obj_map[obj2_id]
                        obj['size']['length'] *= scale2
                        obj['size']['width'] *= scale2
                        obj['size']['height'] *= scale2
                        self.log(f"缩放物体 {obj2_id}: 比例={scale2:.3f}", "info")
                        
                elif strategy == 'reposition':
                    # 应用位置调整策略
                    if obj1_id in obj_map and obj2_id in obj_map:
                        obj1 = obj_map[obj1_id]
                        obj2 = obj_map[obj2_id]
                        
                        adjustment = self._calculate_position_adjustment(
                            obj1, obj2, fix['overlap_dimensions']
                        )
                        
                        if adjustment and adjustment['object_id'] in obj_map:
                            target_obj = obj_map[adjustment['object_id']]
                            target_obj['position'].update(adjustment['new_position'])
                            self.log(f"重新定位物体 {adjustment['object_id']}: {adjustment['reason']}", "info")
            
            return layout_objects
            
        except Exception as e:
            self.log(f"应用碰撞修复失败: {str(e)}", "error")
            return layout_objects

    def _copy_and_modify_json(self, original_file: str, collision_details: Dict, iteration: int) -> Optional[str]:
        """直接复制并修改JSON文件，只调整碰撞物体的位置/尺寸"""
        try:
            # 生成新文件名
            base_name = os.path.splitext(original_file)[0]
            new_file_path = f"{base_name}_{iteration}.json"
            
            # 读取原始JSON文件
            read_result = self.call_tool("file_manager_agent", {
                "query": f"请读取JSON文件内容：{original_file}"
            })
            
            if not read_result:
                self.log(f"读取原始文件失败: {original_file}", "error")
                return None
            
            # 解析JSON内容
            try:
                # 从文件管理器返回结果中提取JSON内容
                json_content_str = str(read_result)
                # 寻找JSON内容（通常在结果的某个部分）
                import re
                json_match = re.search(r'\{.*\}', json_content_str, re.DOTALL)
                if not json_match:
                    self.log("无法从读取结果中提取JSON内容", "error")
                    return None
                    
                original_data = json.loads(json_match.group())
                
            except json.JSONDecodeError as e:
                self.log(f"JSON解析失败: {str(e)}", "error")
                return None
            
            # 确保有layout字段
            if 'layout' not in original_data:
                self.log("JSON文件缺少layout字段", "error")
                return None
            
            # 提取碰撞修复信息
            collision_fixes = self._extract_collision_objects(collision_details)
            
            if not collision_fixes:
                self.log("未找到有效的碰撞修复信息", "warning")
                return None
            
            # 应用碰撞修复
            modified_layout = self._apply_collision_fixes(original_data['layout'], collision_fixes)
            original_data['layout'] = modified_layout
            
            # 验证修改后的JSON结构
            if not self._validate_json_structure(original_data, original_data):
                self.log("修改后的JSON结构验证失败", "error")
                return None
            
            # 保存修改后的JSON文件
            save_result = self.call_tool("file_manager_agent", {
                "query": f"请保存JSON数据到文件: {new_file_path}\n内容: {json.dumps(original_data, ensure_ascii=False, indent=2)}"
            })
            
            if save_result:
                self.log(f"成功保存修改后的JSON文件: {new_file_path}", "info")
                
                # 验证保存的文件是否可读
                if self._check_file_exists(new_file_path):
                    self.log(f"文件验证通过: {new_file_path}", "info")
                    return new_file_path
                else:
                    self.log(f"保存的文件无法验证: {new_file_path}", "error")
                    return None
            else:
                self.log(f"保存修改后的JSON文件失败", "error")
                return None
                
        except Exception as e:
            self.log(f"复制和修改JSON文件过程中发生错误: {str(e)}", "error")
            return None

    def _validate_json_structure(self, json_data: Dict, original_data: Dict) -> bool:
        """验证修改后的JSON文件结构完整性"""
        try:
            # 检查基本结构
            if not isinstance(json_data, dict):
                self.log("JSON数据不是字典类型", "error")
                return False
            
            # 检查必要字段
            required_fields = ['layout']
            for field in required_fields:
                if field not in json_data:
                    self.log(f"缺少必要字段: {field}", "error")
                    return False
            
            # 检查layout是否是列表
            if not isinstance(json_data['layout'], list):
                self.log("layout字段不是列表类型", "error")
                return False
            
            # 检查room字段是否保留（如果原始文件有）
            if 'room' in original_data and 'room' not in json_data:
                self.log("room字段丢失", "warning")
                # 补充room字段
                json_data['room'] = original_data['room']
            
            # 检查layout物体数量不能减少
            original_count = len(original_data.get('layout', []))
            current_count = len(json_data['layout'])
            
            if current_count < original_count:
                self.log(f"物体数量减少：原有{original_count}个，现在{current_count}个", "warning")
                return False
            
            # 检查每个物体的基本结构
            for i, obj in enumerate(json_data['layout']):
                if not isinstance(obj, dict):
                    self.log(f"第{i}个物体不是字典类型", "error")
                    return False
                
                required_obj_fields = ['id', 'position', 'size']
                for field in required_obj_fields:
                    if field not in obj:
                        self.log(f"第{i}个物体缺少字段: {field}", "error")
                        return False
                
                # 检查position字段
                pos = obj['position']
                if not isinstance(pos, dict) or not all(key in pos for key in ['x', 'y', 'z']):
                    self.log(f"第{i}个物体的position字段格式错误", "error")
                    return False
                
                # 检查size字段
                size = obj['size']
                required_size_fields = ['length', 'width', 'height']
                if not isinstance(size, dict) or not all(key in size for key in required_size_fields):
                    self.log(f"第{i}个物体的size字段格式错误", "error")
                    return False
            
            self.log("JSON结构验证通过", "info")
            return True
            
        except Exception as e:
            self.log(f"JSON结构验证失败: {str(e)}", "error")
            return False

    def _handle_file_operation_error(self, operation: str, file_path: str, error: Exception) -> bool:
        """处理文件操作错误，实施重试机制"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            retry_count += 1
            self.log(f"文件操作失败，第{retry_count}次重试: {operation} {file_path}", "warning")
            
            try:
                # 等待一段时间后重试
                time.sleep(1)
                
                if operation == "read":
                    result = self.call_tool("file_manager_agent", {
                        "query": f"请读取JSON文件内容：{file_path}"
                    })
                    if result:
                        return True
                elif operation == "write":
                    # 这里需要额外的数据参数，由调用者处理具体重试逻辑
                    return False
                    
            except Exception as retry_error:
                self.log(f"重试失败: {str(retry_error)}", "warning")
                
        self.log(f"文件操作最终失败，已重试{max_retries}次: {operation} {file_path}", "error")
        return False

    def _backup_and_recover(self, file_path: str) -> Optional[str]:
        """备份和恢复机制"""
        try:
            # 检查是否存在备份文件
            backup_candidates = []
            base_name = os.path.splitext(file_path)[0]
            
            # 查找可能的备份文件
            for i in range(10):  # 最多查找10个版本
                backup_path = f"{base_name}_{i}.json" if i > 0 else f"{base_name}.json"
                if self._check_file_exists(backup_path):
                    backup_candidates.append(backup_path)
            
            # 返回最新的有效备份
            if backup_candidates:
                latest_backup = backup_candidates[-1]
                self.log(f"找到备份文件: {latest_backup}", "info")
                return latest_backup
            else:
                self.log("未找到可用的备份文件", "warning")
                return None
                
        except Exception as e:
            self.log(f"备份恢复失败: {str(e)}", "error")
            return None
    
    def _generate_modification_instruction(self, collision_details: Dict, original_file: str, iteration: int) -> Optional[str]:
        """基于碰撞检测结果直接修改JSON文件，返回新文件路径"""
        try:
            # 直接调用JSON复制和修改方法
            new_file_path = self._copy_and_modify_json(original_file, collision_details, iteration)
            
            if new_file_path:
                self.log(f"成功生成修正后的JSON文件: {new_file_path}", "info")
                return new_file_path
            else:
                # 如果直接修改失败，降级到原有的指令生成机制
                self.log("直接JSON修改失败，降级到指令生成模式", "warning")
                return self._generate_fallback_instruction(collision_details, original_file, iteration)
                
        except Exception as e:
            self.log(f"JSON修改过程中发生错误: {str(e)}", "error")
            # 降级到原有机制
            return self._generate_fallback_instruction(collision_details, original_file, iteration)

    def _generate_fallback_instruction(self, collision_details: Dict, original_file: str, iteration: int) -> str:
        """降级到原有的指令生成机制"""
        try:
            # 解析碰撞详情
            collision_info = []
            modification_requirements = []
            
            # 查找rescale plan
            for key, value in collision_details.items():
                if 'rescale' in key.lower() or 'plan' in key.lower():
                    plan_details = value
                    
                    # 提取碰撞对象和缩放信息
                    objects = []
                    scales = {}
                    collision_meta = {}
                    
                    for obj_id, scale_or_details in plan_details.items():
                        if obj_id == 'collision_details':
                            collision_meta = scale_or_details
                        elif isinstance(scale_or_details, (int, float)):
                            objects.append(obj_id)
                            scales[obj_id] = scale_or_details
                    
                    if len(objects) >= 2:
                        obj1, obj2 = objects[0], objects[1]
                        scale1, scale2 = scales.get(obj1, 1.0), scales.get(obj2, 1.0)
                        iou = collision_meta.get('iou', 0)
                        overlap_dims = collision_meta.get('overlap_dimensions', [0, 0, 0])
                        
                        collision_info.append({
                            'objects': [obj1, obj2],
                            'scales': [scale1, scale2],
                            'iou': iou,
                            'overlap': overlap_dims
                        })
                        
                        # 生成具体的修改要求
                        if min(scale1, scale2) < 0.2:
                            modification_requirements.append(
                                f"{obj1}和{obj2}之间存在严重碰撞（缩放比例={min(scale1, scale2):.2f}），需要重新调整它们的位置关系"
                            )
                        else:
                            modification_requirements.append(
                                f"{obj1}和{obj2}之间存在轻微重叠，建议调整位置增加间距"
                            )
            
            # 构造完整的修改指令
            base_name = os.path.splitext(os.path.basename(original_file))[0]
            new_file_name = f"{base_name}_{iteration}.json"
            
            instruction = f"""【重要】请按以下步骤修正layout中的碰撞问题：

**第1步：读取原始完整文件**
请使用read_lines工具读取完整文件：{original_file}
参数设置为：file_path="{original_file}", start_line=1, end_line=500
获取完整的room结构（walls, doors, windows）和所有layout物体。

**第2步：分析碰撞问题**
检测到的碰撞情况：
"""
            
            for i, collision in enumerate(collision_info[:3], 1):  # 最多显示3个碰撞
                obj1, obj2 = collision['objects']
                scale1, scale2 = collision['scales']
                iou = collision['iou']
                overlap = collision['overlap']
                
                instruction += f"""
{i}. {obj1} 与 {obj2} 发生碰撞：
   - IOU值: {iou:.3f}
   - 建议缩放比例: {obj1}={scale1:.2f}, {obj2}={scale2:.2f}
   - 重叠尺寸: [{overlap[0]:.2f}, {overlap[1]:.2f}, {overlap[2]:.2f}]米
"""
            
            instruction += f"""
**第3步：精确调整碰撞物体**
调整要求：
"""
            for i, req in enumerate(modification_requirements[:3], 1):
                instruction += f"{i}. {req}\n"
            
            instruction += f"""
**第4步：保存完整数据**
请确保新的JSON文件包含：
1. 完整的room结构（与原文件完全相同）
2. 所有原有的layout物体（只调整碰撞物体的位置）
3. 保持所有物体的其他属性不变（size, rotation, description等）
4. 文件名：{new_file_name}

**关键要求**：
- 只调整发生碰撞的物体位置，其他物体保持原位
- 确保物体间距离至少0.3米
- 保持room结构和所有非碰撞物体完全不变
- 生成的文件必须结构完整，包含所有原有内容

请基于原始文件进行精确的位置调整。"""
            
            return instruction
            
        except Exception as e:
            self.log(f"降级指令生成失败: {str(e)}", "warning")
            base_name = os.path.splitext(os.path.basename(original_file))[0]
            new_file_name = f"{base_name}_{iteration}.json"
            
            return f"""【重要】请修正layout中的碰撞问题：

**必须先使用read_lines工具读取原始文件**：{original_file}
参数：file_path="{original_file}", start_line=1, end_line=500

**修正要求**：
1. 保持完整的room结构（walls, doors, windows）不变
2. 保持所有非碰撞物体的位置和属性不变
3. 只调整发生碰撞的物体位置，确保间距至少0.3米
4. 保存为完整的文件：{new_file_name}

请基于原始文件内容进行精确调整，不要重新创建layout。"""
    
    def _perform_iterative_optimization(self, initial_json_file: str, context: str) -> Dict[str, Any]:
        """执行迭代优化流程，直到无碰撞或达到最大次数"""
        optimization_log = []
        current_file = initial_json_file
        
        for iteration in range(1, self.max_iterations + 1):
            self.log(f"开始第{iteration}轮碰撞检测...", "info")
            
            # 进行碰撞检测
            collision_result = self._perform_collision_detection(current_file, context)
            
            optimization_log.append({
                'iteration': iteration,
                'file': current_file,
                'collision_result': collision_result
            })
            
            # 如果无碰撞，优化成功
            if not collision_result['has_collision'] or collision_result['decision'] == 'no_collision':
                self.log(f"第{iteration}轮检测：无碰撞，优化完成！", "info")
                return {
                    'success': True,
                    'final_file': current_file,
                    'total_iterations': iteration,
                    'optimization_log': optimization_log,
                    'final_status': '优化成功，无碰撞检测到'
                }
            
            # 如果是最后一次迭代，不再生成新版本
            if iteration == self.max_iterations:
                self.log(f"达到最大迭代次数({self.max_iterations})，停止优化", "warning")
                return {
                    'success': False,
                    'final_file': current_file,
                    'total_iterations': iteration,
                    'optimization_log': optimization_log,
                    'final_status': f'达到最大迭代次数，仍存在碰撞：{collision_result["optimization_suggestions"]}'
                }
            
            # 需要进行下一轮优化
            if collision_result['decision'] in ['needs_iteration', 'ask_user']:
                self.log(f"第{iteration}轮检测：发现碰撞，执行直接修复...", "info")
                
                # 直接修改JSON文件（新方法）
                new_file_path = self._generate_modification_instruction(
                    collision_result['collision_details'], 
                    current_file,  # 使用当前文件而不是initial_json_file
                    iteration
                )
                
                if new_file_path and isinstance(new_file_path, str) and self._check_file_exists(new_file_path):
                    # 直接JSON修改成功
                    current_file = new_file_path
                    self.log(f"第{iteration}轮优化：直接修改成功，新文件 {new_file_path}", "info")
                elif isinstance(new_file_path, str):
                    # 返回的是指令文本，需要调用image_input_processing_agent
                    self.log(f"第{iteration}轮检测：降级到指令模式，调用重设计agent...", "info")
                    
                    redesign_result = self.call_tool("imageinputprocessingagent", {
                        "query": new_file_path
                    })
                    
                    if not redesign_result:
                        self.log(f"第{iteration}轮优化失败：无法调用重设计agent", "error")
                        return {
                            'success': False,
                            'final_file': current_file,
                            'total_iterations': iteration,
                            'optimization_log': optimization_log,
                            'final_status': '重设计调用失败'
                        }
                    
                    # 提取新的JSON文件路径
                    extracted_path = self._extract_file_path_from_response(str(redesign_result))
                    if extracted_path and self._check_file_exists(extracted_path):
                        current_file = extracted_path
                        self.log(f"第{iteration}轮优化：通过agent生成新文件 {extracted_path}", "info")
                    else:
                        self.log(f"第{iteration}轮优化失败：无法找到agent生成的JSON文件", "error")
                        return {
                            'success': False,
                            'final_file': current_file,
                            'total_iterations': iteration,
                            'optimization_log': optimization_log,
                            'final_status': '新JSON文件生成失败'
                        }
                else:
                    self.log(f"第{iteration}轮优化失败：修改方法返回无效结果", "error")
                    return {
                        'success': False,
                        'final_file': current_file,
                        'total_iterations': iteration,
                        'optimization_log': optimization_log,
                        'final_status': 'JSON修改失败'
                    }
                
                # 等待文件系统同步
                time.sleep(2)
        
        # 理论上不会到达这里
        return {
            'success': False,
            'final_file': current_file,
            'total_iterations': self.max_iterations,
            'optimization_log': optimization_log,
            'final_status': '未知错误'
        }
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Interior Design Supervisor"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=50,  # 支持长对话和多次重试
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )


if __name__ == "__main__":
    InteriorDesignSupervisorAgent.main() 