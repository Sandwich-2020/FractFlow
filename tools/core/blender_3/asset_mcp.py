"""
Asset MCP - 资产管理模块
使用自然语言接口进行资产放置和管理
"""

from mcp.server.fastmcp import FastMCP, Context
import time
import re

# 导入临时的BlenderPrimitive类
from blender_primitive import BlenderPrimitive

# 创建实例
blender_primitive = BlenderPrimitive()

# 创建MCP服务器
mcp = FastMCP("asset_mcp")

# ========== 内部辅助函数 ==========

# 删除了不再需要的辅助函数，直接使用blender-mcp的返回值

# ========== MCP工具函数 ==========

@mcp.tool()
def check_asset_sources_status(ctx: Context) -> str:
    """
    检查所有资产源的连接状态
    
    Returns:
        str - 各个资产源的状态报告
    """
    try:
        status_report = []
        
        # 检查PolyHaven状态
        polyhaven_status = get_polyhaven_status(ctx)
        status_report.append(f"PolyHaven: {polyhaven_status}")
        
        # 检查Sketchfab状态  
        sketchfab_status = get_sketchfab_status(ctx)
        status_report.append(f"Sketchfab: {sketchfab_status}")
        
        # 检查Hyper3D状态
        hyper3d_status = get_hyper3d_status(ctx)
        status_report.append(f"Hyper3D: {hyper3d_status}")
        
        return "✓ Asset Sources Status:\n" + "\n".join(status_report)
        
    except Exception as e:
        return f"✗ Error checking asset sources: {str(e)}"

@mcp.tool()
def search_asset(ctx: Context, item_type: str, style: str = "") -> str:
    """
    在多个资产源中搜索指定类型的资产
    
    Parameters:
        item_type: 资产类型，如"双人床"、"沙发"、"桌子"等
        style: 可选的风格描述，如"现代"、"古典"、"简约"等
    
    Returns:
        str - 搜索结果的详细报告，包含资产信息和下载标识符
    """
    try:
        search_results = []
        
        # 构建搜索查询
        search_query = f"{item_type} {style}".strip()
        
        # 搜索PolyHaven
        try:
            polyhaven_result = search_polyhaven_assets(ctx, "models", None)
            if "✓" in polyhaven_result:
                search_results.append(f"PolyHaven结果:\n{polyhaven_result}")
        except Exception as e:
            search_results.append(f"PolyHaven搜索失败: {str(e)}")
        
        # 搜索Sketchfab
        try:
            sketchfab_result = search_sketchfab_models(ctx, search_query, None, 20, True)
            if "✓" in sketchfab_result or "models found" in sketchfab_result:
                search_results.append(f"Sketchfab结果:\n{sketchfab_result}")
        except Exception as e:
            search_results.append(f"Sketchfab搜索失败: {str(e)}")
        
        if search_results:
            return "✓ 找到以下资产:\n\n" + "\n\n".join(search_results)
        else:
            return f"✗ 未找到匹配 '{search_query}' 的资产"
        
    except Exception as e:
        return f"✗ 搜索资产时出错: {str(e)}"

