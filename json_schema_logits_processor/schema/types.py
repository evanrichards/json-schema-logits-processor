from enum import Flag, auto


class SchemaType(Flag):
    STRING = auto()
    NUMBER = auto()
    OBJECT = auto()
    ENUM = auto()
    # BOOLEAN = "boolean"
    # ARRAY = "array"
    # NULL = "null"
