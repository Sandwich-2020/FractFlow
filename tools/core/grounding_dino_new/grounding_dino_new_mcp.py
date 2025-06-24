import os
import asyncio
from typing import Any, Optional, List
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
from urllib.parse import urlparse
import json
from PIL import Image

from dds_cloudapi_sdk import Config, Client
from dds_cloudapi_sdk.tasks.v2_task import V2Task, create_task_with_local_image_auto_resize
from dds_cloudapi_sdk.visualization_util import visualize_result


# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("grounding_dino_new")

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

@mcp.tool()
async def detect_objects_with_grounding_dino(
    image_path: str,
    query: str,
    box_threshold: float = 0.35,
    text_threshold: float = 0.25,
    show_visualisation: bool = True,
    save_directory: str = ""
) -> str:
    """
    Detect objects in an image using Grounding DINO model with text queries.
    
    This tool uses the adirik/grounding-dino model on Replicate to detect and locate
    objects in images based on natural language descriptions. It can detect arbitrary
    objects described in text format.
    
    Args:
        image_path (str): Path to the input image file
        query (str): Comma-separated text descriptions of objects to detect (e.g., "person, car, dog")
        box_threshold (float): Confidence level for object detection (default: 0.35)
        text_threshold (float): Confidence level for text matching (default: 0.25)
        show_visualisation (bool): Whether to generate and save annotated image with bounding boxes (default: True)
        save_directory (str): Directory where output files will be saved (optional)
    
    Returns:
        str: Detection results with bounding boxes, confidence scores, and file paths
    """
    try:
        # Normalize image path
        image_path = normalize_path(image_path)
        
        # Validate image file exists
        if not os.path.exists(image_path):
            return f"Error: Image file not found at {image_path}"
        
        # Auto-generate save directory if not provided
        if not save_directory.strip():
            image_dir = os.path.dirname(image_path)
            image_name = os.path.splitext(os.path.basename(image_path))[0]
            save_directory = os.path.join(image_dir, f"{image_name}_GROUNDING_DINO_RESULTS")
        else:
            save_directory = normalize_path(save_directory)
        
        # Ensure save directory exists
        os.makedirs(save_directory, exist_ok=True)
        
        # Initialize Replicate client
        config = Config(os.getenv("DINO_X_KEY"))
        client = Client(config) 
        
        api_path = "/v2/task/dinox/detection"
        query = ".".join([s.strip() for s in query.split(",") if s.strip()])

        api_body = {
        "model": "DINO-X-1.0",          # 默认最新公开检测模型
        "prompt": {"type": "text", "text": query},
        "targets": ["bbox"],
        "bbox_threshold": round(box_threshold, 4),
        # iou_threshold 可留空使用服务器默认
        }

        task = create_task_with_local_image_auto_resize(
            api_path=api_path,
            api_body_without_image=api_body,
            image_path=image_path,
        )

        # Run the Grounding DINO model
        client.run_task(task)

        result = task.result or {}
        objects = result.get("objects", []) 
        
        # Prepare serializable results
        
        
        # Save detection results to JSON file
        results_file = os.path.join(save_directory, "detection_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Download annotated image if visualization is enabled
        annotated_image_path = None
        if show_visualisation and objects:
            annotated_image_path = os.path.join(save_directory, "annotated_image.png")
            # visualize_result 会自动画框 / 标签
            visualize_result(
            image_path=image_path,
            result=result,
            output_dir=save_directory,      # 会保存在该目录
            )
        
        output_txt = [f"Object Detection Results (DINO-X) for: '{query}'",
                  f"Total objects detected: {len(objects)}", ""]

        for idx, obj in enumerate(objects, 1):
            x1, y1, x2, y2 = obj["bbox"]
            label = obj.get("category", "unknown")
            conf  = obj.get("score", 0.0)
            output_txt.append(
                f"{idx}. {label}\n"
                f"   Confidence: {conf:.3f}\n"
                f"   BBox: [x1={x1:.1f}, y1={y1:.1f}, x2={x2:.1f}, y2={y2:.1f}]"
            )

        if not objects:
            output_txt.append("No objects matched the query.")

        output_txt.extend([
            "",
            f"Files saved in → {save_directory}",
            f"- JSON results : {results_file}",
        ])
        if annotated_image_path:
            output_txt.append(f"- Annotated PNG : {annotated_image_path}")

        return "\n".join(output_txt)

    except Exception as e:
        return json.dumps({
        "error": f"Error during detection and cropping: {str(e)}",
        "cropped_images": []
        })


@mcp.tool()
async def detect_and_crop_objects(
    image_path: str,
    query: str,
    box_threshold: float = 0.35,
    text_threshold: float = 0.25,
    save_directory: str = "",
    padding: int = 10
) -> str:
    """
    Detect objects in an image and crop them out as separate images.
    
    This tool first detects objects using Grounding DINO, then crops each detected 
    object from the original image and saves them as individual files.
    
    Args:
        image_path (str): Path to the input image file
        query (str): Comma-separated text descriptions of objects to detect
        box_threshold (float): Confidence level for object detection (default: 0.35)
        text_threshold (float): Confidence level for text matching (default: 0.25)
        save_directory (str): Directory where cropped images will be saved (optional)
        padding (int): Extra pixels to add around each crop (default: 10)
    
    Returns:
        str: JSON string containing detection results and list of cropped image paths
    """
    try:
        # Normalize image path
        image_path = normalize_path(image_path)
        
        # Validate image file exists
        if not os.path.exists(image_path):
            return json.dumps({
                "error": f"Image file not found at {image_path}",
                "cropped_images": []
            })
        
        # Auto-generate save directory if not provided
        if not save_directory.strip():
            image_dir = os.path.dirname(image_path)
            image_name = os.path.splitext(os.path.basename(image_path))[0]
            save_directory = os.path.join(image_dir, f"{image_name}_CROPPED_OBJECTS")
        else:
            save_directory = normalize_path(save_directory)
        
        # Ensure save directory exists
        os.makedirs(save_directory, exist_ok=True)
        
        # Initialize Replicate client
        config = Config(os.getenv("DINO_X_KEY"))
        client = Client(config) 
        
        # Run the Grounding DINO model
        api_path = "/v2/task/dinox/detection"
        prompt_text = ".".join([p.strip() for p in query.split(",") if p.strip()])

        task = create_task_with_local_image_auto_resize(
            api_path=api_path,
            api_body_without_image={
                "model": "DINO-X-1.0",
                "prompt": {"type": "text", "text": prompt_text},
                "targets": ["bbox"],
                "bbox_threshold": round(box_threshold, 4)
            },
            image_path=image_path
        )
        client.run_task(task)
        
        # Get detections
        objects = task.result.get("objects", [])
        
        if not objects:
            return json.dumps({
                "message": "No objects detected matching the query",
                "query": query,
                "total_detections": 0,
                "cropped_images": []
            })
        
        # Open the original image for cropping
        original_image = Image.open(image_path)
        image_width, image_height = original_image.size
        
        cropped_image_paths = []
        detection_results = []
        
        # Process each detection
        for idx, obj in enumerate(objects, 1):
            x1, y1, x2, y2 = map(int, obj["bbox"])
            x1, y1 = max(0, x1 - padding), max(0, y1 - padding)
            x2, y2 = min(image_width, x2 + padding), min(image_height, y2 + padding)
            
            # Crop the object
            cropped_image = original_image.crop((x1, y1, x2, y2))
            
            # Generate filename for cropped image
            safe_label = obj["category"].replace(" ", "_").replace("/", "_")
            crop_filename = f"{safe_label}_{idx}_conf{obj['score']:.2f}.png"
            crop_path = os.path.join(save_directory, crop_filename)
            
            # Save cropped image
            cropped_image.save(crop_path)
            cropped_image_paths.append(crop_path)
            
            # Add detection info
            detection_results.append({
                "index": idx,
                "label": obj["category"],
                "confidence": obj["score"],
                "bbox": obj["bbox"],
                "cropped_image_path": crop_path,
                "crop_size": [x2 - x1, y2 - y1]
            })
        
        # Save detection results with cropped paths
        results_file = os.path.join(save_directory, "detection_and_crop_results.json")
        full_results = {
            "query": query,
            "total_detections": len(objects),
            "detections": detection_results,
            "cropped_images": cropped_image_paths,
            "save_directory": save_directory,
            "original_image": image_path
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(full_results, f, indent=2, ensure_ascii=False)
        
        # Return summary as JSON string
        return json.dumps({
            "message": f"Successfully detected and cropped {len(objects)} objects",
            "query": query,
            "total_detections": len(objects),
            "cropped_images": cropped_image_paths,
            "detections": detection_results,
            "save_directory": save_directory,
            "results_file": results_file
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Error during detection and cropping: {str(e)}",
            "cropped_images": []
        })

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 