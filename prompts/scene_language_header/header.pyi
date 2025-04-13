"""This module contains a Domain-Specific Language (DSL) designed 
with built-in support for loops and functions for shape construction and transformation.
"""

from typing import NamedTuple, Any, Callable, Literal
import math
import numpy as np

# type aliases and DSL syntax sugar
P = Any  # 3D vector, e.g., a point or direction
T = Any  # 4x4 transformation matrix
Shape = list[dict[str, Any]]  # a shape is a list of primitive shapes

# shape function library utils

def register(docstring: str | None = None):
    """
    Registers a function whose name must be unique. You can pass in a docstring (optional).

    Every function you register MUST be invoked via `library_call`, and cannot be invoked directly via the function name.
    """
def library_call(func_name: str, **kwargs) -> Shape:
    """
    Call a function from the library and return its outputs. You are responsible for registering the function with `register`.

    Args:
        func_name (str): Function name.
        **kwargs: Keyword arguments passed to the function.
    """


def primitive_call(primitive_name: str, **kwargs) -> Shape:
    """
    Args:
        primitive_name: str - the description of each primitive
            the primitive_name suppose to be generate by few code in the blender using python library 'bpy'
        ...: Any - additional arguments that help for the primitive shape definition in bpy
            For example:
                if you call 'cube' the Any should be:
                    - size (float in [0, inf], (optional)): Size

                    - calc_uvs (boolean, (optional)): Generate UVs, Generate a default UV map

                    - enter_editmode (boolean, (optional)): Enter Edit Mode, Enter edit mode when adding this object

                    - align (enum in ['WORLD', 'VIEW', 'CURSOR'], (optional)):

                        Align, The alignment of the new object

                        WORLD World: Align the new object to the world.

                        VIEW View: Align the new object to the view.

                        CURSOR 3D Cursor: Use the 3D cursor orientation for the new object.

                    - location (mathutils.Vector of 3 items in [-inf, inf], (optional)): Location, Location for the newly added object

                    - rotation (mathutils.Euler rotation of 3 items in [-inf, inf], (optional)): Rotation, Rotation for the newly added object

                    - scale (mathutils.Vector of 3 items in [-inf, inf], (optional)): Scale, Scale for the newly added object
    Returns:
        Shape - a basic primitive shape that can be compose to more complex shape.
    """

# control flows

def loop(n: int, fn: Callable[[int], Shape]) -> Shape:
    """
    Simple loop executing a function `n` times and concatenating the results.

    Args:
        n (int): Number of iterations.
        fn (Callable[[int], Shape]): Function that takes the current iteration index returns a shape.

    Returns:
        Concatenated shapes from each iteration.
    """

# shape manipulation

def concat_shapes(*shapes: Shape) -> Shape:
    """
    Combines multiple shapes into a single shape.
    """
def transform_shape(shape: Shape, pose: T) -> Shape:
    """
    Args:
        shape: Shape
        pose: T - If pose is A @ B, then B is applied first, followed by A.

    Returns:
        The input shape transformed by the given pose.
    """

# pose transformation

def translation_matrix(offset: P) -> T:
    """
    Args:
        offset (P) : the translation vector, which must be composed of integers
    """
def identity_matrix() -> T:
    """
    Returns the identity matrix in SE(3).
    """
