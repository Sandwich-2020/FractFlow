import os
import re
from typing import Optional

from bpyrenderer.camera import add_camera
from bpyrenderer.engine import init_render_engine
from bpyrenderer.environment import set_background_color, set_env_map
from bpyrenderer.importer import load_file, load_armature
from bpyrenderer.render_output import (
    enable_color_output,
    enable_albedo_output,
    enable_depth_output,
    enable_normals_output,
)
from bpyrenderer import SceneManager
from bpyrenderer.camera.layout import get_camera_positions_on_sphere
from bpyrenderer.utils import convert_normal_to_webp

def render_mesh(mesh_path: str, save_path: Optional[str] = None) -> str:
    '''
    Render 3D mesh from multiple viewpoints and save images using bpy-renderer.
    
    Args:
        mesh_path (str): Path to the 3D mesh file (obj, ply, glb, etc.)
        save_path (str, optional): Directory path where rendered images will be saved.
                                  If None, will create a directory based on mesh filename.
        
    Returns:
        str: Success message with information about rendered images
    '''
    
    # Auto-generate save path if not provided
    if save_path is None:
        mesh_name = os.path.splitext(os.path.basename(mesh_path))[0]
        save_path = os.path.join(os.path.dirname(mesh_path), f"{mesh_name}_renders")
    
    # Ensure output directory exists
    os.makedirs(save_path, exist_ok=True)
    
    # 1. Init engine and scene manager
    init_render_engine("CYCLES")
    scene_manager = SceneManager()
    scene_manager.clear(reset_keyframes=True)

    # 2. Import models
    load_file(mesh_path)

    # Others. smooth objects and normalize scene
    # scene_manager.smooth()
    scene_manager.clear_normal_map()
    scene_manager.set_material_transparency(False)
    scene_manager.set_materials_opaque()  # !!! Important for render normal but may cause render error !!!
    scene_manager.normalize_scene(1.0)

    # 3. Set environment
    set_env_map("/hpc2hdd/home/msheng758/projects/bpy-renderer/assets/env_textures/brown_photostudio_02_1k.exr")
    # set_background_color([1.0, 1.0, 1.0, 1.0])

    # 4. Prepare cameras
    cam_pos, cam_mats, elevations, azimuths = get_camera_positions_on_sphere(
        center=(0, 0, 0),
        radius=1.5,
        elevations=[30],
        azimuths=[item - 90 for item in [0, 45, 90, 180, 270, 315]],  # forward issue
    )
    cameras = []
    for i, camera_mat in enumerate(cam_mats):
        camera = add_camera(camera_mat, "ORTHO", add_frame=i < len(cam_mats) - 1)
        cameras.append(camera)
        print(f"Added camera {i+1}/{len(cam_mats)}")

    # 5. Set render outputs
    width, height = 1024, 1024
    enable_color_output(
        width,
        height,
        save_path,
        file_format="PNG",
        mode="IMAGE",
        film_transparent=True,
    )
    
    # 6. Render
    print(f"Rendering {len(cameras)} views...")
    scene_manager.render()
    
    return f"Successfully rendered {len(cameras)} images from mesh {mesh_path} to directory {save_path}"

def detect_3d_files(text: str) -> list:
    """
    Detect 3D file paths in text based on file extensions.
    
    Args:
        text (str): Input text to search for 3D file paths
        
    Returns:
        list: List of detected 3D file paths
    """
    print(f"Detecting 3D files in text: {text}")
    # 3D file extensions to detect
    extensions = ['.obj', '.glb', '.gltf', '.fbx', '.dae', '.ply', '.stl', '.blend', '.3ds', '.x3d']
    
    # Multiple patterns to match different file path formats
    patterns = [
        # Pattern 1: Full paths starting with / (Unix/Linux absolute paths)
        r'/[^\s]*?(?:' + '|'.join(re.escape(ext) for ext in extensions) + r')(?=\s|$)',
        # Pattern 2: Relative paths or Windows paths
        r'[a-zA-Z]:[^\s]*?(?:' + '|'.join(re.escape(ext) for ext in extensions) + r')(?=\s|$)',
        # Pattern 3: Relative paths starting with ./ or ../
        r'\.\.?/[^\s]*?(?:' + '|'.join(re.escape(ext) for ext in extensions) + r')(?=\s|$)',
        # Pattern 4: Simple filenames with extensions
        r'\b[^\s/\\]*?(?:' + '|'.join(re.escape(ext) for ext in extensions) + r')(?=\s|$)',
        # Pattern 5: Any sequence ending with 3D extensions (fallback)
        r'\S*?(?:' + '|'.join(re.escape(ext) for ext in extensions) + r')(?=\s|$)'
    ]
    
    all_matches = []
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.IGNORECASE)
        print(f"Pattern {i+1} found: {matches}")
        all_matches.extend(matches)
    
    # Remove duplicates while preserving order
    unique_matches = []
    for match in all_matches:
        if match not in unique_matches:
            unique_matches.append(match)
    
    print(f"All unique matches: {unique_matches}")
    
    # Filter to only return existing files
    existing_files = []
    for match in unique_matches:
        print(f"Checking if file exists: {match}")
        if os.path.exists(match):
            existing_files.append(match)
            print(f"✓ File exists: {match}")
        else:
            print(f"✗ File not found: {match}")
    
    print(f"Final existing files: {existing_files}")
    return existing_files

if __name__ == "__main__":
    # Test the render function
    import sys
    if len(sys.argv) > 1:
        mesh_path = sys.argv[1]
        save_path = sys.argv[2] if len(sys.argv) > 2 else None
        result = render_mesh(mesh_path, save_path)
        print(result)