@mcp.tool()
def download_asset(
    ctx: Context, 
    source: str, 
    asset_identifier: str, 
    target_name: str,
    target_guide: str,
    target_scale: list
) -> str:
    """
    从指定源下载资产，自动合并、设置绝对尺寸并准备放置
    
    Parameters:
        source: 资产源 ("polyhaven", "sketchfab", "hyper3d", 或 "file")
        asset_identifier: 资产标识符或文件路径
        target_name: 目标名称（必须！如"Master_Bed_Double"）
        target_guide: 目标引导线标识符（必须！如"bed_1"）
        target_scale: 目标绝对尺寸（必须！[长, 宽, 高] 米，如[2.0, 1.5, 0.5]）
    
    Returns:
        str - 下载、尺寸设置和放置准备的完整结果报告
    """
    try:
        # 验证必须参数
        if not target_name:
            return f"✗ target_name is required"
        if not target_guide:
            return f"✗ target_guide is required"
        if not target_scale or len(target_scale) == 0:
            return f"✗ target_scale is required"
        
        # 1. 执行下载操作，获取完整结果
        download_result = None
        if source.lower() == "polyhaven":
            download_result = _download_polyhaven_asset_raw(ctx, asset_identifier, "models", "1k")
        elif source.lower() == "sketchfab":
            download_result = _download_sketchfab_model_raw(ctx, asset_identifier)
        elif source.lower() == "hyper3d":
            download_result = _generate_hyper3d_model_raw(ctx, asset_identifier)
        elif source.lower() == "file":
            return f"✓ 建议使用 Blender 文件菜单导入 {asset_identifier}"
        else:
            return f"✗ 不支持的资产源: {source}"
        
        # 2. 检查下载结果
        if not download_result or download_result.get("error"):
            error_msg = download_result.get("error", "Unknown error") if download_result else "No result"
            return f"✗ 下载失败: {error_msg}"
        
        if not download_result.get("success"):
            return f"✗ 下载失败: {download_result}"
        
        # 3. 获取导入的对象列表（直接从blender-mcp返回值）
        imported_objects = download_result.get("imported_objects", [])
        if not imported_objects:
            return f"✗ 下载成功但未检测到导入的对象: {download_result}"
        
        # 4. 处理导入的对象
        final_object_name = target_name
        
        if len(imported_objects) == 1:
            # 只有一个对象，直接重命名
            original_name = imported_objects[0]
            if original_name != target_name:
                rename_result = blender_primitive.send_command("rename_object", {
                    "old_name": original_name,
                    "new_name": target_name
                })
                if isinstance(rename_result, dict) and rename_result.get("error"):
                    return f"✗ 重命名失败: {rename_result['error']}"
        else:
            # 多个对象，合并它们
            merge_result = blender_primitive.merge_objects(imported_objects, target_name)
            if "✗" in merge_result:
                return f"✗ 合并对象失败: {merge_result}"
        
        # 5. 设置绝对尺寸
        scale_result = scale_object(ctx, final_object_name, target_scale)
        if "✗" in scale_result:
            return f"✗ 缩放失败: {scale_result}"
        
        # 6. 获取引导线信息
        guides_info = blender_primitive.get_guide_info_by_semantic_id(target_guide)
        if "✗" in guides_info:
            return f"✗ 无法找到引导线 '{target_guide}': {guides_info}"
        
        return f"""✓ 资产下载和准备完成！

📦 下载详情: 
   - 源: {source}
   - 标识符: {asset_identifier}
   - 导入对象数: {len(imported_objects)}
   - 导入对象: {imported_objects}

🎯 处理结果:
   - 最终对象名称: {final_object_name}
   - 缩放结果: {scale_result}

📍 下一步：请从以下引导线信息中提取位置坐标，然后调用move_object将'{final_object_name}'移动到正确位置：
{guides_info}

建议调用: move_object("{final_object_name}", [x, y, z])"""
        
    except Exception as e:
        return f"✗ 下载资产时出错: {str(e)}"

@mcp.tool()
def place_asset(
    ctx: Context,
    object_name: str,
    guide_identifier: str,
    apply_scale: list = None,
    apply_rotation: list = None
) -> str:
    """
    将资产完整放置到引导线位置，组合使用独立的变换工具
    
    Parameters:
        object_name: 要放置的对象名称
        guide_identifier: 引导线标识符（必须！如 "bed_1", "床头柜1"）
        apply_scale: 可选的缩放调整 [x, y, z] 或 [uniform_scale]
        apply_rotation: 可选的旋转调整 [x, y, z] (弧度)
    
    Returns:
        str - 完整放置结果的自然语言报告
    """
    try:
        # 检查对象是否存在
        obj_desc = blender_primitive.get_object_description(object_name)
        if "✗" in obj_desc:
            return f"✗ Object '{object_name}' not found in scene"
        
        results = []
        
        # 1. 应用缩放（如果指定）
        if apply_scale:
            scale_result = scale_object(ctx, object_name, apply_scale)
            results.append(f"缩放: {scale_result}")
            if "✗" in scale_result:
                return f"✗ 缩放失败: {scale_result}"
        
        # 2. 应用旋转（如果指定）
        if apply_rotation:
            rotate_result = rotate_object(ctx, object_name, apply_rotation)
            results.append(f"旋转: {rotate_result}")
            if "✗" in rotate_result:
                return f"✗ 旋转失败: {rotate_result}"
        
        # 3. 获取引导线信息并移动到位置
        guides_info = blender_primitive.get_guide_info_by_semantic_id(guide_identifier)
        
        if "✓" in guides_info:
            # 返回引导线信息，让LLM分析并调用move_object
            guide_info_msg = f"""
{guides_info}

任务：将对象 '{object_name}' 移动到引导线 '{guide_identifier}' 的位置

请从上述原始数据中：
1. 找到语义ID或名称匹配 '{guide_identifier}' 的引导线
2. 提取其location坐标
3. 调用 move_object("{object_name}", [x, y, z]) 完成放置

当前对象信息：{obj_desc}
"""
            
            if results:
                return f"✓ 变换操作完成:\n" + "\n".join(results) + f"\n\n{guide_info_msg}"
            else:
                return guide_info_msg
        else:
            return f"✗ 无法找到引导线 '{guide_identifier}': {guides_info}"
        
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


