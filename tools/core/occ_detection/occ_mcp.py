import os
import numpy as np
from typing import List, Dict, Tuple
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("3d_iou")

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

def calculate_overlap_1d(min1: float, max1: float, min2: float, max2: float) -> Tuple[float, float, float]:
    """
    计算1D线段的重叠情况
    
    Args:
        min1, max1: 第一个线段的范围
        min2, max2: 第二个线段的范围
        
    Returns:
        Tuple[float, float, float]: (重叠长度, 重叠方向, 重叠中心点)
        重叠方向: 1表示正向重叠(2在1右侧), -1表示负向重叠(2在1左侧)
    """
    # 计算重叠区间
    overlap_min = max(min1, min2)
    overlap_max = min(max1, max2)
    overlap_len = max(0, overlap_max - overlap_min)
    
    if overlap_len == 0:
        return 0, 0, 0
    
    # 计算重叠方向
    center1 = (min1 + max1) / 2
    center2 = (min2 + max2) / 2
    direction = 1 if center2 > center1 else -1
    
    # 计算重叠中心点
    overlap_center = (overlap_min + overlap_max) / 2
    
    return overlap_len, direction, overlap_center

@mcp.tool()
def calculate_3d_iou(bbox1: List[float], bbox2: List[float]) -> str:
    """
    计算两个3D边界框的IOU loss，并分析重叠情况
    
    Args:
        bbox1: 第一个边界框 [cx, cy, bz, dx, dy, dz]，其中(cx,cy,bz)是底部的中心点，(dx,dy,dz)是各轴向的长度
        bbox2: 第二个边界框 [cx, cy, bz, dx, dy, dz]
        
    Returns:
        str: 包含IOU值和重叠分析的结果描述
    """
    try:
        # 提取边界框参数
        x1, y1, z1, dx1, dy1, dz1 = bbox1
        x2, y2, z2, dx2, dy2, dz2 = bbox2
        
        # 计算每个边界框的最小/最大坐标
        box1_min = [x1 - dx1/2, y1 - dy1/2, z1]
        box1_max = [x1 + dx1/2, y1 + dy1/2, z1 + dz1]
        box2_min = [x2 - dx2/2, y2 - dy2/2, z2]
        box2_max = [x2 + dx2/2, y2 + dy2/2, z2 + dz2]
        
        # 计算三个轴向的重叠
        overlaps = []
        directions = []
        centers = []
        for i in range(3):
            overlap, direction, center = calculate_overlap_1d(
                box1_min[i], box1_max[i],
                box2_min[i], box2_max[i]
            )
            overlaps.append(overlap)
            directions.append(direction)
            centers.append(center)
        
        # 计算体积
        volume1 = dx1 * dy1 * dz1
        volume2 = dx2 * dy2 * dz2
        overlap_volume = overlaps[0] * overlaps[1] * overlaps[2]
        union_volume = volume1 + volume2 - overlap_volume
        
        # 计算IOU
        iou = overlap_volume / union_volume if union_volume > 0 else 0
        
        # 生成结果报告
        result = f"3D IOU 计算结果:\n"
        result += f"IOU = {iou:.4f}\n"
        
        # 如果有重叠，分析重叠情况
        if iou > 0:
            result += "\n重叠分析:\n"
            
            # X轴重叠
            if overlaps[0] > 0:
                direction_x = "右" if directions[0] > 0 else "左"
                result += f"X轴: bbox2在bbox1{direction_x}侧重叠，重叠长度 {overlaps[0]:.3f}\n"
            
            # Y轴重叠
            if overlaps[1] > 0:
                direction_y = "前" if directions[1] > 0 else "后"
                result += f"Y轴: bbox2在bbox1{direction_y}侧重叠，重叠长度 {overlaps[1]:.3f}\n"
            
            # Z轴重叠
            if overlaps[2] > 0:
                direction_z = "上" if directions[2] > 0 else "下"
                result += f"Z轴: bbox2在bbox1{direction_z}侧重叠，重叠长度 {overlaps[2]:.3f}\n"
            
            # 重叠体积
            result += f"\n重叠体积: {overlap_volume:.3f}\n"
            result += f"总体积: {union_volume:.3f}\n"
            
            # 重叠中心点
            result += f"重叠区域中心点: ({centers[0]:.3f}, {centers[1]:.3f}, {centers[2]:.3f})"
        
        return result
        
    except Exception as e:
        return f"计算过程中出现错误: {str(e)}"

