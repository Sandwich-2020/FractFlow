from helper import *

"""
A vintage style study room.
"""



@register()
def chair() -> Shape:
    # import single primitive (chair) from poly haven, take care of the scale should be homo with scene
    return primitive_call(
        "chair",
        description="a  vintage style chair",
        scale = [0.5,0.5,0.5]
    )

@register()
def table() -> Shape:
    # import single primitive (table) from poly haven, take care of the scale should be homo with scene
    return primitive_call(
        "table",
        description="a vintage style table",
        scale = [1.,1.,1.]
    )


@register()
def cabinet() -> Shape:
    # import single primitive (cabinet) from poly haven, take care of the scale should be homo with scene
    return primitive_call(
        "lamp",
        description="a vintage style lamp",
        scale = [1.,1.,1.]
    )


@register()
def lamp() -> Shape:
    # import single primitive (lamp) from poly haven, take care of the scale should be homo with scene
    return primitive_call(
        "lamp",
        description="a vintage style lamp",
        scale = [1.,1.,1.]
    )

@register()
def book() -> Shape:
    # import single primitive (lamp) from poly haven, take care of the scale should be homo with scene
    return primitive_call(
        "book",
        description="a book",
        scale = [1.,1.,1.]
    )

"""
A set of books stack in the cabinet.
"""

@register()
def book_sets(book_num: int = 3) -> Shape:
    # a book sets contains of 4 books and stack together in the Z axis

    return loop(
        4,
        lambda i: loop(
            4,
            lambda j: transform_shape(
                library_call(
                    "book"
                ),  # Make it random to give the appearance of having varying heights
                T = (0, 0, i*0.1), # make the book stack together （0.1 is the thickness of book ）
                R = (0, 90, 0), # lay the book down
                S = (1,1,1),                
                ),
        ),
    )

@register()
def cabinet_with_books() -> Shape:
    # a cabinet that stack book
    return concat_shapes(
        transform_shape(
        library_call(
            "cabinet"
        ),
        T = (1.5, 0, 0), 
        R = (0, 0, 270), # face to the chair and table
        S = (0.7,0.7,0.7),
        ),  # 
        transform_shape(
        library_call("book_sets"),
        T = (1.5, 0, 0.98), # place in the cabinet
        R = (0, 0, 0),
        S = (0.5,0.5,0.5),)        
         # 
    )  # hint: these library calls must be implemented to be compatible with the usage

"""
A Table with lamp.
"""


@register()
def table_with_lamp() -> Shape:
    # A table with a lamp on it 
    return concat_shapes(
        library_call(
            "table"
        ),  # 
        transform_shape(
        library_call("lamp"),
        T = (0.4, -0.2, 0.98), # place in the top of the table
        R = (0, 0, 0),
        S = (1.,1.,1.),)        
         # 
    )  # 


@register()
def vintage_study_room() -> Shape:
    # the whole vintage study home
    return concat_shapes(
        library_call(
            "cabinet_with_books"
        ),
        library_call(
            "table_with_lamp"
        ),   
        transform_shape(     
        library_call(
            "chair"
        ),
        T = (0., 0.5, 0.), # place in the back of the table
        R = (0, 0, 0),
        S = (1.,1.,1.),)      
    )  # hint: these library calls must be implemented to be compatible with the usage
