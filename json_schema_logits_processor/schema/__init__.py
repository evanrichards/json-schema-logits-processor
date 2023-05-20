import json
from dataclasses import dataclass

from json_schema_logits_processor.schema.types import SchemaType


@dataclass
class ObjectJsonSchema:
    type = SchemaType.OBJECT
    properties: dict[str, "JsonSchema"]
    aditional_properties = False


@dataclass
class StringJsonSchema:
    type = SchemaType.STRING


StaticStringJsonSchema = StringJsonSchema()


@dataclass
class NumberJsonSchema:
    type = SchemaType.NUMBER


StaticNumberJsonSchema = NumberJsonSchema()


@dataclass
class EnumJsonSchema:
    type = SchemaType.ENUM
    values: tuple[str, ...]


JsonSchema = ObjectJsonSchema | StringJsonSchema | NumberJsonSchema | EnumJsonSchema


def parse_schema_from_string(schema_str: str) -> "JsonSchema":
    schema_dict = json.loads(schema_str)
    return parse_schema_from_dict(schema_dict)


def parse_schema_from_dict(schema_dict: dict) -> "JsonSchema":
    match schema_dict:
        case {"type": "object", "properties": properties}:
            return ObjectJsonSchema(
                properties=parse_properties(properties),
            )
        case {"type": "string"}:
            return StaticStringJsonSchema
        case {"type": "number"}:
            return StaticNumberJsonSchema
        case {"type": "enum", "values": values}:
            return EnumJsonSchema(values=values)
        case other:
            raise NotImplementedError(f"schema type {other} not implemented")


def parse_properties(properties: dict) -> dict[str, "JsonSchema"]:
    return {key: parse_schema_from_dict(value) for key, value in properties.items()}
