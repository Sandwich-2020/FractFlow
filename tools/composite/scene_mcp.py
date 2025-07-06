
import os
import mimetypes
import base64
import json
import numpy as np
import trimesh
from PIL import Image
import replicate
from gradio_client import Client, handle_file
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置 Replicate API token
if os.getenv('REPLICATE_API_TOKEN'):
    replicate.api_token = os.getenv('REPLICATE_API_TOKEN')

HUNYUAN_API_BASE = "http://10.30.58.120:7103/"
USER_AGENT = "3d_generation_mcp_tool"
TEMP_DIR = "/hpc2hdd/home/msheng758/projects/FractFlow/tmp"
THICKNESS = 0.1

def process_text_to_image(input_text, id):
    input = {
        "prompt": input_text,
        "guidance": 3.5
    }
    output = replicate.run(
        "black-forest-labs/flux-dev",
        input=input
    )
    item = output[0]
    file_name = os.path.join(TEMP_DIR, f"{id}.webp")
    with open(file_name, "wb") as file:
        file.write(item.read())
    
    return file_name

def process_image_to_3d(input_image, client):
    result = client.predict(
        input_image=handle_file(input_image),
        api_name="/process_image_to_3d"
    )

    return result[0]

def process_image_sr(input_image, id):
    mime_type, _ = mimetypes.guess_type(input_image)
    with open(input_image, "rb") as image_file:
        base64_data = base64.b64encode(image_file.read()).decode('utf-8')
    input_uri = f"data:{mime_type};base64,{base64_data}"
    input = {
        "image": input_uri
    }
    output = replicate.run(
        "xinntao/esrgan:c263265e04b16fda1046d1828997fc27b46610647a3348df1c72fbffbdbac912",
        input=input
    )
    file_name = os.path.join(TEMP_DIR, f"{id}_sr.webp")
    with open(file_name, "wb") as file:
        file.write(output.read())
    
    return file_name

def process_image_editing(input_image, prompt, id):
    mime_type, _ = mimetypes.guess_type(input_image)
    with open(input_image, "rb") as image_file:
        base64_data = base64.b64encode(image_file.read()).decode('utf-8')
    input_uri = f"data:{mime_type};base64,{base64_data}"
    input = {
        "prompt": "this is " + prompt + ", " + "Change the view into front-view and remove the background",
        "input_image": input_uri,
        "output_format": "webp",
        "num_inference_steps": 30
    }

    output = replicate.run(
        "black-forest-labs/flux-kontext-dev",
        input=input
    )
    file_name = os.path.join(TEMP_DIR, f"{id}_kontext.webp")
    with open(file_name, "wb") as file:
        file.write(output.read())
    
    return file_name

def process_rem_bg(input_image, id):
    mime_type, _ = mimetypes.guess_type(input_image)
    with open(input_image, "rb") as image_file:
        base64_data = base64.b64encode(image_file.read()).decode('utf-8')
    input_uri = f"data:{mime_type};base64,{base64_data}"
    input = {
        "image": input_uri
    }

    output = replicate.run(
        "851-labs/background-remover:a029dff38972b5fda4ec5d75d7d1cd25aeff621d2cf4946a41055d7db66b80bc",
        input=input
    )
    file_name = os.path.join(TEMP_DIR, f"{id}_rb.webp")
    with open(file_name, "wb") as file:
        file.write(output.read())
    
    return file_name
    
def align_orientation_by_size(expected_size, actual_size, state):
    if actual_size[2] / min(actual_size[0], actual_size[1]) < 0.05 and \
       expected_size[1] / min(expected_size[0], expected_size[2]) < 0.05:
        if state == "[Floor]":
            return trimesh.transformations.rotation_matrix(
                angle=-np.pi / 2, 
                direction=[1, 0, 0]
            )
        elif state == "[Hanging]":
            return trimesh.transformations.rotation_matrix(
                angle=np.pi / 2, 
                direction=[1, 0, 0]
            )
    if expected_size[0] > expected_size[2] and actual_size[0] < actual_size[2]:
        return trimesh.transformations.rotation_matrix(
            angle=np.pi / 2, 
            direction=[0, 1, 0]
        )
    elif expected_size[0] < expected_size[2] and actual_size[0] > actual_size[2]:
        return trimesh.transformations.rotation_matrix(
            angle=-np.pi / 2, 
            direction=[0, 1, 0]
        )

    return trimesh.transformations.rotation_matrix(
        angle=0, 
        direction=[1, 0, 0]
    )

