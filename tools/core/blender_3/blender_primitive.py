"""
BlenderPrimitive - 原始数据接口
提供Blender场景的原始数值数据，不做任何推断或解释
让LLM自己理解数值的含义
"""

from typing import List, Dict, Any, Optional
import json
import sys
import os

# 导入Blender连接
try:
    # 添加blender-mcp到路径
    blender_mcp_src = os.path.join(os.path.dirname(__file__), "blender-mcp", "src")
    if os.path.exists(blender_mcp_src):
        sys.path.insert(0, blender_mcp_src)
    
    from blender_mcp.server import get_blender_connection
except ImportError as e:
    # 只保留错误处理的print
    print(f"Warning: Could not import blender-mcp modules: {e}")
    get_blender_connection = None


class BlenderPrimitive:
    """
    Blender原始数据接口 - 专注于提供原始数据，让LLM自主理解
    
    设计原则：
    1. 提供原始数据，避免预处理和"翻译"
    2. 让LLM自己分析和理解数据含义
    3. 避免硬编码的语义判断
    4. 保持接口简洁，功能专一
    """
    
    def __init__(self):
        self.blender = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """初始化Blender连接"""
        if get_blender_connection is not None:
            try:
                self.blender = get_blender_connection()
            except Exception as e:
                # 只保留错误处理的print
                print(f"警告：无法连接到Blender MCP服务器: {e}")
                self.blender = None
    
    def send_command(self, tool_name, arguments=None):
        """向Blender发送命令"""
        if self.blender is None:
            return "✗ Blender连接不可用"
        
        try:
            if arguments is None:
                arguments = {}
            result = self.blender.send_command(tool_name, arguments)
            return result if isinstance(result, str) else str(result)
        except Exception as e:
            return f"✗ 执行命令失败: {e}"
    
    # ========== 原始数据获取接口 ==========
    
    def get_raw_scene_data(self):
        """获取场景中所有对象的原始数据"""
        script = """
import bpy
import json

scene_data = {
    'total_count': len(bpy.data.objects),
    'objects': [],
    'boundaries': {'min': [0, 0, 0], 'max': [0, 0, 0]}
}

# 收集所有对象信息
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj_data = {
            'name': obj.name,
            'location': [round(obj.location.x, 3), round(obj.location.y, 3), round(obj.location.z, 3)],
            'dimensions': [round(obj.dimensions.x, 3), round(obj.dimensions.y, 3), round(obj.dimensions.z, 3)],
            'rotation': [round(obj.rotation_euler.x, 3), round(obj.rotation_euler.y, 3), round(obj.rotation_euler.z, 3)],
            'type': obj.type
        }
        
        # 获取元数据
        if 'guide_metadata' in obj:
            try:
                obj_data['metadata'] = json.loads(obj['guide_metadata'])
            except:
                obj_data['metadata'] = obj['guide_metadata']
        else:
            obj_data['metadata'] = None
            
        scene_data['objects'].append(obj_data)

# 计算场景边界
if scene_data['objects']:
    all_locations = [obj['location'] for obj in scene_data['objects']]
    min_coords = [min(loc[i] for loc in all_locations) for i in range(3)]
    max_coords = [max(loc[i] for loc in all_locations) for i in range(3)]
    scene_data['boundaries'] = {'min': min_coords, 'max': max_coords}

print(json.dumps(scene_data, ensure_ascii=False))
"""
        
        result = self.send_command("execute_code", {"code": script})
        
        # 直接返回原始数据，不添加格式化输出
        if result.startswith("✗"):
            return result
        
        try:
            import json
            scene_data = json.loads(result.split('\n')[-2])
            return scene_data
        except:
            return result
    
    def get_raw_object_data(self, name):
        """获取单个对象的原始数据"""
        script = f"""
import bpy
import json

obj = bpy.data.objects.get("{name}")
if not obj:
    print("✗ 未找到对象")
elif obj.type != 'MESH':
    print("✗ 不是网格对象")
else:
    obj_data = {{
        'name': obj.name,
        'location': [round(obj.location.x, 3), round(obj.location.y, 3), round(obj.location.z, 3)],
        'dimensions': [round(obj.dimensions.x, 3), round(obj.dimensions.y, 3), round(obj.dimensions.z, 3)],
        'rotation': [round(obj.rotation_euler.x, 3), round(obj.rotation_euler.y, 3), round(obj.rotation_euler.z, 3)],
        'type': obj.type
    }}
    
    # 获取元数据
    if 'guide_metadata' in obj:
        try:
            obj_data['metadata'] = json.loads(obj['guide_metadata'])
        except:
            obj_data['metadata'] = obj['guide_metadata']
    else:
        obj_data['metadata'] = None
    
    print(json.dumps(obj_data, ensure_ascii=False))
"""
        
        result = self.send_command("execute_code", {"code": script})
        
        if "✗" in result:
            return result
            
        try:
            import json
            lines = result.strip().split('\n')
            for line in lines:
                if line.startswith('{'):
                    return json.loads(line)
        except:
            pass
        
        return result
    
    def get_raw_guides_data(self):
        """获取所有引导线的原始数据"""
        script = """
import bpy
import json

guides = []
for obj in bpy.data.objects:
    if obj.name.startswith('LAYOUT_GUIDE_'):
        guide_data = {
            'name': obj.name,
            'location': [round(obj.location.x, 3), round(obj.location.y, 3), round(obj.location.z, 3)],
            'dimensions': [round(obj.dimensions.x, 3), round(obj.dimensions.y, 3), round(obj.dimensions.z, 3)],
            'rotation': [round(obj.rotation_euler.x, 3), round(obj.rotation_euler.y, 3), round(obj.rotation_euler.z, 3)],
            'type': obj.type
        }
        
        # 获取元数据
        if 'guide_metadata' in obj:
            try:
                guide_data['metadata'] = json.loads(obj['guide_metadata'])
            except:
                guide_data['metadata'] = obj['guide_metadata']
        else:
            guide_data['metadata'] = None
            
        guides.append(guide_data)

guides_data = {
    'total_count': len(guides),
    'guides': guides
}

print(json.dumps(guides_data, ensure_ascii=False))
"""
        
        result = self.send_command("execute_code", {"code": script})
        
        if result.startswith("✗"):
            return result
        
        try:
            import json
            return json.loads(result.strip().split('\n')[-1])
        except:
            return result
    
    def get_scene_boundaries(self):
        """获取场景边界的原始坐标"""
        script = """
import bpy

if not bpy.data.objects:
    print("场景为空")
else:
    # 计算边界
    locations = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            locations.append([obj.location.x, obj.location.y, obj.location.z])
    
    if locations:
        min_x = min(loc[0] for loc in locations)
        max_x = max(loc[0] for loc in locations)
        min_y = min(loc[1] for loc in locations)
        max_y = max(loc[1] for loc in locations)
        min_z = min(loc[2] for loc in locations)
        max_z = max(loc[2] for loc in locations)
        
        boundaries = {
            'min': [round(min_x, 3), round(min_y, 3), round(min_z, 3)],
            'max': [round(max_x, 3), round(max_y, 3), round(max_z, 3)],
            'size': [round(max_x - min_x, 3), round(max_y - min_y, 3), round(max_z - min_z, 3)],
            'center': [round((max_x + min_x)/2, 3), round((max_y + min_y)/2, 3), round((max_z + min_z)/2, 3)]
        }
        
        import json
        print(json.dumps(boundaries))
    else:
        print("无网格对象")
"""
        
        result = self.send_command("execute_code", {"code": script})
        
        if "场景为空" in result or "无网格对象" in result:
            return result
        
        try:
            import json
            return json.loads(result.strip().split('\n')[-1])
        except:
            return result
    
    # ========== 基本操作接口（保持简洁） ==========
    
    def create_guide_cube(self, name, location, dimensions, metadata=None):
        """创建线框式引导线"""
        import json
        
        metadata_json = ""
        if metadata:
            metadata_json = json.dumps(metadata, ensure_ascii=False)
        
        # 构建代码片段 - 创建线框引导线
        code_parts = [
            "import bpy",
            "import bmesh",
            "import json",
            "",
            "# 创建新的网格",
            f'mesh = bpy.data.meshes.new("{name}_mesh")',
            f'obj = bpy.data.objects.new("{name}", mesh)',
            "bpy.context.collection.objects.link(obj)",
            "",
            "# 手动创建线框立方体的顶点和边",
            "bm = bmesh.new()",
            "",
            "# 创建立方体的8个顶点",
            "v0 = bm.verts.new((-0.5, -0.5, -0.5))",
            "v1 = bm.verts.new((0.5, -0.5, -0.5))",
            "v2 = bm.verts.new((0.5, 0.5, -0.5))",
            "v3 = bm.verts.new((-0.5, 0.5, -0.5))",
            "v4 = bm.verts.new((-0.5, -0.5, 0.5))",
            "v5 = bm.verts.new((0.5, -0.5, 0.5))",
            "v6 = bm.verts.new((0.5, 0.5, 0.5))",
            "v7 = bm.verts.new((-0.5, 0.5, 0.5))",
            "",
            "# 创建立方体的12条边",
            "# 底面边",
            "bm.edges.new([v0, v1])",
            "bm.edges.new([v1, v2])",
            "bm.edges.new([v2, v3])",
            "bm.edges.new([v3, v0])",
            "# 顶面边",
            "bm.edges.new([v4, v5])",
            "bm.edges.new([v5, v6])",
            "bm.edges.new([v6, v7])",
            "bm.edges.new([v7, v4])",
            "# 垂直边",
            "bm.edges.new([v0, v4])",
            "bm.edges.new([v1, v5])",
            "bm.edges.new([v2, v6])",
            "bm.edges.new([v3, v7])",
            "",
            "# 确保bmesh有效",
            "bm.verts.ensure_lookup_table()",
            "bm.edges.ensure_lookup_table()",
            "",
            "# 将bmesh数据写入网格",
            "bm.to_mesh(mesh)",
            "bm.free()",
            "",
            "# 更新网格",
            "mesh.update()",
            "",
            "# 设置位置",
            f"obj.location = ({location[0]}, {location[1]}, {location[2]})",
            "",
            "# 先缩放到目标尺寸",
            f"obj.scale = ({dimensions[0]}, {dimensions[1]}, {dimensions[2]})",
            "",
            "# 应用变换",
            "bpy.context.view_layer.objects.active = obj",
            "bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)",
            "",
            "# 创建线框材质",
            f'mat = bpy.data.materials.new(name="{name}_wireframe_material")',
            "mat.use_nodes = True",
            "nodes = mat.node_tree.nodes",
            "links = mat.node_tree.links",
            "",
            "# 清除默认节点",
            "nodes.clear()",
            "",
            "# 添加Wireframe节点",
            'wireframe_node = nodes.new(type="ShaderNodeWireframe")',
            "wireframe_node.location = (0, 0)",
            "wireframe_node.inputs[0].default_value = 0.02  # 线条粗细",
            "",
            "# 添加Emission节点",
            'emission_node = nodes.new(type="ShaderNodeEmission")',
            "emission_node.location = (200, 0)",
            "emission_node.inputs[0].default_value = (0.2, 0.8, 0.2, 1.0)  # 绿色",
            "emission_node.inputs[1].default_value = 1.0  # 强度",
            "",
            "# 添加Transparent节点",
            'transparent_node = nodes.new(type="ShaderNodeBsdfTransparent")',
            "transparent_node.location = (200, -150)",
            "",
            "# 添加Mix节点",
            'mix_node = nodes.new(type="ShaderNodeMixShader")',
            "mix_node.location = (400, 0)",
            "",
            "# 添加Material Output节点",
            'output_node = nodes.new(type="ShaderNodeOutputMaterial")',
            "output_node.location = (600, 0)",
            "",
            "# 连接节点",
            "links.new(wireframe_node.outputs[0], mix_node.inputs[0])  # Wireframe -> Mix Factor",
            "links.new(emission_node.outputs[0], mix_node.inputs[1])   # Emission -> Mix Shader 1",
            "links.new(transparent_node.outputs[0], mix_node.inputs[2]) # Transparent -> Mix Shader 2",
            "links.new(mix_node.outputs[0], output_node.inputs[0])     # Mix -> Material Output",
            "",
            "# 应用材质",
            "obj.data.materials.append(mat)",
            "",
            "# 设置显示模式为线框",
            "obj.display_type = 'WIRE'",
            "obj.show_wire = True"
        ]
        
        # 只在有元数据时添加元数据设置
        if metadata_json:
            code_parts.extend([
                "",
                "# 设置元数据",
                f'obj["guide_metadata"] = """{metadata_json}"""'
            ])
        
        code = "\n".join(code_parts)
        
        return self.send_command("execute_code", {"code": code})
    
    def move_object(self, name, new_location):
        """移动对象到新位置"""
        script = f"""
import bpy

obj = bpy.data.objects.get("{name}")
if not obj:
    print("✗ 未找到对象")
else:
    old_location = [obj.location.x, obj.location.y, obj.location.z]
    obj.location = ({new_location[0]}, {new_location[1]}, {new_location[2]})
    
    import json
    result = {{
        'object': obj.name,
        'old_location': old_location,
        'new_location': [{new_location[0]}, {new_location[1]}, {new_location[2]}]
    }}
    print(json.dumps(result))
"""
        
        return self.send_command("execute_code", {"code": script})
    
    def set_guide_metadata(self, object_name, metadata):
        """设置引导线对象的元数据"""
        import json
        metadata_json = json.dumps(metadata, ensure_ascii=False)
        
        script = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if not obj:
    print("✗ 未找到对象")
