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

5. **智能决策与迭代优化**：
   ```
   迭代循环（最多3次）：
   如果检测到碰撞：
     a) 解析***_plan.json文件内容
     b) 分析缩放比例和碰撞详情：
        - 缩放比例 ≥ 0.3：可接受，应用缩放方案
        - 缩放比例 < 0.2：需要重新布局
        - IOU > 0.5：严重碰撞，必须重新设计
     c) 构造修改指令给image_input_processing_agent：
        "之前的layout存在碰撞问题，根据分析：[具体碰撞详情]。
         请重新调整layout，确保：[具体调整要求]。
         保存为：[原文件名]_[迭代次数].json"
     d) 验证新JSON文件生成
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

### 修改指令生成示例
```
基于碰撞检测结果，发现以下问题：
- desk_0和chair_0发生碰撞，IOU=0.15，重叠尺寸为[0.2, 0.1, 0.0]
- 建议调整：将chair_0位置从(1.5, 0.8, 0)调整到(1.5, 0.6, 0)，增加0.2m距离
- sofa_0和bookshelf_0过于接近，建议将sofa_0移动到房间中央位置

请重新生成layout，确保：
1. desk_0和chair_0之间至少保持0.3m距离
2. sofa_0重新定位到更合适的位置  
3. 保持整体布局的功能性和美观性
4. 保存为：student_study_room_design_1.json
```

### 错误处理和重试机制
- image_input_processing_agent调用失败：分析错误原因并重试
- occ_detection_agent调用失败：跳过碰撞检测，提醒用户手动检查
- plan.json文件不存在：表示无碰撞，正常结束流程
- JSON保存失败：指导agent采用分段保存策略
- 文件损坏或不完整：提示用户重新生成或从备份恢复
- 网络或工具调用超时：实施智能重试
- **碰撞检测迭代失败**：保存当前最优结果，向用户报告情况

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
1. **初始分析报告**：layout生成结果
2. **碰撞检测报告**：详细的碰撞情况和处理建议  
3. **优化过程记录**：每次迭代的改进情况
4. **最终结果**：无碰撞的layout和完整JSON文件路径

记住：你是流程的监督者和优化者，现在还具备了3D空间碰撞检测能力，不仅要确保技术流程的完整性，更要通过持续对话和自动优化帮助用户获得既美观又实用的室内设计方案。
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
    
    def _generate_modification_instruction(self, collision_details: Dict, original_file: str, iteration: int) -> str:
        """基于碰撞检测结果生成修改指令"""
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
            self.log(f"指令生成失败: {str(e)}", "warning")
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
                self.log(f"第{iteration}轮检测：发现碰撞，生成修改指令...", "info")
                
                # 生成修改指令
                modification_instruction = self._generate_modification_instruction(
                    collision_result['collision_details'], 
                    initial_json_file, 
                    iteration
                )
                
                # 调用image_input_processing_agent重新设计
                redesign_result = self.call_tool("imageinputprocessingagent", {
                    "query": modification_instruction
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
                new_file_path = self._extract_file_path_from_response(str(redesign_result))
                if new_file_path and self._check_file_exists(new_file_path):
                    current_file = new_file_path
                    self.log(f"第{iteration}轮优化：新文件生成 {new_file_path}", "info")
                else:
                    self.log(f"第{iteration}轮优化失败：无法找到新生成的JSON文件", "error")
                    return {
                        'success': False,
                        'final_file': current_file,
                        'total_iterations': iteration,
                        'optimization_log': optimization_log,
                        'final_status': '新JSON文件生成失败'
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