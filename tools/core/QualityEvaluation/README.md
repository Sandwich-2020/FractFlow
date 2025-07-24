# 3D模型与场景质量评估子系统（FractFlow Quality Evaluation）

## 项目简介

本子系统为 FractFlow 分形智能架构中的 3D 场景与模型质量自动化评估模块，支持多角度渲染、物体尺寸评估、物体支撑关系检测、场景全局评估与结构化反馈。系统高度结构化，便于上层Agent自动调用，广泛适用于3D内容生成、室内设计、AI辅助建模等场景。

## 系统架构与主要模块

- **feedback_agent.py**：顶层工作流代理，自动协调渲染、尺寸评估、支撑关系评估、场景评估，输出结构化YAML报告。
- **Size_evaluation_agent.py / Size_evaluation_mcp.py**：物体尺寸评估，分析渲染图像中各类物体尺寸是否符合标准。
- **Support_relation_agent.py / Support_relation_mcp.py**：物体支撑关系与物理合理性检测，解析3D场景JSON，检测悬空、重叠、与门窗/墙体的物理关系。
- **Scene_vqa_agent.py / Scene_vqa_mcp.py**：场景视觉问答与评估，聚焦对象计数、属性、空间关系、架构关系与文本描述一致性。

## 项目内容查看

- #团队项目
- github地址：https://github.com/Sandwich-2020/FractFlow/tree/main
- 个人内容：tools/core/Qualityevaluation文件中场景评估工具

## 个人工作内容描述

### 1. 增加物体关系检测agent(Support_relation_agent)
功能：根据房间布局Json生成所有物体、门、窗、墙的3D bbox即六个面位置信息；推断物体之间的支撑关系（优先级：地面>墙>其他物体>门>窗）；检测物理关系错误：检测悬空、弱支撑（2D重叠比例低于50%）、物体与门窗的重合、物体与门窗距离过近（影响采光，交通）的情形。
理由：LLM对物体空间理解过于依赖文本描述词[1]，在给只给予图片或文本中空间关系描述不足时，需要检测物体空间关系，模块主要包含论文[2]中的物体支撑关系（碰撞关系已有occ模块），额外添加物体门窗关系的检测，避免遮挡。
不足：在场景内物体较多的情况下，判断初始支撑关系（最近支撑物体）的处理时间过长，不影响最终物理错误关系判断，但应考虑优化initialize_support_relation mcp tool 模块

### 2. 修改更新场景质量检测agent(Scene_vqa_agent)
根据论文[3]中的文本场景一致性包含的维度对场景进行检测，对象计数（CNT），对象属性（ATR），对象-对象关系（OOR），对象架构关系（QAR），输出结果主要包含message（结论）、error（不符点）、fidelity（一致性分数），便于主反馈代理自动解析，将修改的评估工具整合到feedback中
理由：使其评估结果更符合整个项目通过文本生成3D场景的评估需求
不足：尚未实现自动接入其他agent的生成结果

### 3. 其他过程工作
物体大小评估agent初稿（保留）——基于SG-FRONT semantic scene graph先验信息
物体位置评估agent（删除）
feedback agent(整体调用其他三个工具)初稿，初始完成量见提交附件文件夹（others/feedback_agent.py）

## 其他附件
运行日志见附件others
演示文件（个人部分）见附件pre_files

## 参考文献/代码
【1】A. Majumdar et al., "OpenEQA: Embodied Question Answering in the Era of Foundation Models," 2024 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), Seattle, WA, USA, 2024, pp. 16488-16498, doi: 10.1109/CVPR52733.2024.01560.
【2】Chen, Yixin & Siyuan, Huang & Yuan, Tao & Zhu, Yixin & Qi, Siyuan & Zhu, Song. (2019). Holistic++ Scene Understanding: Single-View 3D Holistic Scene Parsing and Human Pose Estimation With Human-Object Interaction and Physical Commonsense. 8647-8656. 10.1109/ICCV.2019.00874. 
【3】Chen, Zuyao & Wu, Jinlin & Lei, Zhen & Chen, Chang. (2024). What Makes a Scene ? Scene Graph-based Evaluation and Feedback for Controllable Generation. 10.48550/arXiv.2411.15435. 

## 输入输出示例

### 1. Size_evaluation_agent.py
#### 输入示例：
```evaluate the sence in the path'……'
Image: ./renders/render_0000.png 请评估所有物体尺寸是否合规
```

#### 输出YAML片段：

- object_name: radiator
  predicted_dimensions:
    length: 1.2
    width: 0.1
    height: 0.6
  standard_dimensions:
    length: {min: 0.0, max: 0.0}
    width: {min: 0.0, max: 0.0}
    height: {min: 0.0, max: 0.0}
  evaluation: 不合理
  notes: 暖气片没有标准尺寸定义，无法判断合规性；建议依据房间热负荷需求调整。

