"""This module contains a Domain-Specific Language (DSL) designed 
with built-in support for loops and functions for shape construction and transformation.
"""

from typing import NamedTuple, Any, Callable, Literal
import math
import numpy as np

# type aliases and DSL syntax sugar
P = Any  # 3D vector, e.g., a point or direction
T = Any  # transform parameters in the corresponding [X Y Z], control the position of objecty
R = Any  # rotation parameters in the corresponding [X Y Z] , the mode is ' X Y Z Euler ' in Blender
S = Any  # scale parameters in the corresponding [X Y Z], control the size of objecty
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
            the primitive_name suppose to be search and import a shape from 'Poly Haven'
        ...: Any - additional arguments that help for the primitive shape search in 'Poly Haven'
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
def transform_shape(shape: Shape, T: T, R:R, S:S) -> Shape:
    """
    Args:
        shape: Shape
        transform parameters: T - help to place the object.
        rotation parameters: T - help to rotate the object.
        scale parameters: T - help to scale the object.

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