def normalize_to_unit_bbox(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    bbox = mesh.bounding_box.bounds
    min_corner, max_corner = bbox
    center = (min_corner + max_corner) / 2
    extents = max_corner - min_corner
    scale_factors = 1.0 / extents

    mesh.apply_translation(-center)
    mesh.apply_scale(scale_factors)

    return mesh, scale_factors

def apply_transform_from_properties(
        mesh: trimesh.Trimesh, 
        position: dict, 
        size: dict, 
        rotation: dict
    ) -> trimesh.Trimesh:
    
    S = np.eye(4)
    S[0, 0] = size["width"]
    S[1, 1] = size["height"]
    S[2, 2] = size["length"]

    yaw_rad = np.radians(rotation["yaw"])
    R = trimesh.transformations.rotation_matrix(angle=yaw_rad, direction=[0, 1, 0])

    T = trimesh.transformations.translation_matrix([
        position["x"],
        position["z"] + size["height"] / 2,
        position["y"]
    ])

    M = T @ R @ S

    mesh.apply_transform(M)

    return mesh

def create_wall_mesh(start, end, height, image_file):
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

def create_scene(layout_json):
    client = Client(HUNYUAN_API_BASE, download_files = TEMP_DIR)
    
    with open(layout_json, 'r') as f:
        layout = json.load(f)

    meshes = []

    for object in layout["layout"]:
        id = object["id"]
        state = object["description"].split(" ")[0]
        desciption = object["description"].split(" ", 1)[-1]
    
        if "image_reference" in object and  object["image_reference"] is not None and object["image_reference"] != "":
            image_reference = object["image_reference"]
            image = Image.open(image_reference)
            if image.size[0] < 512 or image.size[1] < 512:
                image_reference = process_image_sr(image_reference, id)
            image_reference = process_image_editing(image_reference, desciption, id)
            image_reference = process_rem_bg(image_reference, id)
        else:
            desciption = desciption + ", pure white background"
            image_reference = process_text_to_image(desciption, id)
        
        mesh_file = process_image_to_3d(image_reference, client)
        mesh = trimesh.load(mesh_file)
        mesh, scale_factors = normalize_to_unit_bbox(mesh)

        size = np.array([object["size"]["width"], object["size"]["height"], object["size"]["length"]])
        rot = align_orientation_by_size(size, 1/scale_factors, state)
        mesh.apply_transform(rot)
        
        if state == "[Tabletop]":
            pass
        elif state == "[Hanging]":
            pass
        elif state == "[Floor]":
            object["position"]["z"] = 0
        mesh = apply_transform_from_properties(
            mesh,
            position=object["position"],
            size=object["size"],
            rotation=object["rotation"]
        )

        meshes.append(mesh)
    
    wall_rot = {}
    for wall in layout["room"]["walls"]:
        id = wall["id"]
        
        description = wall["description"]
        image_reference = process_text_to_image(description, id)
        wall_mesh = create_wall_mesh(
            start=wall["start"],
            end=wall["end"],
            height=wall["height"],
            image_file=image_reference,
        )
        wall_mesh.export(f"{id}.glb")
        meshes.append(wall_mesh)

        rotation = np.atan2(wall['end']['y'] - wall['start']['y'],
                            wall['end']['x'] - wall['start']['x'])
        wall_rot[id] = {'yaw': np.degrees(rotation)}
    
    for door in layout["room"]["doors"]:
        desciption = door["description"].split(" ", 1)[-1]
        desciption = desciption + ", pure white background"
        image_reference = process_text_to_image(desciption, id)
        
        mesh_file = process_image_to_3d(image_reference, client)
        mesh = trimesh.load(mesh_file)
        mesh, _ = normalize_to_unit_bbox(mesh)

        door["size"]["length"] = door["size"]["width"]
        door["size"]["width"] = THICKNESS
        door["position"]["z"] = 0
        mesh = apply_transform_from_properties(
            mesh,
            position=door["position"],
            size=door["size"],
            rotation=wall_rot[door['wall_id']]
        )

        meshes.append(mesh)

    for window in layout["room"]["windows"]:
        desciption = window["description"].split(" ", 1)[-1]
        desciption = desciption + ", pure white background"
        image_reference = process_text_to_image(desciption, id)
        
        mesh_file = process_image_to_3d(image_reference, client)
        mesh = trimesh.load(mesh_file)
        mesh, _ = normalize_to_unit_bbox(mesh)

        window["size"]["length"] = window["size"]["width"]
        window["size"]["width"] = THICKNESS
        mesh = apply_transform_from_properties(
            mesh,
            position=window["position"],
            size=window["size"],
            rotation=wall_rot[window['wall_id']]
        )

        meshes.append(mesh)

    scene = trimesh.Scene(meshes)
    return scene

if __name__ == "__main__":
    json_file = "/hpc2hdd/home/msheng758/projects/FractFlow/sporty_boy_bedroom_design_1.json"
    scene = create_scene(json_file)
    scene.export(os.path.basename(json_file).replace(".json", ".glb"))