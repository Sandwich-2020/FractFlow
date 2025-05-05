from typing import List, Union, Optional
import logging


# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("prompter")



def read_header() -> str:
    # files = sorted((root / 'outputs' / 'stubgen').iterdir(), key=os.path.getmtime)[-1]
    header_file = "prompts/scene_language_header_ph/header.pyi"
    print(header_file)
    with open(header_file, "r") as f:
        s = f.read()
    return s


def read_example() -> str:
    # files = sorted((root / 'outputs' / 'stubgen').iterdir(), key=os.path.getmtime)[-1]
    example_file = "prompts/scene_language_example/blender_scene_polyheavn.py"
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


SYSTEM_RULES = f"""STRICTLY follow these rules:
1. Only use the functions and imported libraries in `helper.py`.
2. You can only write functions. Follow a modular approach and use the `register` decorator to define semantic shapes or shape groups. Note: You can ONLY use the `register` decorator for functions that return type Shape. Any helper functions that you attempt to register will cause an error.
3. The Camera coordinate system: +x is right, +z is up, -y is forward.
4. Pay attention that the objects are not too large so it can't be rendered.
5. **IMPORTANT** During the coding process, use different 'library_call' functions as much as possible to construct complex shapes, and make sure to include clear shape names and comments. Only use 'primitive_call' to build basic shapes when they can be created using Blender's built-in simple geometry.
"""

SYSTEM_PROMPT = """\
You are a code completion model and can only write python functions wrapped within ```python```.

You are provided with the following `helper.py` which defines the given functions and definitions:
```python
{header}
```

{rules}

You should be precise and creative.
""".format(
    header=SYSTEM_HEADER, rules=SYSTEM_RULES
)

def get_user_prompt(task: str):

    return '''Here are some examples of how to use `helper.py`:
    ```python
    {example}
    ```
    IMPORTANT: THE FUNCTIONS ABOVE ARE JUST EXAMPLES, YOU CANNOT USE THEM IN YOUR PROGRAM! 

    Now, write a similar program for the given task:    
    ```python
    from helper import *

    """
    {task}
    """
    ```
    '''.format(
            task=task,
            example=read_example(),
        )


if __name__ == "__main__":
    # Initialize and run the server
    print(get_user_prompt("a beautiful room"))