# combine_asset_parts 已移至内部函数 _combine_objects

# ========== 原始下载函数（内部使用） ==========

def _download_polyhaven_asset_raw(
    ctx: Context,
    asset_id: str,
    asset_type: str,
    resolution: str = "1k",
    file_format: str = None
) -> dict:
    """
    使用blender-mcp原生下载PolyHaven资产，返回完整结果
    
    Returns:
        dict - blender-mcp的原始返回结果，包含imported_objects列表
    """
    try:
        result = blender_primitive.send_command("download_polyhaven_asset", {
            "asset_id": asset_id,
            "asset_type": asset_type,
            "resolution": resolution,
            "file_format": file_format
        })
        
        # blender-mcp可能返回字符串或dict，需要统一处理
        if isinstance(result, str):
            try:
                # 尝试解析JSON字符串
                import json
                parsed_result = json.loads(result)
                return parsed_result
            except (json.JSONDecodeError, ValueError):
                # 如果不是JSON，检查是否是成功消息
                if "imported successfully" in result or "success" in result.lower():
                    # 从字符串中提取对象名称（简单解析）
                    if "imported_objects" in result:
                        # 尝试提取对象列表
                        import re
                        objects_match = re.search(r"imported_objects.*?(\[.*?\])", result)
                        if objects_match:
                            try:
                                objects_list = eval(objects_match.group(1))  # 简单评估
                                return {"success": True, "imported_objects": objects_list, "message": result}
                            except:
                                pass
                    # 如果无法提取，返回通用成功结果
                    return {"success": True, "imported_objects": [asset_id], "message": result}
                else:
                    return {"error": result, "success": False}
        elif isinstance(result, dict):
            return result
        else:
            return {"error": f"Unexpected result type: {type(result)}", "success": False}
        
    except Exception as e:
        return {"error": str(e), "success": False}

def _download_sketchfab_model_raw(ctx: Context, uid: str) -> dict:
    """
    使用blender-mcp原生下载Sketchfab模型，返回完整结果
    
    Returns:
        dict - blender-mcp的原始返回结果，包含imported_objects列表
    """
    try:
        result = blender_primitive.send_command("download_sketchfab_model", {
            "uid": uid
        })
        
        # blender-mcp可能返回字符串或dict，需要统一处理
        if isinstance(result, str):
            try:
                # 尝试解析JSON字符串
                import json
                parsed_result = json.loads(result)
                return parsed_result
            except (json.JSONDecodeError, ValueError):
                # 如果不是JSON，检查是否是成功消息
                if "imported successfully" in result or "success" in result.lower():
                    # 从字符串中提取对象名称（简单解析）
                    if "imported_objects" in result:
                        # 尝试提取对象列表
                        import re
                        objects_match = re.search(r"imported_objects.*?(\[.*?\])", result)
                        if objects_match:
                            try:
                                objects_list = eval(objects_match.group(1))  # 简单评估
                                return {"success": True, "imported_objects": objects_list, "message": result}
                            except:
                                pass
                    # 如果无法提取，返回通用成功结果
                    return {"success": True, "imported_objects": [uid], "message": result}
                else:
                    return {"error": result, "success": False}
        elif isinstance(result, dict):
            return result
        else:
            return {"error": f"Unexpected result type: {type(result)}", "success": False}
        
    except Exception as e:
        return {"error": str(e), "success": False}

def _generate_hyper3d_model_raw(
    ctx: Context,
    text_prompt: str,
    bbox_condition: list = None
) -> dict:
    """
    使用blender-mcp原生生成Hyper3D模型，返回完整结果
    
    Returns:
        dict - blender-mcp的原始返回结果
    """
    try:
        result = blender_primitive.send_command("generate_hyper3d_model_via_text", {
            "text_prompt": text_prompt,
            "bbox_condition": bbox_condition
        })
        
        # 直接返回blender-mcp的原始结果
        return result
        
    except Exception as e:
        return {"error": str(e), "success": False}

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
        # 直接获取所有引导线原始数据，让LLM分析匹配
        guides_data = blender_primitive.get_raw_guides_data()
        
        return f"✓ 查找引导线 '{guide_identifier}' 的信息：\n\n所有引导线原始数据：\n{guides_data}\n\n请从上述数据中找到匹配 '{guide_identifier}' 的引导线信息。"
        
    except Exception as e:
        return f"✗ 获取引导线信息时出错：{str(e)}"



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

