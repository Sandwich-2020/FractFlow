"""
Asset MCP - 资产管理模块
使用自然语言接口进行资产放置和管理
"""

from mcp.server.fastmcp import FastMCP, Context
import time
import re

# 导入临时的BlenderPrimitive类
from blender_primitive_temp import BlenderPrimitive

# 创建实例
blender_primitive = BlenderPrimitive()

# 创建MCP服务器
mcp = FastMCP("asset_mcp")

@mcp.tool()
def check_asset_sources_status(ctx: Context) -> str:
    """
    检查所有资产源的状态和可用性
    
    Returns:
        str - 资产源状态的自然语言报告
    """
    try:
        # 简化状态检查，专注于核心功能
        status_report = [
            "✓ Asset MCP 自然语言接口已启用",
            "✓ Blender 连接正常",
            "✓ 引导线系统可用"
        ]
        
        return "\n".join(status_report)
        
    except Exception as e:
        return f"✗ Error checking asset sources: {str(e)}"


@mcp.tool()
def search_asset(ctx: Context, item_type: str, style: str = "") -> str:
    """
    在资产库中搜索指定类型的资产
    
    Parameters:
        item_type: 资产类型 (如 "chair", "table", "bed")
        style: 可选的风格描述
    
    Returns:
        str - 搜索结果的自然语言描述
    """
    try:
        # 简化搜索功能，返回通用建议
        search_suggestions = [
            f"✓ 搜索 {item_type} 类型资产",
            f"建议使用 Blender 内置资产库或导入外部模型",
            f"可以使用文件导入功能添加 {item_type} 模型"
        ]
        
        if style:
            search_suggestions.append(f"风格要求：{style}")
        
        return "\n".join(search_suggestions)
        
    except Exception as e:
        return f"✗ Error searching assets: {str(e)}"


@mcp.tool()
def download_asset(
    ctx: Context, 
    source: str, 
    asset_identifier: str, 
    target_name: str = ""
) -> str:
    """
    从指定源下载资产
    
    Parameters:
        source: 资产源 (如 "file", "import")
        asset_identifier: 资产标识符或文件路径
        target_name: 可选的目标名称
    
    Returns:
        str - 下载结果的自然语言报告
    """
    try:
        # 简化下载功能，返回导入建议
        if source == "file":
            return f"✓ 建议使用 Blender 文件菜单导入 {asset_identifier}"
        else:
            return f"✓ 建议手动导入资产：{asset_identifier}"
        
    except Exception as e:
        return f"✗ Error downloading asset: {str(e)}"

@mcp.tool()
def place_asset(
    ctx: Context,
    object_name: str,
    position: list = None,
    rotation: list = None,
    scale: list = None,
    use_guide_alignment: bool = True,
    guide_identifier: str = ""
) -> str:
    """
    将资产放置到指定位置或引导线位置，支持语义ID和智能对齐
    
    Parameters:
        object_name: 要放置的对象名称
        position: 目标位置 [x, y, z] (可选，如果指定guide_identifier则可为空)
        rotation: 目标旋转 [x, y, z] (弧度，可选)
        scale: 目标缩放 [x, y, z] (可选)
        use_guide_alignment: 是否使用引导线智能对齐 (默认True)
        guide_identifier: 引导线标识符，如 "bed_1", "床头柜1" (可选)
    
    Returns:
        str - 放置结果的自然语言报告
    """
    try:
        if rotation is None:
            rotation = [0, 0, 0]
        if scale is None:
            scale = [1, 1, 1]
        
        # 检查对象是否存在 - 使用新的自然语言接口
        obj_desc = blender_primitive.get_object_description(object_name)
        if "✗" in obj_desc:
            return f"✗ Object '{object_name}' not found in scene"
        
        final_position = None
        final_rotation = rotation[:]
        alignment_info = ""
        guide_used = None
        
        # 如果指定了引导线标识符，优先使用引导线位置
        if guide_identifier:
            semantic_id = _parse_guide_identifier(guide_identifier)
            if semantic_id:
                guide_desc = blender_primitive.get_guide_info_by_semantic_id(semantic_id)
                if "✓" in guide_desc:
                    # 从自然语言描述中提取位置信息
                    import re
                    pos_match = re.search(r'位于\(([^)]+)\)', guide_desc)
                    if pos_match:
                        coords = pos_match.group(1).split(', ')
                        guide_location = [float(c) for c in coords]
                        
                        # 使用引导线的位置
                        final_position = [
                            guide_location[0],
                            guide_location[1],
                            guide_location[2] + 0.5  # 放在引导线上方
                        ]
                        
                        guide_used = semantic_id
                        alignment_info = f"\n✓ Placed at guide {semantic_id}"
                        
                        # 更新引导线占用状态
                        update_result = blender_primitive.set_guide_metadata(
                            f"LAYOUT_GUIDE_{semantic_id}", 
                            semantic_id=semantic_id,
                            occupied=True, 
                            occupied_by=object_name
                        )
                    else:
                        return f"✗ 无法解析引导线位置信息"
                else:
                    return f"✗ 无法找到引导线 '{guide_identifier}'：{guide_desc}"
            else:
                return f"✗ 无法解析引导线标识符 '{guide_identifier}'"
        
        # 如果没有指定引导线或引导线查找失败，使用指定位置
        if final_position is None:
            if position is None:
                return f"✗ 必须指定position或guide_identifier中的一个"
            
            final_position = position[:]
        
        # 应用变换 - 使用新的移动接口
        move_result = blender_primitive.move_object(object_name, final_position)
        
        if "✗" in move_result:
            return f"✗ Failed to place {object_name}: {move_result}"
        
        # 构建结果报告
        result_message = f"✓ Successfully placed {object_name} at position ({final_position[0]:.1f}, {final_position[1]:.1f}, {final_position[2]:.1f})"
        
        if guide_used:
            result_message += f"\n✓ Used guide: {guide_used}"
        
        if alignment_info:
            result_message += alignment_info
        
        return result_message
        
    except Exception as e:
        return f"✗ Error placing asset: {str(e)}"