Conclusion: 吊灯(pendant_lamp)的尺寸符合标准；其余物体如楼梯(staircase)、壁炉(fireplace)、沙发椅(armchair)、茶几(coffee_table)、地毯(carpet)、立式台灯(floor_lamp)、画作(painting)、大理石球(marble_ball)、书架(bookshelf)、底座(pedestal)和暖气片(radiator)无法完全匹配预设的标准尺寸范围。沙发椅的宽度不足，茶几尺寸超标，书架的长宽高均不达标，其他物体无明确标准。

### 2. Support_relation_agent.py
#### 输入示例：
```analyze the provided JSON file for physical relations.
```
#### 输出Python字典片段：
support info
    "summary": {
        "total_errors": 7,
        "traffic_blocked": 4,
        "overlap_door": 1,
        "overlap_window": 2,
        "message": "共检测到7处物理关系异常。"
    },
    "success": True

Key Findings:
1. **Support Relationships**:
   - All major furniture items (sofa, coffee table, desk) are properly supported by the flooring
   - Smaller objects are correctly placed on their supporting surfaces (laptop on desk, bowl/fruit on coffee table)
   - The flooring itself is properly grounded

2. **Physical Errors**:
   - **Traffic Flow Issues**: Multiple objects are blocking the door area (sofa, flooring, rug, bookshelf)
   - **Overlap Problems**:
     - The flooring overlaps with both the door and a window
     - The plant overlaps with a window
   - **Critical Issues**:
     - The bookshelf is extremely close to the door (0.14m)
     - The flooring completely overlaps with the door (distance 0.00m)

3. **Recommendations**:
   - Reposition the bookshelf further from the door (minimum recommended clearance: 0.5m)
   - Adjust the flooring boundaries to avoid door/window overlaps
   - Move the plant away from the window area
   - Consider rearranging the sofa to improve door access
   - Verify the rug placement to ensure it doesn't obstruct traffic flow

The scene demonstrates good basic support relationships but requires spatial adjustments to improve functionality and accessibility, particularly around the door and window areas.

### 3. Scene_vqa_agent.py
#### 输入示例：
```
You: evaluate the fidelity of image and text description, 渲染图像路径': 'd:\Term3\CVproject\FractFlow2\assets\indoorscene3.png', '场景描述': '这是一个现代化的客厅，展现出优雅和舒适的氛围。灰色沙发占据了显眼的位置，配有柔和色调的装饰靠垫，营造出放松的感觉。旁边是一张浅色的扶手椅，提供额外的座位，增强了整体美感。中央的咖啡桌采用木材与玻璃的结合，设计现代，几何造型独特，成为房间的亮点。角落里，一盏高大的落地灯，明亮的黄色灯罩为空间增添了温暖的光辉和活力。小巧的边桌上摆放着一个花瓶，插着新鲜的花朵，为室内带来自然气息，增添了一丝清新。墙面装饰简约，柔和的窗帘轻柔垂落，滤过自然光，营造出宁静的氛围。整体来看，这个客厅融合了柔和的色彩、自然光与时尚家具，创造出一个理想的放松和社交空间'
```
#### 输出Python字典片段：
Agent: scene_evaluation = {
    'answer': {
        '对象计数': {'message': '场景中对象数量与文本描述基本匹配，满足规格的百分比为90%。', 'error': None, 'fidelity': 0.9},
        '对象属性': {'message': '对象视觉属性（颜色/材质/尺寸）与文本描述的匹配度较高，符合属性的对象占比为85%。', 'error': None, 'fidelity': 0.85},
        '对象-对象关系': {'message': '预定义空间关系（内部/紧挨/面对等）的符合性较好，满足文本空间关系描述的占比为88%。', 'error': None, 'fidelity': 0.88},
        '对象架构关系': {'message': '对象与建筑结构（墙/地板/天花板）的空间关系合理，符合架构约束的布局占比为92%。', 'error': None, 'fidelity': 0.92},
        '文本场景描述一致性': {'message': '场景图像与文本描述内容（空间功能、结构分布、家具概况、风格亮点等）一致性较高，每项描述的匹配度超过90%。', 'error': None, 'fidelity': 0.9}
    },
    'Conclusion': '整体来看，图像和文本描述之间的匹配度非常高，所有方面的评估结果均达到或超过预期标准，证明图像场景忠实反映了文本描述的内容。',
    'fidelity': 0.89,
    'success': True
}

## 端到端评估流程（文字说明）

1. 用户输入3D模型文件路径或场景JSON描述
2. 系统自动检测并渲染3D模型，生成多角度高质量图片
3. 调用尺寸评估Agent，对所有物体尺寸进行标准合规性分析
4. 调用支撑关系评估Agent，检测物体与地面、墙体、门窗等的物理关系
5. 调用场景评估Agent，分析整体空间布局、对象关系与文本描述一致性
6. 汇总所有评估结果，输出结构化YAML反馈报告，便于上层Agent或用户查阅

## 目录结构示例

```
tools/core/QualityEvaluation/
├── feedback_agent.py
├── Size_evaluation_agent.py
├── Size_evaluation_mcp.py
├── Support_relation_agent.py
├── Support_relation_mcp.py
├── Scene_vqa_agent.py
├── Scene_vqa_mcp.py
├── README.md
└── ...
```

---
如有问题请查阅各Agent源码注释或联系维护者。 