# ========== 从 blender-mcp 导入的资产功能 ==========

# 添加必要的导入
import json
import os
import base64
from pathlib import Path
from urllib.parse import urlparse

def _process_bbox(bbox_condition):
    """处理bbox条件"""
    if bbox_condition is None:
        return None
    return bbox_condition

# ========== PolyHaven 资产功能 ==========

@mcp.tool()
def get_polyhaven_categories(ctx: Context, asset_type: str = "hdris") -> str:
    """
    获取PolyHaven资产分类列表
    
    Parameters:
    - asset_type: 资产类型 (hdris, textures, models, all)
    """
    try:
        primitive = BlenderPrimitive()
        result = primitive.send_command("get_polyhaven_categories", {"asset_type": asset_type})
        
        if "error" in str(result):
            return f"Error: {result}"
        
        return result
    except Exception as e:
        return f"Error getting PolyHaven categories: {str(e)}"

@mcp.tool()
def search_polyhaven_assets(
    ctx: Context,
    asset_type: str = "all",
    categories: str = None
) -> str:
    """
    在PolyHaven搜索资产
    
    Parameters:
    - asset_type: 资产类型 (hdris, textures, models, all)
    - categories: 可选的分类过滤，用逗号分隔
    
    Returns: 匹配资产的格式化列表
    """
    try:
        primitive = BlenderPrimitive()
        result = primitive.send_command("search_polyhaven_assets", {
            "asset_type": asset_type,
            "categories": categories
        })
        
        if "error" in str(result):
            return f"Error: {result}"
        
        return result
    except Exception as e:
        return f"Error searching PolyHaven assets: {str(e)}"

# download_polyhaven_asset 已移至内部函数 _download_polyhaven_asset_raw

@mcp.tool()
def get_polyhaven_status(ctx: Context) -> str:
    """
    检查PolyHaven集成状态
    """
    try:
        primitive = BlenderPrimitive()
        result = primitive.send_command("get_polyhaven_status")
        return str(result)
    except Exception as e:
        return f"Error checking PolyHaven status: {str(e)}"

# ========== Sketchfab 模型功能 ==========

@mcp.tool()
def search_sketchfab_models(
    ctx: Context,
    query: str,
    categories: str = None,
    count: int = 20,
    downloadable: bool = True
) -> str:
    """
    在Sketchfab搜索模型
    
    Parameters:
    - query: 搜索文本
    - categories: 可选分类过滤，用逗号分隔
    - count: 最大结果数量 (默认20)
    - downloadable: 是否只包含可下载模型 (默认True)
    
    Returns: 匹配模型的格式化列表
    """
    try:
        primitive = BlenderPrimitive()
        result = primitive.send_command("search_sketchfab_models", {
            "query": query,
            "categories": categories,
            "count": count,
            "downloadable": downloadable
        })
        
        if "error" in str(result):
            return f"Error: {result}"
        
        return result
    except Exception as e:
        return f"Error searching Sketchfab models: {str(e)}"

# download_sketchfab_model 已移至内部函数 _download_sketchfab_model_raw

@mcp.tool()
def get_sketchfab_status(ctx: Context) -> str:
    """
    检查Sketchfab集成状态
    """
    try:
        primitive = BlenderPrimitive()
        result = primitive.send_command("get_sketchfab_status")
        return str(result)
    except Exception as e:
        return f"Error checking Sketchfab status: {str(e)}"

# ========== Hyper3D AI生成功能 ==========

# generate_hyper3d_model_via_text 已移至内部函数 _generate_hyper3d_model_raw

@mcp.tool()
def get_hyper3d_status(ctx: Context) -> str:
    """
    检查Hyper3D集成状态
    """
    try:
        primitive = BlenderPrimitive()
        result = primitive.send_command("get_hyper3d_status")
        return str(result)
    except Exception as e:
        return f"Error checking Hyper3D status: {str(e)}"

# ========== 独立的变换工具 ==========

