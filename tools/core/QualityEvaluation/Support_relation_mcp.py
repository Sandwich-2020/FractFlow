import os
import json
import numpy as np
import httpx
from typing import List, Dict
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# 加载环境变量
load_dotenv()

# 初始化 FastMCP 服务器
mcp = FastMCP("Support_relation_detection")


def normalize_path(path: str) -> str:
    """
    Normalize a file path by expanding ~ to user's home directory
    and resolving relative paths.
    
    Args:
        path: The input path to normalize
        
    Returns:
        The normalized absolute path
    """
    # Expand ~ to user's home directory
    expanded_path = os.path.expanduser(path)
    
    # Convert to absolute path if relative
    if not os.path.isabs(expanded_path):
        expanded_path = os.path.abspath(expanded_path)
        
    return expanded_path

async def download_file(url: str, save_path: str) -> None:
    """
    Download a file from URL to local path.
    
    Args:
        url: The URL to download from
        save_path: Local path to save the file
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)


# --- 辅助函数 ---
def get_bbox_2d_from_extents(extents):
    # [x_min, y_min, z_min, x_max, y_max, z_max] -> [x_min, y_min, x_max, y_max]
    return [extents[0], extents[1], extents[3], extents[4]]

def bboxes_2d_overlap(b1, b2):
    ix_min = max(b1[0], b2[0])
    iy_min = max(b1[1], b2[1])
    ix_max = min(b1[2], b2[2])
    iy_max = min(b1[3], b2[3])
    return (ix_max > ix_min) and (iy_max > iy_min)


@mcp.tool()
def collect_all_bboxes(json_path: str) -> dict:
    """
    读取场景JSON，收集所有物体、门、窗、墙的3D bbox即六个面的位置信息。
    返回格式：
      {
        'result': 格式化字符串,
        'obj_bbox2d': [{'id': object_id, 'bbox': [Xmin, Ymin, Zmin, Xmax, Ymax, Zmax]}, ...],
        'door_bbox': [{'id': door_id, 'bbox': [Xmin, Ymin, Zmin, Xmax, Ymax, Zmax]}, ...],
        'window_bbox': [{'id': window_id, 'bbox': [Xmin, Ymin, Zmin, Xmax, Ymax, Zmax]}, ...],
        'wall_bbox': [{'id': wall_id, 'bbox': [Xmin, Ymin, Zmin, Xmax, Ymax, Zmax]}, ...]
      }
    其中bbox为六面坐标[Xmin, Ymin, Zmin, Xmax, Ymax, Zmax]。
    如有异常，返回{'success': False, 'error': ...}
    """
    import json
    try:
        normalized_path = normalize_path(json_path)
        if not os.path.exists(normalized_path):
            return {'success': False, 'error': f'文件不存在: {normalized_path}'}
        with open(normalized_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        obj_bbox2d = []
        for obj in data.get('layout', []):
            pos = obj['position']
            size = obj['size']
            ext = [
                pos['x'] - size['length']/2, pos['y'] - size['width']/2, pos['z'],
                pos['x'] + size['length']/2, pos['y'] + size['width']/2, pos['z'] + size['height']
            ]
            obj_bbox2d.append({'id': obj['id'], 'bbox': ext})
        door_bbox = []
        window_bbox = []
        wall_bbox = []
        room = data.get('room', {})
        for door in room.get('doors', []):
            pos = door['position']
            size = door['size']
            ext = [
                pos['x'] - size['width']/2, pos['y'] - 0.01, pos['z'],
                pos['x'] + size['width']/2, pos['y'] + 0.01, pos['z'] + size['height']
            ]
            door_bbox.append({'id': door.get('id', f'door_{len(door_bbox)}'), 'bbox': ext})
        for window in room.get('windows', []):
            pos = window['position']
            size = window['size']
            ext = [
                pos['x'] - size['width']/2, pos['y'] - 0.01, pos['z'],
                pos['x'] + size['width']/2, pos['y'] + 0.01, pos['z'] + size['height']
            ]
            window_bbox.append({'id': window.get('id', f'window_{len(window_bbox)}'), 'bbox': ext})
        for wall in room.get('walls', []):
            start = wall['start']
            end = wall['end']
            height = wall['height']
            x_min = min(start['x'], end['x'])
            x_max = max(start['x'], end['x'])
            y_min = min(start['y'], end['y'])
            y_max = max(start['y'], end['y'])
            z_min = 0.0
            z_max = height
            ext = [x_min, y_min, z_min, x_max, y_max, z_max]
            wall_bbox.append({'id': wall.get('id', f'wall_{len(wall_bbox)}'), 'bbox': ext})
        # 格式化输出
        result = f"成功解析JSON文件，objects: {len(obj_bbox2d)}，doors: {len(door_bbox)}，windows: {len(window_bbox)}，walls: {len(wall_bbox)}\n\n"
        result += "所有bbox均为[Xmin, Ymin, Zmin, Xmax, Ymax, Zmax]格式。\n"
        for obj in obj_bbox2d:
            bbox = obj['bbox']
            x0, y0, z0, x1, y1, z1 = bbox
            result += f"object {obj['id']}: [{x0:.3f}, {y0:.3f}, {z0:.3f}, {x1:.3f}, {y1:.3f}, {z1:.3f}]\n"
            result += f"  - min: ({x0:.3f}, {y0:.3f}, {z0:.3f}), max: ({x1:.3f}, {y1:.3f}, {z1:.3f})\n"
        for door in door_bbox:
            bbox = door['bbox']
            x0, y0, z0, x1, y1, z1 = bbox
            result += f"door {door['id']}: [{x0:.3f}, {y0:.3f}, {z0:.3f}, {x1:.3f}, {y1:.3f}, {z1:.3f}]\n"
            result += f"  - min: ({x0:.3f}, {y0:.3f}, {z0:.3f}), max: ({x1:.3f}, {y1:.3f}, {z1:.3f})\n"
        for window in window_bbox:
            bbox = window['bbox']
            x0, y0, z0, x1, y1, z1 = bbox
            result += f"window {window['id']}: [{x0:.3f}, {y0:.3f}, {z0:.3f}, {x1:.3f}, {y1:.3f}, {z1:.3f}]\n"
            result += f"  - min: ({x0:.3f}, {y0:.3f}, {z0:.3f}), max: ({x1:.3f}, {y1:.3f}, {z1:.3f})\n"
        for wall in wall_bbox:
            bbox = wall['bbox']
            x0, y0, z0, x1, y1, z1 = bbox
            result += f"wall {wall['id']}: [{x0:.3f}, {y0:.3f}, {z0:.3f}, {x1:.3f}, {y1:.3f}, {z1:.3f}]\n"
            result += f"  - min: ({x0:.3f}, {y0:.3f}, {z0:.3f}), max: ({x1:.3f}, {y1:.3f}, {z1:.3f})\n"
        result += "\n字典格式:\n"
        result += str({'obj_bbox2d': obj_bbox2d, 'door_bbox': door_bbox, 'window_bbox': window_bbox, 'wall_bbox': wall_bbox})
        return {'result': result, 'obj_bbox2d': obj_bbox2d, 'door_bbox': door_bbox, 'window_bbox': window_bbox, 'wall_bbox': wall_bbox}
    except Exception as e:
        return {'success': False, 'error': str(e)}



# --- 支撑关系推断 ---
@mcp.tool()
def initialize_support_relation(objects: list, floor_z: float = 0.0, bboxes_dict: dict = None) -> list:
    """
    推断每个物体的支撑对象（地面/墙/其他物体/门/窗），返回详细支持关系列表。
    依赖collect_all_bboxes的obj_bbox2d、door_bbox、window_bbox、wall_bbox。
    优先级：地面>墙>其他物体>门>窗。
    
    Args:
        objects: 物体列表（layout中的对象）
        floor_z: 地面高度（默认0.0）
        bboxes_dict: collect_all_bboxes的输出字典
    Returns:
        list: 每个物体的支撑关系信息（object_id, support_type, support_id, distance, intersect_ratio）
    """
    support_all = []
    if bboxes_dict is None:
        raise ValueError('bboxes_dict must be provided')
    obj_bbox2d = bboxes_dict.get('obj_bbox2d', [])
    door_bbox = bboxes_dict.get('door_bbox', [])
    window_bbox = bboxes_dict.get('window_bbox', [])
    wall_bbox = bboxes_dict.get('wall_bbox', [])
    id2bbox = {item['id']: item['bbox'] for item in obj_bbox2d}
    def bboxes_2d_overlap(b1, b2):
        ix_min = max(b1[0], b2[0])
        iy_min = max(b1[1], b2[1])
        ix_max = min(b1[3], b2[3])
        iy_max = min(b1[4], b2[4])
        return (ix_max > ix_min) and (iy_max > iy_min)
    for obj_i in objects:
        i_extents = id2bbox[obj_i['id']]
        i_z_min = i_extents[2]
        best_supporter = None
        max_supporter_z = -float('inf')
        # 1. 墙支撑
        for wall in wall_bbox:
            j_extents = wall['bbox']
            j_z_max = j_extents[5]
            if j_z_max <= i_z_min:
                if bboxes_2d_overlap(i_extents, j_extents):
                    if j_z_max > max_supporter_z:
                        max_supporter_z = j_z_max
                        best_supporter = ('wall', wall['id'], j_extents)
        # 2. 物体支撑
        if best_supporter is None:
            for obj_j in objects:
                if obj_i['id'] == obj_j['id']:
                    continue
                j_extents = id2bbox[obj_j['id']]
                j_z_max = j_extents[5]
                if j_z_max <= i_z_min:
                    if bboxes_2d_overlap(i_extents, j_extents):
                        if j_z_max > max_supporter_z:
                            max_supporter_z = j_z_max
                            best_supporter = ('object', obj_j['id'], j_extents)
        # 3. 门支撑
        if best_supporter is None:
            for door in door_bbox:
                j_extents = door['bbox']
                j_z_max = j_extents[5]
                if j_z_max <= i_z_min:
                    if bboxes_2d_overlap(i_extents, j_extents):
                        if j_z_max > max_supporter_z:
                            max_supporter_z = j_z_max
                            best_supporter = ('door', door['id'], j_extents)
        # 4. 窗支撑
        if best_supporter is None:
            for window in window_bbox:
                j_extents = window['bbox']
                j_z_max = j_extents[5]
                if j_z_max <= i_z_min:
                    if bboxes_2d_overlap(i_extents, j_extents):
                        if j_z_max > max_supporter_z:
                            max_supporter_z = j_z_max
                            best_supporter = ('window', window['id'], j_extents)
        # 5. 地面支撑
        if best_supporter is not None:
            supporter_type, supporter_id, supporter_extents = best_supporter
            distance = i_z_min - supporter_extents[5]
            intersect = bboxes_2d_overlap(i_extents, supporter_extents)
            support_all.append({
                "object_id": obj_i["id"],
                "support_type": supporter_type,
                "support_id": supporter_id,
                "distance": distance,
                "intersect_ratio": intersect
            })
        else:
            distance_floor = i_z_min - floor_z
            support_all.append({
                "object_id": obj_i["id"],
                "support_type": "ground",
                "support_id": "floor",
                "distance": distance_floor,
                "intersect_ratio": 1.0
            })
    return support_all


# --- 物理错误检测 ---
@mcp.tool()
def compute_physical_error(objects: list, support_info: list, bboxes_dict: dict, floor_z=0.0, room_info: dict=None) -> list:
    """
    基于详细的支撑关系，检测物理合理性，返回详细错误报告。
    依赖collect_all_bboxes的输出（bboxes_dict）。
    """
    errors = []
    obj_bbox2d = bboxes_dict.get('obj_bbox2d', [])
    door_bboxes = bboxes_dict.get('door_bbox', [])
    window_bboxes = bboxes_dict.get('window_bbox', [])

    def get_bbox_2d_from_extents(extents):
        return [extents[0], extents[1], extents[3], extents[4]]

    def bboxes_2d_overlap(b1, b2):
        ix_min = max(b1[0], b2[0])
        iy_min = max(b1[1], b2[1])
        ix_max = min(b1[2], b2[2])
        iy_max = min(b1[3], b2[3])
        return (ix_max > ix_min) and (iy_max > iy_min)

    def bbox_2d_min_distance(b1, b2):
        # 计算两个2D bbox最近边缘距离（重叠为0，否则为最近边缘间距）
        # b1, b2: [xmin, ymin, xmax, ymax]
        if bboxes_2d_overlap(b1, b2):
            return 0.0
        dx = max(b1[0] - b2[2], b2[0] - b1[2], 0)
        dy = max(b1[1] - b2[3], b2[1] - b1[3], 0)
        return (dx ** 2 + dy ** 2) ** 0.5

    # --- 新增：所有物体与门窗重合/距离检测 ---
    for obj in obj_bbox2d:
        obj_id = obj['id']
        obj_bbox2d_proj = get_bbox_2d_from_extents(obj['bbox'])
        obj_zmax = obj['bbox'][5]
        # 与门重合检测
        for door_bbox in door_bboxes:
            door_bbox2d = get_bbox_2d_from_extents(door_bbox['bbox'])
            if bboxes_2d_overlap(obj_bbox2d_proj, door_bbox2d):
                errors.append({
                    "object_id": obj_id,
                    "type": "overlap_door",
                    "desc": f"物体 {obj_id} 与门 {door_bbox['id']} 重合，位置不合理。"
                })
            # 与门距离过近检测
            min_dist = bbox_2d_min_distance(obj_bbox2d_proj, door_bbox2d)
            if min_dist < 0.9:
                errors.append({
                    "object_id": obj_id,
                    "type": "traffic_blocked",
                    "desc": f"物体 {obj_id} 距离门 {door_bbox['id']} 仅 {min_dist:.2f}m，可能影响交通。"
                })
        # 与窗重合检测
        for window_bbox in window_bboxes:
            window_bbox2d = get_bbox_2d_from_extents(window_bbox['bbox'])
            if bboxes_2d_overlap(obj_bbox2d_proj, window_bbox2d):
                errors.append({
                    "object_id": obj_id,
                    "type": "overlap_window",
                    "desc": f"物体 {obj_id} 与窗 {window_bbox['id']} 重合，位置不合理。"
                })
            # 与窗距离过近且高度影响采光
            min_dist = bbox_2d_min_distance(obj_bbox2d_proj, window_bbox2d)
            if min_dist < 1.0 and obj_zmax > 1.7:
                errors.append({
                    "object_id": obj_id,
                    "type": "lighting_blocked",
                    "desc": f"物体 {obj_id} 距离窗 {window_bbox['id']} 仅 {min_dist:.2f}m 且顶部高于1.7m，可能影响采光。"
                })

    # --- 保留原有悬空和弱支撑检测 ---
    for support in support_info:
        obj_id = support['object_id']
        # 悬空检测
        if support["distance"] > 0.05: # 5cm 阈值
            errors.append({
                "object_id": obj_id,
                "type": "floating",
                "desc": f"物体 {obj_id} 悬空 {support['distance']:.3f}m, 未与支撑物 '{support['support_id']}' 接触。"
            })
        # 弱支撑检测
        if support["support_type"] == "object" and support["intersect_ratio"] < 0.5: # 50%重叠阈值
            errors.append({
                "object_id": obj_id,
                "type": "unstable_support",
                "desc": f"物体 {obj_id} 由 '{support['support_id']}' 支撑, 但2D重叠率仅为 {support['intersect_ratio']:.2f}, 可能不稳定。"
            })
    return errors

@mcp.tool()
def analyze_physical_relations(json_path: str) -> dict:
    """
    物理关系检测主函数，输入为场景布局JSON，输出详细物理错误报告（字典格式）。
    优先使用collect_all_bboxes的输出。
    """
    try:
        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        objects = data.get("layout", [])
        floor_z = 0.0  # 可根据实际场景调整
        room_info = data.get("room", None)
        bboxes_dict = collect_all_bboxes(json_path)
        support_info = initialize_support_relation(objects, floor_z, bboxes_dict)
        errors = compute_physical_error(objects, support_info, bboxes_dict, floor_z, room_info)
        report = {
            "support_info": support_info,
            "errors": errors,
            "summary": f"共检测到{len(errors)}处物理关系异常。",
            "success": True
        }
        return report
    except Exception as e:
        return {"success": False, "error": f"分析失败: {str(e)}"}



if __name__ == "__main__":
    mcp.run(transport='stdio')