else:
    obj['guide_metadata'] = '''{metadata_json}'''
    print("✓ 元数据已更新")
"""
        
        return self.send_command("execute_code", {"code": script})
    
    def find_objects_near_location(self, center, radius=2.0):
        """查找指定位置附近的对象"""
        script = f"""
import bpy
import json
import math

center = [{center[0]}, {center[1]}, {center[2]}]
radius = {radius}

nearby_objects = []
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        distance = math.sqrt(
            (obj.location.x - center[0])**2 + 
            (obj.location.y - center[1])**2 + 
            (obj.location.z - center[2])**2
        )
        
        if distance <= radius:
            obj_data = {{
                'name': obj.name,
                'location': [round(obj.location.x, 3), round(obj.location.y, 3), round(obj.location.z, 3)],
                'dimensions': [round(obj.dimensions.x, 3), round(obj.dimensions.y, 3), round(obj.dimensions.z, 3)],
                'rotation': [round(obj.rotation_euler.x, 3), round(obj.rotation_euler.y, 3), round(obj.rotation_euler.z, 3)],
                'distance': round(distance, 3)
            }}
            
            # 获取元数据
            if 'guide_metadata' in obj:
                try:
                    obj_data['metadata'] = json.loads(obj['guide_metadata'])
                except:
                    obj_data['metadata'] = obj['guide_metadata']
            else:
                obj_data['metadata'] = None
                
            nearby_objects.append(obj_data)

result = {{
    'center': center,
    'radius': radius,
    'count': len(nearby_objects),
    'objects': nearby_objects
}}

print(json.dumps(result, ensure_ascii=False))
"""
        
        result = self.send_command("execute_code", {"code": script})
        
        try:
            import json
            return json.loads(result.strip().split('\n')[-1])
        except:
            return result


blender_primitive = BlenderPrimitive() 