@mcp.tool()
def read_json(json_path: str) -> str:
    """
    读取室内布局JSON文件，解析objects并转换为bbox格式
    
    Args:
        json_path: JSON文件路径
        
    Returns:
        str: 包含所有objects的bbox信息的字典描述，格式为object_id: [x,y,z,dx,dy,dz]
        其中(x,y,z)是bbox的起始位置（左下后角），(dx,dy,dz)是各轴向的长度
    """
    import json
    
    try:
        # 规范化路径
        normalized_path = normalize_path(json_path)
        
        # 检查文件是否存在
        if not os.path.exists(normalized_path):
            return f"错误：文件不存在 - {normalized_path}"
        
        # 读取JSON文件
        with open(normalized_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查JSON结构
        if 'layout' not in data :
            return "错误：JSON文件格式不正确"
        
        # 解析objects并转换坐标
        bbox_dict = {}
        for obj in data['layout']:
            # 提取基本信息
            obj_id = obj['id']
            position = obj['position']  # {x, y, z} - 中心位置
            size = obj['size']  # {length, width, height}
            
            # 从中心位置转换为起始位置（左下后角）
            center_x, center_y, center_z = position['x'], position['y'], position['z']
            dx, dy, dz = size['length'], size['width'], size['height']
            
            # 计算bbox起始位置
            start_x = center_x - dx / 2
            start_y = center_y - dy / 2
            start_z = center_z - dz / 2
            
            # 存储为[x, y, z, dx, dy, dz]格式
            bbox_dict[obj_id] = [start_x, start_y, start_z, dx, dy, dz]
        
        # 格式化输出结果
        result = f"成功解析JSON文件，共找到 {len(bbox_dict)} 个objects:\n\n"
        
        for obj_id, bbox in bbox_dict.items():
            x, y, z, dx, dy, dz = bbox
            result += f"{obj_id}: [{x:.3f}, {y:.3f}, {z:.3f}, {dx:.3f}, {dy:.3f}, {dz:.3f}]\n"
            result += f"  - 起始位置: ({x:.3f}, {y:.3f}, {z:.3f})\n"
            result += f"  - 尺寸: {dx:.3f} × {dy:.3f} × {dz:.3f}\n\n"
        
        # 同时返回字典的字符串表示，便于后续处理
        result += "\n字典格式:\n"
        result += str(bbox_dict)
        
        return result
        
    except json.JSONDecodeError as e:
        return f"JSON解析错误: {str(e)}"
    except Exception as e:
        return f"读取文件时出现错误: {str(e)}"

@mcp.tool()
def scale_object_location(object_dict:dict,rescale_size: dict) -> str:
    """
    移动和放缩物体位置
    
    Args:
        object_dict: 物体字典{key: obj_id, value: [cx, cy, cz,dx,dy,dz]}
        rescale_size: 放缩尺寸 {key: obj_id, value: rescale_size}rescale_size,那么则是缩小，如果大于1，则是放大，如果等于1，则不进行放缩

    """
    for obj_id, bbox in object_dict.items():
        bbox[3] *= rescale_size[obj_id]
        bbox[4] *= rescale_size[obj_id]
        bbox[5] *= rescale_size[obj_id]
    return object_dict

@mcp.tool()
def calcute_rescale_size(bbox1: List[float], bbox2: List[float],overlap_length: List[float], ratio:float = 0.5) -> dict:
    """
    bbox1: 第一个边界框 [x, y, z, dx, dy, dz]，其中(x,y,z)是底部的中心点，(dx,dy,dz)是各轴向的长度
    bbox2: 第二个边界框 [x, y, z, dx, dy, dz]
    overlap_length: 重叠长度 [overlap_x, overlap_y, overlap_z]
    ratio: 缩放比例这个缩放比例是基于重叠长度来缩放的，如果是0.7，那么则是bbox1缩放重叠长度的0.7，bbox2缩放重叠长度的0.3
    Returns:
        dict: 放缩尺寸 rescale_size1，rescale_size2
    """
    # 提取两个边界框的尺寸
    # 如果没有传入ratio或ratio无效，使用默认值0.5
    if ratio <= 0 or ratio >= 1:
        ratio = 0.5
    dx1, dy1, dz1 = bbox1[3], bbox1[4], bbox1[5]  # bbox1的xyz尺寸
    dx2, dy2, dz2 = bbox2[3], bbox2[4], bbox2[5]  # bbox2的xyz尺寸
    
    # 提取重叠长度
    overlap_x, overlap_y, overlap_z = overlap_length[0], overlap_length[1], overlap_length[2]
    
    # 两个物体均缩放，每个物体需要缩放重叠长度的一半
    # bbox1在各轴需要缩放的长度
    bbox1_shrink_x = overlap_x * ratio  # 0.05
    bbox1_shrink_y = overlap_y * ratio  # 0.1  
    bbox1_shrink_z = overlap_z * ratio  # 0.15
    
    # bbox2在各轴需要缩放的长度
    bbox2_shrink_x = overlap_x * (1-ratio)  # 0.05
    bbox2_shrink_y = overlap_y * (1-ratio)  # 0.1
    bbox2_shrink_z = overlap_z * (1-ratio)  # 0.15
    
    # 计算bbox1在各轴的缩放比例
    # 基于中心点的缩放，缩放比例 = 1 - (需要缩放的长度 / 原长度)
    # 因为是基于中心点缩放，两头都会缩放，所以需要乘以2
    bbox1_scale_x = 1 - (bbox1_shrink_x / dx1 * 2)  # 1-(0.05/0.4*2)
    bbox1_scale_y = 1 - (bbox1_shrink_y / dy1 * 2)  # 1-(0.1/0.5*2)
    bbox1_scale_z = 1 - (bbox1_shrink_z / dz1 * 2)  # 1-(0.15/0.6*2)
    
    # 计算bbox2在各轴的缩放比例
    bbox2_scale_x = 1 - (bbox2_shrink_x / dx2 * 2)  # 1-(0.05/0.7*2)
    bbox2_scale_y = 1 - (bbox2_shrink_y / dy2 * 2)  # 1-(0.1/0.8*2)
    bbox2_scale_z = 1 - (bbox2_shrink_z / dz2 * 2)  # 1-(0.15/0.9*2)
    
    # 选择最大的缩放比例（即最小的数值，因为小于1表示缩小）
    # bbox1选择缩放程度最大的轴（数值最小）
    bbox1_rescale = min(bbox1_scale_x, bbox1_scale_y, bbox1_scale_z)
    
    # bbox2选择缩放程度最大的轴（数值最小）  
    bbox2_rescale = min(bbox2_scale_x, bbox2_scale_y, bbox2_scale_z)
    
    return {
        "bbox1_rescale": bbox1_rescale-0.01,
        "bbox2_rescale": bbox2_rescale-0.01
    }


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 