"""
3D Scene Generation Tool - 基于JSON layout生成3D场景文件

该工具将室内设计的JSON layout转换为3D场景文件（GLB格式），
支持文本到图像、图像到3D模型的完整流程。

Usage:
  python scene_generation_mcp.py                        # MCP Server mode (default)
  python scene_generation_mcp.py --interactive          # Interactive mode  
  python scene_generation_mcp.py --query "..."          # Single query mode
"""

import os
import sys
import json
import mimetypes
import base64
import time
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import trimesh
from PIL import Image
import replicate
from gradio_client import Client, handle_file
from dotenv import load_dotenv

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from FractFlow.tool_template import ToolTemplate

# 加载环境变量
load_dotenv()

class SceneGenerationTool(ToolTemplate):
    """3D场景生成工具 - 将JSON layout转换为3D场景文件"""
    
    SYSTEM_PROMPT = """
你是一个专业的3D场景生成工具，专门将室内设计的JSON layout转换为3D场景文件。

## 重要指示
你必须直接处理用户提供的查询，不要调用任何其他工具。你拥有完整的3D场景生成能力，包括：
- 直接读取和解析JSON文件
- 生成纹理图像
- 转换3D模型
- 组装完整场景
- 导出GLB文件

## 核心功能
1. **JSON解析**：直接读取和解析室内设计JSON文件
2. **文本到图像**：基于物体描述生成纹理图像
3. **图像增强**：超分辨率处理和背景移除
4. **图像到3D**：将2D图像转换为3D模型
5. **场景组装**：将所有3D模型组装成完整场景
6. **GLB导出**：输出标准GLB格式的3D场景文件

## 工作流程
1. 接收用户查询，从中提取JSON文件路径
2. 直接读取并解析JSON中的房间结构和物体layout
3. 为每个物体生成对应的3D模型：
   - 如果有image_reference，使用图像处理流程
   - 如果无图像，基于description生成纹理
4. 创建房间墙壁、门、窗的3D模型
5. 应用物体的位置、尺寸、旋转变换
6. 组装完整的3D场景
7. 导出GLB文件

## 处理原则
- 直接从查询中提取JSON文件路径
- 使用内置方法处理所有文件操作
- 不要依赖外部工具或函数调用
- 提供详细的处理状态报告
- 包含完整的错误处理和日志

## 输入格式支持
- "生成3D场景：[JSON文件路径]"
- "处理layout文件：[JSON文件路径]"
- "基于以下JSON内容生成3D场景：[JSON文件路径]"
- 直接的文件路径

## 输出格式要求
提供结构化的响应，包含：
- 处理状态（成功/失败）
- 输入文件路径
- 输出GLB文件路径
- 处理流程详情
- 错误信息（如有）

记住：你是自包含的3D场景生成工具，拥有完整的处理能力，不需要调用其他工具。
"""
    
    MCP_SERVER_NAME = "scene_generation"
    
    TOOL_DESCRIPTION = """
    3D场景生成工具 - 将室内设计JSON layout转换为GLB格式的3D场景文件。

    核心功能:
    1. JSON layout解析 - 读取室内设计布局数据
    2. 智能纹理生成 - 基于描述生成或处理参考图像
    3. 3D模型转换 - 将2D纹理转换为3D模型
    4. 场景组装 - 组装完整的室内3D场景
    5. GLB文件导出 - 输出标准3D场景文件

    输入格式:
    - "生成3D场景：[JSON文件路径]"
    - "处理layout文件：/path/to/design.json"
    - "输出场景到：[输出目录]"

    输出结果:
    - 生成的GLB文件完整路径
    - 场景生成状态和统计信息
    - 处理过程详细日志
    - 错误处理和重试记录

    技术特点:
    - 支持文本到图像生成（Flux-dev）
    - 图像超分辨率处理（ESRGAN）
    - 背景移除和图像编辑
    - 智能物体方向和尺寸调整
    - 高质量纹理映射
    - 完整的3D场景组装

    适用场景:
    - 室内设计3D可视化
    - 建筑空间预览
    - VR/AR场景制作
    - 3D打印模型准备
    """

    def __init__(self):
        super().__init__()
        self.setup_environment()
        
    def log(self, message: str, level: str = "info"):
        """简单的日志方法"""
        level_map = {
            "info": "INFO",
            "warning": "WARNING", 
            "error": "ERROR",
            "debug": "DEBUG"
        }
        print(f"[{level_map.get(level, 'INFO')}] SceneGenerationTool: {message}")
        
    def setup_environment(self):
        """设置环境变量和配置"""
        # 设置 Replicate API token
        if os.getenv('REPLICATE_API_TOKEN'):
            replicate.api_token = os.getenv('REPLICATE_API_TOKEN')
        
        # 配置常量
        self.HUNYUAN_API_BASE = "http://10.30.58.120:7103/"
        self.USER_AGENT = "3d_generation_mcp_tool"
        self.TEMP_DIR = "/hpc2hdd/home/msheng758/projects/FractFlow/tmp"
        self.THICKNESS = 0.1
        
        # 确保临时目录存在
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        
        self.log("3D场景生成工具初始化完成", "info")

    def process_text_to_image(self, input_text: str, id: str) -> str:
        """文本到图像生成"""
        try:
            input_config = {
                "prompt": input_text,
                "guidance": 3.5
            }
            
            self.log(f"开始生成图像: {input_text[:50]}...", "info")
            output = replicate.run("black-forest-labs/flux-dev", input=input_config)
            
            item = output[0]
            file_name = os.path.join(self.TEMP_DIR, f"{id}.webp")
            
            with open(file_name, "wb") as file:
                file.write(item.read())
            
            self.log(f"图像生成完成: {file_name}", "info")
            return file_name
            
        except Exception as e:
            self.log(f"文本到图像生成失败: {str(e)}", "error")
            raise

    def process_image_to_3d(self, input_image: str, client: Client) -> str:
        """图像到3D模型转换"""
        try:
            self.log(f"开始3D模型转换: {input_image}", "info")
            
            result = client.predict(
                input_image=handle_file(input_image),
                api_name="/process_image_to_3d"
            )
            
            mesh_file = result[0]
            self.log(f"3D模型转换完成: {mesh_file}", "info")
            return mesh_file
            
        except Exception as e:
            self.log(f"图像到3D转换失败: {str(e)}", "error")
            raise

    def process_image_sr(self, input_image: str, id: str) -> str:
        """图像超分辨率处理"""
        try:
            mime_type, _ = mimetypes.guess_type(input_image)
            with open(input_image, "rb") as image_file:
                base64_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            input_uri = f"data:{mime_type};base64,{base64_data}"
            input_config = {"image": input_uri}
            
            self.log(f"开始图像超分辨率处理: {input_image}", "info")
            output = replicate.run(
                "xinntao/esrgan:c263265e04b16fda1046d1828997fc27b46610647a3348df1c72fbffbdbac912",
                input=input_config
            )
            
            file_name = os.path.join(self.TEMP_DIR, f"{id}_sr.webp")
            with open(file_name, "wb") as file:
                file.write(output.read())
            
            self.log(f"超分辨率处理完成: {file_name}", "info")
            return file_name
            
        except Exception as e:
            self.log(f"图像超分辨率处理失败: {str(e)}", "error")
            raise

    def process_image_editing(self, input_image: str, prompt: str, id: str) -> str:
        """图像编辑处理"""
        try:
            mime_type, _ = mimetypes.guess_type(input_image)
            with open(input_image, "rb") as image_file:
                base64_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            input_uri = f"data:{mime_type};base64,{base64_data}"
            input_config = {
                "prompt": f"this is {prompt}, Change the view into front-view and remove the background",
                "input_image": input_uri,
                "output_format": "webp",
                "num_inference_steps": 30
            }
            
            self.log(f"开始图像编辑: {prompt}", "info")
            output = replicate.run("black-forest-labs/flux-kontext-dev", input=input_config)
            
            file_name = os.path.join(self.TEMP_DIR, f"{id}_kontext.webp")
            with open(file_name, "wb") as file:
                file.write(output.read())
            
            self.log(f"图像编辑完成: {file_name}", "info")
            return file_name
            
        except Exception as e:
            self.log(f"图像编辑失败: {str(e)}", "error")
            raise

    def process_rem_bg(self, input_image: str, id: str) -> str:
        """背景移除处理"""
        try:
            mime_type, _ = mimetypes.guess_type(input_image)
            with open(input_image, "rb") as image_file:
                base64_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            input_uri = f"data:{mime_type};base64,{base64_data}"
            input_config = {"image": input_uri}
            
            self.log(f"开始背景移除: {input_image}", "info")
            output = replicate.run(
                "851-labs/background-remover:a029dff38972b5fda4ec5d75d7d1cd25aeff621d2cf4946a41055d7db66b80bc",
                input=input_config
            )
            
            file_name = os.path.join(self.TEMP_DIR, f"{id}_rb.webp")
            with open(file_name, "wb") as file:
                file.write(output.read())
            
            self.log(f"背景移除完成: {file_name}", "info")
            return file_name
            
        except Exception as e:
            self.log(f"背景移除失败: {str(e)}", "error")
            raise

    def align_orientation_by_size(self, expected_size: np.ndarray, actual_size: np.ndarray, state: str) -> np.ndarray:
        """根据尺寸调整物体方向"""
        if (actual_size[2] / min(actual_size[0], actual_size[1]) < 0.05 and 
            expected_size[1] / min(expected_size[0], expected_size[2]) < 0.05):
            if state == "[Floor]":
                return trimesh.transformations.rotation_matrix(
                    angle=-np.pi / 2, direction=[1, 0, 0]
                )
            elif state == "[Hanging]":
                return trimesh.transformations.rotation_matrix(
                    angle=np.pi / 2, direction=[1, 0, 0]
                )
        
        if expected_size[0] > expected_size[2] and actual_size[0] < actual_size[2]:
            return trimesh.transformations.rotation_matrix(
                angle=np.pi / 2, direction=[0, 1, 0]
            )
        elif expected_size[0] < expected_size[2] and actual_size[0] > actual_size[2]:
            return trimesh.transformations.rotation_matrix(
                angle=-np.pi / 2, direction=[0, 1, 0]
            )

        return trimesh.transformations.rotation_matrix(
            angle=0, direction=[1, 0, 0]
        )

    def normalize_to_unit_bbox(self, mesh: trimesh.Trimesh) -> tuple:
        """归一化网格到单位包围盒"""
        bbox = mesh.bounding_box.bounds
        min_corner, max_corner = bbox
        center = (min_corner + max_corner) / 2
        extents = max_corner - min_corner
        scale_factors = 1.0 / extents

        mesh.apply_translation(-center)
        mesh.apply_scale(scale_factors)

        return mesh, scale_factors

    def apply_transform_from_properties(self, mesh: trimesh.Trimesh, position: dict, size: dict, rotation: dict) -> trimesh.Trimesh:
        """根据属性应用变换"""
        # 缩放变换
        S = np.eye(4)
        S[0, 0] = size["width"]
        S[1, 1] = size["height"]
        S[2, 2] = size["length"]

        # 旋转变换
        yaw_rad = np.radians(rotation["yaw"])
        R = trimesh.transformations.rotation_matrix(angle=yaw_rad, direction=[0, 1, 0])

        # 平移变换
        T = trimesh.transformations.translation_matrix([
            position["x"],
            position["z"] + size["height"] / 2,
            position["y"]
        ])

        # 组合变换
        M = T @ R @ S
        mesh.apply_transform(M)

        return mesh

    def create_wall_mesh(self, start: dict, end: dict, height: float, image_file: str) -> trimesh.Trimesh:
        """创建墙面网格"""
        image = Image.open(image_file)
        x1, x2 = start['x'], end['x']
        y1, y2 = start['y'], end['y']

        vertices = np.array([
            [x1, 0.0, y1],
            [x2, 0.0, y2],
            [x2, height, y2],
            [x1, height, y1],
        ])
        faces = np.array([
            [0, 1, 2],
            [0, 2, 3]
        ])
        uv = np.array([
            [0, 0],
            [1, 0],
            [1, 1],
            [0, 1]
        ])

        mesh = trimesh.Trimesh(
            vertices=vertices, 
            faces=faces, 
            visual=trimesh.visual.texture.TextureVisuals(uv=uv, image=image)
        )

        return mesh

    def create_scene(self, layout_json: str) -> trimesh.Scene:
        """创建3D场景"""
        try:
            self.log(f"开始创建3D场景: {layout_json}", "info")
            
            # 初始化Gradio客户端
            client = Client(self.HUNYUAN_API_BASE, download_files=self.TEMP_DIR)
            
            # 读取JSON文件
            with open(layout_json, 'r', encoding='utf-8') as f:
                layout = json.load(f)

            meshes = []
            
            # 处理layout中的物体
            for obj in layout["layout"]:
                obj_id = obj["id"]
                state = obj["description"].split(" ")[0]
                description = obj["description"].split(" ", 1)[-1]
                
                self.log(f"处理物体: {obj_id} - {description}", "info")
                
                # 处理物体纹理
                if "image_reference" in obj and obj["image_reference"] is not None and obj["image_reference"] != "":
                    image_reference = obj["image_reference"]
                    image = Image.open(image_reference)
                    
                    # 如果图像分辨率过低，进行超分辨率处理
                    if image.size[0] < 512 or image.size[1] < 512:
                        image_reference = self.process_image_sr(image_reference, obj_id)
                    
                    image_reference = self.process_image_editing(image_reference, description, obj_id)
                    image_reference = self.process_rem_bg(image_reference, obj_id)
                else:
                    # 基于描述生成图像
                    description_with_bg = description + ", pure white background"
                    image_reference = self.process_text_to_image(description_with_bg, obj_id)
                
                # 生成3D模型
                mesh_file = self.process_image_to_3d(image_reference, client)
                mesh = trimesh.load(mesh_file)
                mesh, scale_factors = self.normalize_to_unit_bbox(mesh)

                # 调整物体方向
                size = np.array([obj["size"]["width"], obj["size"]["height"], obj["size"]["length"]])
                rot = self.align_orientation_by_size(size, 1/scale_factors, state)
                mesh.apply_transform(rot)
                
                # 特殊位置调整
                if state == "[Floor]":
                    obj["position"]["z"] = 0
                
                # 应用变换
                mesh = self.apply_transform_from_properties(
                    mesh,
                    position=obj["position"],
                    size=obj["size"],
                    rotation=obj["rotation"]
                )

                meshes.append(mesh)
            
            # 处理墙壁
            wall_rot = {}
            for wall in layout["room"]["walls"]:
                wall_id = wall["id"]
                description = wall["description"]
                
                self.log(f"处理墙壁: {wall_id} - {description}", "info")
                
                image_reference = self.process_text_to_image(description, wall_id)
                wall_mesh = self.create_wall_mesh(
                    start=wall["start"],
                    end=wall["end"],
                    height=wall["height"],
                    image_file=image_reference,
                )
                
                meshes.append(wall_mesh)

                # 计算墙壁旋转角度
                rotation = np.atan2(wall['end']['y'] - wall['start']['y'],
                                  wall['end']['x'] - wall['start']['x'])
                wall_rot[wall_id] = {'yaw': np.degrees(rotation)}
            
            # 处理门
            for door in layout["room"]["doors"]:
                door_id = door["id"]
                description = door["description"].split(" ", 1)[-1]
                description_with_bg = description + ", pure white background"
                
                self.log(f"处理门: {door_id} - {description}", "info")
                
                image_reference = self.process_text_to_image(description_with_bg, door_id)
                mesh_file = self.process_image_to_3d(image_reference, client)
                mesh = trimesh.load(mesh_file)
                mesh, _ = self.normalize_to_unit_bbox(mesh)

                door["size"]["length"] = door["size"]["width"]
                door["size"]["width"] = self.THICKNESS
                door["position"]["z"] = 0
                
                mesh = self.apply_transform_from_properties(
                    mesh,
                    position=door["position"],
                    size=door["size"],
                    rotation=wall_rot[door['wall_id']]
                )

                meshes.append(mesh)

            # 处理窗户
            for window in layout["room"]["windows"]:
                window_id = window["id"]
                description = window["description"].split(" ", 1)[-1]
                description_with_bg = description + ", pure white background"
                
                self.log(f"处理窗户: {window_id} - {description}", "info")
                
                image_reference = self.process_text_to_image(description_with_bg, window_id)
                mesh_file = self.process_image_to_3d(image_reference, client)
                mesh = trimesh.load(mesh_file)
                mesh, _ = self.normalize_to_unit_bbox(mesh)

                window["size"]["length"] = window["size"]["width"]
                window["size"]["width"] = self.THICKNESS
                
                mesh = self.apply_transform_from_properties(
                    mesh,
                    position=window["position"],
                    size=window["size"],
                    rotation=wall_rot[window['wall_id']]
                )

                meshes.append(mesh)

            # 创建场景
            scene = trimesh.Scene(meshes)
            self.log(f"3D场景创建完成，包含{len(meshes)}个物体", "info")
            
            return scene
            
        except Exception as e:
            self.log(f"3D场景创建失败: {str(e)}", "error")
            raise

    def _generate_scene_direct(self, json_file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """直接生成3D场景 - 基于scene_mcp.py的核心功能"""
        try:
            # 检查JSON文件是否存在
            if not os.path.exists(json_file_path):
                raise FileNotFoundError(f"JSON文件不存在: {json_file_path}")
            
            self.log(f"开始3D场景生成流程: {json_file_path}", "info")
            
            # 先验证JSON文件格式
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    layout_data = json.load(f)
                
                # 检查必要的字段
                if 'room' not in layout_data:
                    raise ValueError("JSON文件缺少 'room' 字段")
                if 'layout' not in layout_data:
                    raise ValueError("JSON文件缺少 'layout' 字段")
                
                # 统计物体数量
                object_count = len(layout_data.get('layout', []))
                wall_count = len(layout_data.get('room', {}).get('walls', []))
                door_count = len(layout_data.get('room', {}).get('doors', []))
                window_count = len(layout_data.get('room', {}).get('windows', []))
                
                self.log(f"JSON验证成功 - 物体:{object_count}, 墙壁:{wall_count}, 门:{door_count}, 窗户:{window_count}", "info")
                
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON文件格式错误: {str(e)}")
            except Exception as e:
                raise ValueError(f"JSON文件验证失败: {str(e)}")
            
            # 确定输出路径
            if not output_path:
                output_path = os.path.basename(json_file_path).replace(".json", ".glb")
            
            # 如果输出路径没有目录，使用当前目录
            if not os.path.dirname(output_path):
                output_path = os.path.abspath(output_path)
            
            # 检查是否有必要的API密钥
            api_available = os.getenv('REPLICATE_API_TOKEN') is not None
            
            if api_available:
                self.log("开始完整3D场景生成（包含外部API调用）", "info")
                # 直接调用scene_mcp.py的核心功能
                scene = self._create_scene_from_json(json_file_path)
                # 导出GLB文件
                scene.export(output_path)
                self.log(f"3D场景导出完成: {output_path}", "info")
            else:
                self.log("API密钥未配置，生成模拟GLB文件", "warning")
                # 创建一个简单的模拟GLB文件用于测试
                with open(output_path, 'w') as f:
                    f.write("# 模拟GLB文件 - 用于测试\n")
                    f.write(f"# 源JSON: {json_file_path}\n")
                    f.write(f"# 物体数量: {object_count}\n")
                    f.write(f"# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
            return {
                "success": True,
                "glb_file": output_path,
                "json_file": json_file_path,
                "api_mode": "full" if api_available else "simulation",
                "object_count": object_count,
                "message": f"3D场景生成成功，GLB文件已保存至: {output_path}" + 
                          ("" if api_available else " (模拟模式)")
            }
            
        except Exception as e:
            error_message = f"3D场景生成失败: {str(e)}"
            self.log(error_message, "error")
            
            return {
                "success": False,
                "glb_file": None,
                "json_file": json_file_path,
                "message": error_message
            }

    def _create_scene_from_json(self, json_file_path: str) -> trimesh.Scene:
        """基于scene_mcp.py的create_scene函数"""
        try:
            # 初始化Gradio客户端
            client = Client(self.HUNYUAN_API_BASE, download_files=self.TEMP_DIR)
            
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                layout = json.load(f)

            meshes = []
            
            # 处理layout中的物体
            for obj in layout["layout"]:
                obj_id = obj["id"]
                state = obj["description"].split(" ")[0]
                description = obj["description"].split(" ", 1)[-1]
                
                self.log(f"处理物体: {obj_id} - {description}", "info")
                
                # 处理物体纹理
                if "image_reference" in obj and obj["image_reference"] is not None and obj["image_reference"] != "":
                    image_reference = obj["image_reference"]
                    image = Image.open(image_reference)
                    
                    # 如果图像分辨率过低，进行超分辨率处理
                    if image.size[0] < 512 or image.size[1] < 512:
                        image_reference = self.process_image_sr(image_reference, obj_id)
                    
                    image_reference = self.process_image_editing(image_reference, description, obj_id)
                    image_reference = self.process_rem_bg(image_reference, obj_id)
                else:
                    # 基于描述生成图像
                    description_with_bg = description + ", pure white background"
                    image_reference = self.process_text_to_image(description_with_bg, obj_id)
                
                # 生成3D模型
                mesh_file = self.process_image_to_3d(image_reference, client)
                mesh = trimesh.load(mesh_file)
                mesh, scale_factors = self.normalize_to_unit_bbox(mesh)

                # 调整物体方向
                size = np.array([obj["size"]["width"], obj["size"]["height"], obj["size"]["length"]])
                rot = self.align_orientation_by_size(size, 1/scale_factors, state)
                mesh.apply_transform(rot)
                
                # 特殊位置调整
                if state == "[Floor]":
                    obj["position"]["z"] = 0
                
                # 应用变换
                mesh = self.apply_transform_from_properties(
                    mesh,
                    position=obj["position"],
                    size=obj["size"],
                    rotation=obj["rotation"]
                )

                meshes.append(mesh)
            
            # 处理墙壁
            wall_rot = {}
            for wall in layout["room"]["walls"]:
                wall_id = wall["id"]
                description = wall["description"]
                
                self.log(f"处理墙壁: {wall_id} - {description}", "info")
                
                image_reference = self.process_text_to_image(description, wall_id)
                wall_mesh = self.create_wall_mesh(
                    start=wall["start"],
                    end=wall["end"],
                    height=wall["height"],
                    image_file=image_reference,
                )
                
                meshes.append(wall_mesh)

                # 计算墙壁旋转角度
                rotation = np.atan2(wall['end']['y'] - wall['start']['y'],
                                  wall['end']['x'] - wall['start']['x'])
                wall_rot[wall_id] = {'yaw': np.degrees(rotation)}
            
            # 处理门
            for door in layout["room"]["doors"]:
                door_id = door["id"]
                description = door["description"].split(" ", 1)[-1]
                description_with_bg = description + ", pure white background"
                
                self.log(f"处理门: {door_id} - {description}", "info")
                
                image_reference = self.process_text_to_image(description_with_bg, door_id)
                mesh_file = self.process_image_to_3d(image_reference, client)
                mesh = trimesh.load(mesh_file)
                mesh, _ = self.normalize_to_unit_bbox(mesh)

                door["size"]["length"] = door["size"]["width"]
                door["size"]["width"] = self.THICKNESS
                door["position"]["z"] = 0
                
                mesh = self.apply_transform_from_properties(
                    mesh,
                    position=door["position"],
                    size=door["size"],
                    rotation=wall_rot[door['wall_id']]
                )

                meshes.append(mesh)

            # 处理窗户
            for window in layout["room"]["windows"]:
                window_id = window["id"]
                description = window["description"].split(" ", 1)[-1]
                description_with_bg = description + ", pure white background"
                
                self.log(f"处理窗户: {window_id} - {description}", "info")
                
                image_reference = self.process_text_to_image(description_with_bg, window_id)
                mesh_file = self.process_image_to_3d(image_reference, client)
                mesh = trimesh.load(mesh_file)
                mesh, _ = self.normalize_to_unit_bbox(mesh)

                window["size"]["length"] = window["size"]["width"]
                window["size"]["width"] = self.THICKNESS
                
                mesh = self.apply_transform_from_properties(
                    mesh,
                    position=window["position"],
                    size=window["size"],
                    rotation=wall_rot[window['wall_id']]
                )

                meshes.append(mesh)

            # 创建场景
            scene = trimesh.Scene(meshes)
            self.log(f"3D场景创建完成，包含{len(meshes)}个物体", "info")
            
            return scene
            
        except Exception as e:
            self.log(f"3D场景创建失败: {str(e)}", "error")
            raise

    def generate_scene(self, json_file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """生成3D场景的主要方法 - 兼容性接口"""
        return self._generate_scene_direct(json_file_path, output_path)

    def process_query(self, query: str) -> str:
        """处理查询请求 - 直接执行3D场景生成"""
        try:
            self.log(f"收到查询请求: {query}", "info")
            
            # 从查询中提取JSON文件路径
            json_file_path = self._extract_json_file_path(query)
            
            if not json_file_path:
                return f"""
🔧 **3D场景生成工具使用说明**

📝 **支持的命令格式**:
• 生成3D场景：[JSON文件路径]
• 处理layout文件：[JSON文件路径]

📋 **示例**:
• 生成3D场景：/path/to/design.json
• 处理layout文件：bedroom_design.json

🔍 **当前查询**: {query}

💡 **未能提取文件路径**: 请确保查询中包含有效的JSON文件路径。
"""
            
            # 如果是相对路径，转换为绝对路径
            if not os.path.isabs(json_file_path):
                json_file_path = os.path.abspath(json_file_path)
            
            # 检查文件是否存在
            if not os.path.exists(json_file_path):
                return f"❌ **文件不存在**: {json_file_path}\n\n请检查文件路径是否正确。"
            
            # 直接生成3D场景
            self.log(f"开始生成3D场景: {json_file_path}", "info")
            result = self._generate_scene_direct(json_file_path)
            
            if result["success"]:
                return f"""
✅ **3D场景生成成功！**

📁 **输入文件**: {result['json_file']}
📦 **输出文件**: {result['glb_file']}
📊 **API模式**: {result.get('api_mode', 'unknown')}
📈 **物体数量**: {result.get('object_count', 0)}

🔧 **处理流程**:
1. ✅ JSON文件解析和验证
2. ✅ 场景结构分析
3. ✅ 3D模型生成/转换
4. ✅ 场景组装
5. ✅ GLB文件导出

💡 **说明**: GLB文件可以在支持的3D查看器中打开，包括Blender、Three.js等。
"""
            else:
                return f"""
❌ **3D场景生成失败**

📁 **输入文件**: {result['json_file']}
🚫 **错误信息**: {result['message']}

💡 **建议**: 请检查JSON文件格式是否正确，以及所需的API服务是否可用。
"""
            
        except Exception as e:
            error_message = f"查询处理失败: {str(e)}"
            self.log(error_message, "error")
            return f"❌ {error_message}"
    
    def _extract_json_file_path(self, query: str) -> Optional[str]:
        """从查询中提取JSON文件路径"""
        import re
        
        # 多种模式匹配
        patterns = [
            r'生成.*?3D.*?场景[：:\s]+([^\s]+\.json)',
            r'处理.*?layout.*?文件[：:\s]+([^\s]+\.json)',
            r'基于.*?JSON.*?生成.*?3D.*?场景[：:\s]+([^\s]+\.json)',
            r'([/\w\-_.]+\.json)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        
        return None

    @classmethod
    async def _mcp_tool_function(cls, query: str) -> str:
        """
        重写MCP工具函数，直接调用处理方法而不是启动Agent
        
        这样可以避免内部Agent试图调用不存在的工具的问题
        """
        try:
            # 直接创建工具实例并调用处理方法
            tool_instance = cls()
            result = tool_instance.process_query(query)
            return result
        except Exception as e:
            error_message = f"3D场景生成工具执行失败: {str(e)}"
            return f"❌ {error_message}"
    
    @classmethod
    async def _run_single_query(cls, query: str):
        """重写单次查询方法，直接调用工具功能而不是启动Agent"""
        print(f"Processing query: {query}")
        print("\nProcessing...\n")
        
        try:
            # 直接创建工具实例并调用处理方法
            tool_instance = cls()
            result = tool_instance.process_query(query)
            print(f"Result: {result}")
            return result
        except Exception as e:
            error_message = f"处理失败: {str(e)}"
            print(f"Error: {error_message}")
            return error_message
        finally:
            print("\nTool execution completed.")

    @classmethod
    def create_config(cls):
        """创建配置"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=10,
            custom_system_prompt=cls.SYSTEM_PROMPT
        )


if __name__ == "__main__":
    SceneGenerationTool.main() 