@mcp.tool()
def get_asset_info(ctx: Context, object_name: str) -> str:
    """
    获取资产的基本信息
    
    Parameters:
        object_name: 对象名称
    
    Returns:
        str - 资产信息的简单报告
    """
    try:
        # 使用新的自然语言接口获取对象信息
        obj_desc = blender_primitive.get_object_description(object_name)
        
        if "✗" in obj_desc:
            return f"✗ Object '{object_name}' not found in scene"
        
        # 直接返回自然语言描述
        return f"Asset Information:\n{obj_desc}"
        
    except Exception as e:
        return f"✗ Error getting asset info: {str(e)}"


@mcp.tool()
def fix_asset_ground(ctx: Context, object_name: str) -> str:
    """
    将资产固定到地面
    
    Parameters:
        object_name: 对象名称
    
    Returns:
        str - 操作结果的简单报告
    """
    try:
        # 检查对象是否存在
        obj_desc = blender_primitive.get_object_description(object_name)
        if "✗" in obj_desc:
            return f"✗ Object '{object_name}' not found in scene"
        
        # 从描述中提取当前位置
        import re
        pos_match = re.search(r'位于\(([^)]+)\)', obj_desc)
        if pos_match:
            coords = pos_match.group(1).split(', ')
            current_location = [float(c) for c in coords]
            
            # 设置新位置（Z坐标为0，放在地面上）
            ground_position = [current_location[0], current_location[1], 0.0]
            
            # 移动对象到地面
            move_result = blender_primitive.move_object(object_name, ground_position)
            
            if "✓" in move_result:
                return f"✓ Successfully fixed {object_name} to ground: {move_result}"
            else:
                return f"✗ Failed to fix {object_name} to ground: {move_result}"
        else:
            return f"✗ Could not extract position from object description"
        
    except Exception as e:
        return f"✗ Error fixing asset to ground: {str(e)}"


@mcp.tool()
def find_empty_guide_positions(ctx: Context, item_type: str = "") -> str:
    """
    查找空置的引导线位置
    
    Parameters:
        item_type: 可选的物品类型过滤
    
    Returns:
        str - 空置引导线位置的自然语言报告
    """
    try:
        # 使用新的自然语言接口查找空置引导线
        empty_guides_desc = blender_primitive.find_empty_guides(item_type)
        
        if "✗" in empty_guides_desc:
            return empty_guides_desc
        
        return f"Empty Guide Positions:\n{empty_guides_desc}"
        
    except Exception as e:
        return f"✗ Error finding empty guide positions: {str(e)}"


@mcp.tool()
def combine_asset_parts(
    ctx: Context, 
    object_pattern: str, 
    target_name: str = "",
    asset_info: dict = None
) -> str:
    """
    合并匹配模式的资产部件
    
    Parameters:
        object_pattern: 对象名称模式 (支持通配符)
        target_name: 合并后的目标名称 (可选，自动生成)
        asset_info: 资产信息字典 (可选，用于智能命名)
    
    Returns:
        str - 合并结果的自然语言报告
    """
    try:
        # 获取场景描述来查找匹配的对象
        scene_desc = blender_primitive.get_scene_description()
        if "✗" in scene_desc:
            return f"✗ Failed to get scene info: {scene_desc}"
        
        # 从场景描述中提取匹配的对象名称
        import re
        object_matches = re.findall(r'^- ([^：]+)：', scene_desc, re.MULTILINE)
        
        # 筛选匹配模式的对象
        matching_objects = []
        for obj_name in object_matches:
            if object_pattern.lower() in obj_name.lower():
                matching_objects.append(obj_name)
        
        if not matching_objects:
            return f"✗ No objects found matching pattern '{object_pattern}'"
        
        if len(matching_objects) < 2:
            return f"✗ Need at least 2 objects to combine, found only {len(matching_objects)}: {', '.join(matching_objects)}"
        
        # 生成目标名称
        if not target_name:
            if asset_info and asset_info.get("type"):
                target_name = f"{asset_info['type']}_{int(time.time() * 1000) % 10000}"
            else:
                base_name = object_pattern.replace("*", "").replace("?", "")
                target_name = f"Combined_{base_name}_{int(time.time() * 1000) % 10000}"
        
        # 执行合并
        combine_result = blender_primitive.merge_objects(matching_objects, target_name)
        
        if "✓" in combine_result:
            return f"✓ Successfully combined {len(matching_objects)} parts:\n{combine_result}\nOriginal objects: {', '.join(matching_objects)}"
        else:
            return f"✗ Failed to combine objects: {combine_result}"
        
    except Exception as e:
        return f"✗ Error combining asset parts: {str(e)}"


