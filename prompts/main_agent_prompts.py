from typing import List, Union, Optional
import logging


# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("prompter")


def read_header() -> str:
    # files = sorted((root / 'outputs' / 'stubgen').iterdir(), key=os.path.getmtime)[-1]
    header_file = "prompts/scene_language_header/header.pyi"
    print(header_file)
    with open(header_file, "r") as f:
        s = f.read()
    return s


def read_example() -> str:
    # files = sorted((root / 'outputs' / 'stubgen').iterdir(), key=os.path.getmtime)[-1]
    example_file = "prompts/scene_language_example/blender_scene.py"
    print(example_file)
    with open(example_file, "r") as f:
        s = f.read()
    return s


SYSTEM_HEADER = read_header()



# TODO unify rule 2
# SYSTEM_RULES = f"""STRICTLY follow these rules:
# 1. Only use the functions and imported libraries in `helper.py`.
# 2. You can only write functions. Follow a modular approach and use the `register` decorator to define semantic shapes or shape groups. Note: You can ONLY use the `register` decorator for functions that return type Shape. Any helper functions that you attempt to register will cause an error.
# 3. Camera coordinate system: +x is right, +y is up, +z is forward. 
# 4. Pay attention that the objects are not too large so it can't be rendered.
# 5. Use `compute_shape_*` from `helper.py` if possible to compute transformations.  
# 6. Make sure that only use `primitive_call` in the shape that can be represent in simple primitive that you can call the functions under `bpy.ops.mesh` to generate it.
# """

TOOL_PROMPTS = """
        When tools are needed, include a JSON-formatted tool call anywhere in your response. You can use code blocks or inline JSON. The tool call should include the tool name and required arguments.

        Common formats include:
        ```json
        {"tool_call": {"name": "tool_name", "arguments": {"param1": "value1"}}}
        ```

        For multiple tool calls, you can use:
        ```json
        {"tool_calls": [{"name": "tool1", "arguments": {...}}, {"name": "tool2", "arguments": {...}}]}
        ```

        Or any equivalent format as long as it contains the required name and arguments fields.

        If no tools are needed, simply provide a direct answer or explanation.

        Remember: Only use tools when specific information is truly needed. If you can answer directly, do so."""

#1. When the user requests you to generate a scene, always query the 'Scene_Planner' tool to obtain a coarse pseudo-code representing the scene as a *suggestion*. Then, follow this *suggestion* to generate the scene incrementally, starting from primitive elements and progressing to complex scenes STEP BY STEP.
SYSTEM_RULES = f"""STRICTLY follow these rules:
1. Camera coordinate system: +x is right, +z is up, -y is forward. 
2. all the [Action] relate to generate/import an object, trying to generate a mesh from poly haven.
2. Other [Action] should use "execute_blender_code" tool to achieve by writing 'bpy' codes.
3. all the [Observation] should use "get_scene_info" tool to check actions, also, check the 'bounding box' of each object in the scene and check if 1. there is an intersection of each object. 2. is the size of the object reasonable.
4. [Decision] should specifically check if the spatial relation is right.
5. don't add light, add camera, just trying to design the scene by given prompt.
6. If you want to generate a mesh from poly haven, you should 1. using 'get_polyhaven_categories' to get the categories and modified the requirement to search objects within the categories. 2. using 'search_polyhaven_assets' to search the assets that correspond to your requirement, and them use "download_polyhaven_asset" to get them.
"""

SYSTEM_PROMPT = """\
You are a professonal scene generate model using BLENDER, you are familiar to the blender using. You can ask and help user about using BLENDER, remember the if the user ask you for generate something, always following:
[Planining] ([Reasoning] [Action] [Observation] [Reasoning] [Decision])*N to achieve it.
[Planining] : plan how to generate a complex model with iteratively introduce different basic objects from poly haven and divide it to several steps。
( IN EACH STEP:
    [Reasoning] : think about how to conduct this step
    [Action] : call tool_call to achieve it
    [Observation] : use tool to observe the current state of the scene.
    [Reasoning] : is current state fit the requirement in 1. spatial relation. 2. shape correspondance
    [Decision] : if it is good, moving forward, if not, delete the thing you generate in this STEP and re generate it.
)

{rules}

You are provided with several tools to complete your work:

{tool}


You should be precise and creative.
""".format(
    tool=TOOL_PROMPTS, rules=SYSTEM_RULES
)



if __name__ == "__main__":
    # Initialize and run the server
    print(SYSTEM_PROMPT)