@mcp.tool()
def scale_object(ctx: Context, object_name: str, scale_factors: list) -> str:
    """
    将对象缩放到指定的绝对尺寸
    
    Parameters:
        object_name: 要缩放的对象名称
        scale_factors: 目标绝对尺寸 [x, y, z] (米) 或 [uniform_size] (等比缩放到该尺寸)
    
    Returns:
        str - 缩放结果报告，包含尺寸变化信息
    """
    try:
        # 检查对象是否存在
        obj_desc = blender_primitive.get_object_description(object_name)
        if "✗" in obj_desc:
            return f"✗ Object '{object_name}' not found in scene"
        
        # 处理等比缩放
        if len(scale_factors) == 1:
            scale_factors = [scale_factors[0], scale_factors[0], scale_factors[0]]
        elif len(scale_factors) != 3:
            return f"✗ scale_factors must be [x, y, z] or [uniform_scale]"
        
        # 执行缩放
        result = blender_primitive.scale_object(object_name, scale_factors)
        
        if "✗" in result:
            return f"✗ Failed to scale {object_name}: {result}"
        
        return f"✓ Successfully scaled {object_name} to [{scale_factors[0]:.2f}, {scale_factors[1]:.2f}, {scale_factors[2]:.2f}]"
        
    except Exception as e:
        return f"✗ Error scaling object: {str(e)}"


@mcp.tool()
def move_object(ctx: Context, object_name: str, position: list) -> str:
    """
    移动对象到指定位置
    
    Parameters:
        object_name: 要移动的对象名称
        position: 目标位置 [x, y, z]
    
    Returns:
        str - 移动结果报告
    """
    try:
        # 检查对象是否存在
        obj_desc = blender_primitive.get_object_description(object_name)
        if "✗" in obj_desc:
            return f"✗ Object '{object_name}' not found in scene"
        
        if len(position) != 3:
            return f"✗ position must be [x, y, z]"
        
        # 执行移动
        result = blender_primitive.move_object(object_name, position)
        
        if "✗" in result:
            return f"✗ Failed to move {object_name}: {result}"
        
        return f"✓ Successfully moved {object_name} to [{position[0]:.2f}, {position[1]:.2f}, {position[2]:.2f}]"
        
    except Exception as e:
        return f"✗ Error moving object: {str(e)}"


@mcp.tool()
def rotate_object(ctx: Context, object_name: str, rotation: list) -> str:
    """
    旋转对象到指定角度
    
    Parameters:
        object_name: 要旋转的对象名称
        rotation: 目标旋转角度 [x, y, z] (弧度)
    
    Returns:
        str - 旋转结果报告
    """
    try:
        # 检查对象是否存在
        obj_desc = blender_primitive.get_object_description(object_name)
        if "✗" in obj_desc:
            return f"✗ Object '{object_name}' not found in scene"
        
        if len(rotation) != 3:
            return f"✗ rotation must be [x, y, z] in radians"
        
        # 执行旋转
        result = blender_primitive.rotate_object(object_name, rotation)
        
        if "✗" in result:
            return f"✗ Failed to rotate {object_name}: {result}"
        
        # 转换为度数显示
        degrees = [r * 180 / 3.14159 for r in rotation]
        return f"✓ Successfully rotated {object_name} to [{degrees[0]:.1f}°, {degrees[1]:.1f}°, {degrees[2]:.1f}°]"
        
    except Exception as e:
        return f"✗ Error rotating object: {str(e)}"


@mcp.tool()
def debug_scene_objects(ctx: Context) -> str:
    """
    调试工具：检查当前场景中的所有对象
    
    Returns:
        str - 场景中所有对象的详细信息
    """
    try:
        # 获取原始场景数据
        scene_data = blender_primitive.get_raw_scene_data()
        
        if isinstance(scene_data, dict):
            objects_info = []
            if 'objects' in scene_data:
                for obj in scene_data['objects']:
                    obj_info = f"- {obj.get('name', 'Unknown')}: 位置{obj.get('location', 'N/A')}, 尺寸{obj.get('dimensions', 'N/A')}"
                    objects_info.append(obj_info)
            
            total_objects = len(scene_data.get('objects', []))
            
            return f"""✓ 场景调试信息:
总对象数: {total_objects}

对象列表:
{chr(10).join(objects_info) if objects_info else '无对象'}

原始数据:
{scene_data}
"""
        else:
            return f"✗ 无法获取场景数据: {scene_data}"
        
    except Exception as e:
        return f"✗ 调试场景时出错: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport='stdio') 