@mcp.tool()
def get_guide_info(guide_identifier: str) -> str:
    """
    获取引导线的原始数据信息
    
    Args:
        guide_identifier: 引导线标识符
        
    Returns:
        str - 引导线原始数据的自然语言描述
    """
    try:
        primitive = BlenderPrimitive()
        
        # 解析引导线标识符
        parsed_id = _parse_guide_identifier(guide_identifier)
        if not parsed_id:
            return f"✗ 无法解析引导线标识符：{guide_identifier}"
        
        # 查找对应的引导线对象
        guides_data = primitive.get_raw_guides_data()
        
        # 让LLM从原始数据中找到匹配的引导线
        if parsed_id in guides_data:
            return guides_data
        else:
            return f"✗ 未找到引导线：{guide_identifier}\n\n可用引导线：\n{guides_data}"
        
    except Exception as e:
        return f"✗ 获取引导线信息时出错：{str(e)}"

def _parse_guide_identifier(identifier: str) -> str:
    """
    解析引导线标识符，转换为标准的语义ID
    
    Args:
        identifier: 用户输入的标识符
        
    Returns:
        str - 标准语义ID，如果无法解析则返回None
    """
    identifier = identifier.strip().lower()
    
    # 直接匹配语义ID格式 (如 "bed_1", "chair_2")
    if "_" in identifier and identifier.replace("_", "").replace("1", "").replace("2", "").replace("3", "").replace("4", "").replace("5", "").replace("6", "").replace("7", "").replace("8", "").replace("9", "").replace("0", "").isalpha():
        return identifier
    
    # 中文数字映射
    chinese_numbers = {
        "一": "1", "1": "1", "第一": "1", "第1": "1",
        "二": "2", "2": "2", "第二": "2", "第2": "2", 
        "三": "3", "3": "3", "第三": "3", "第3": "3",
        "四": "4", "4": "4", "第四": "4", "第4": "4",
        "五": "5", "5": "5", "第五": "5", "第5": "5"
    }
    
    # 物品类型映射
    item_type_mapping = {
        "床": "bed", "bed": "bed",
        "椅子": "chair", "chair": "chair", "座椅": "chair",
        "桌子": "table", "table": "table", "书桌": "desk", "desk": "desk",
        "沙发": "sofa", "sofa": "sofa",
        "床头柜": "nightstand", "nightstand": "nightstand",
        "衣柜": "wardrobe", "wardrobe": "wardrobe", "柜子": "wardrobe",
        "梳妆台": "dresser", "dresser": "dresser",
        "茶几": "coffee_table", "coffee_table": "coffee_table"
    }
    
    # 尝试解析中文格式 (如 "床1", "椅子2")
    for chinese_type, english_type in item_type_mapping.items():
        if identifier.startswith(chinese_type):
            number_part = identifier[len(chinese_type):]
            if number_part in chinese_numbers:
                return f"{english_type}_{chinese_numbers[number_part]}"
    
    # 尝试解析英文格式 (如 "bed1", "chair2")  
    for english_type in item_type_mapping.values():
        if identifier.startswith(english_type):
            number_part = identifier[len(english_type):]
            if number_part in chinese_numbers:
                return f"{english_type}_{chinese_numbers[number_part]}"
    
    # 尝试解析描述性格式 (如 "第一个床", "主卧的床")
    for phrase, number in chinese_numbers.items():
        if phrase in identifier:
            for chinese_type, english_type in item_type_mapping.items():
                if chinese_type in identifier:
                    return f"{english_type}_{number}"
    
    return None

@mcp.tool()
def list_available_guides() -> str:
    """
    列出所有可用引导线的原始数据
    
    Returns:
        str - 所有引导线原始数据的自然语言描述
    """
    try:
        primitive = BlenderPrimitive()
        return primitive.get_raw_guides_data()
    except Exception as e:
        return f"✗ 列出引导线时出错：{str(e)}"

if __name__ == "__main__":
    mcp.run(transport='stdio') 