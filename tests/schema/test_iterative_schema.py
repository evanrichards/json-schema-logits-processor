from json_schema_logits_processor.schema.interative_schema import (
    SchemaId, parse_schema_from_string)
from json_schema_logits_processor.schema.types import SchemaType


def test_iterative_schema_parsing():
    schema_str = '{"type": "object", "properties": {"a": {"type": "string"}}}'
    schema = parse_schema_from_string(schema_str)
    assert schema[SchemaId(0)].type == SchemaType.OBJECT
    assert schema[SchemaId(1)].type == SchemaType.STRING
    assert schema[SchemaId(2)].type == SchemaType.ENUM
