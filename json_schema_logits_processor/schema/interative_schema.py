import json
from dataclasses import dataclass
from typing import NewType, Optional

from json_schema_logits_processor.schema.types import SchemaType

SchemaId = NewType("SchemaId", int)


@dataclass
class StringJsonSchema:
    type = SchemaType.STRING
    id: SchemaId
    parent_id: SchemaId | None

    def __hash__(self):
        return self.id


@dataclass
class NumberJsonSchema:
    type = SchemaType.NUMBER
    id: SchemaId
    parent_id: SchemaId | None

    def __hash__(self):
        return self.id


@dataclass
class EnumJsonSchema:
    type = SchemaType.ENUM
    values: tuple[str, ...]
    id: SchemaId
    parent_id: SchemaId | None

    def __hash__(self):
        return self.id


@dataclass
class ObjectJsonSchema:
    type = SchemaType.OBJECT
    id: SchemaId
    parent_id: SchemaId | None
    properties: dict[str, SchemaId]
    aditional_properties = False
    keys_schema: EnumJsonSchema

    def __hash__(self):
        return self.id


JsonSchemaUnion = (
    ObjectJsonSchema | StringJsonSchema | NumberJsonSchema | EnumJsonSchema
)


class JsonSchema:
    schemas: dict[SchemaId, JsonSchemaUnion] = {}
    hash: int

    def __init__(self, schemas: dict[SchemaId, JsonSchemaUnion]):
        self.schemas = schemas
        # a sanity check here to ensure the schema_ids are contiguous
        assert len(self.schemas) == max(self.schemas.keys()) + 1
        self.hash = hash(frozenset(self.schemas.items()))

    def __getitem__(self, item: SchemaId) -> JsonSchemaUnion:
        return self.schemas[item]

    def __hash__(self):
        return self.hash


class JsonSchemaParser:
    counter: SchemaId = SchemaId(-1)
    schemas: dict[SchemaId, JsonSchemaUnion] = {}

    @staticmethod
    def parse_schema_from_dict(schema_dict: dict):
        schema, _ = JsonSchemaParser()._parse_schema_from_dict(
            schema_dict, None
        )
        return JsonSchema(schema)

    def _parse_schema_from_dict(self, schema_dict: dict, parent_id: Optional[SchemaId]):
        self.counter = SchemaId(self.counter + 1)
        schema_id = self.counter
        schema = self._parse_schema(schema_dict, schema_id, parent_id)
        self.schemas[schema_id] = schema
        return self.schemas, schema_id

    def _parse_schema(
        self, schema_dict: dict, schema_id: SchemaId, parent_id: Optional[SchemaId]
    ) -> JsonSchemaUnion:
        match schema_dict:
            case {"type": "object", "properties": properties}:
                schema_properties = self._parse_properties(properties, schema_id)
                self.counter = SchemaId(self.counter + 1)
                key_schema_id = self.counter
                keys_schema = EnumJsonSchema(
                    values=tuple(schema_properties.keys()),
                    id=key_schema_id,
                    parent_id=schema_id,
                )
                self.schemas[key_schema_id] = keys_schema
                return ObjectJsonSchema(
                    id=schema_id,
                    parent_id=parent_id,
                    properties=schema_properties,
                    keys_schema=keys_schema,
                )
            case {"type": "string"}:
                return StringJsonSchema(id=schema_id, parent_id=parent_id)
            case {"type": "number"}:
                return NumberJsonSchema(id=schema_id, parent_id=parent_id)
            case {"type": "enum", "values": values}:
                return EnumJsonSchema(values=values, id=schema_id, parent_id=parent_id)
            case other:
                raise NotImplementedError(f"schema type {other} not implemented")

    def _parse_properties(
        self, properties: dict, parent_id: SchemaId
    ) -> dict[str, SchemaId]:
        parsed_properties = {}
        for key, value in properties.items():
            _, schema_id = self._parse_schema_from_dict(value, parent_id)
            parsed_properties[key] = schema_id
        return parsed_properties


def parse_schema_from_string(schema_str: str) -> JsonSchema:
    schema_dict = json.loads(schema_str)
    return JsonSchemaParser().parse_schema_from_dict(schema_dict)
