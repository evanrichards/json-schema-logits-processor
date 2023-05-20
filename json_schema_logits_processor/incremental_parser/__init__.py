from json_schema_logits_processor.incremental_parser.number_parser import \
    is_valid_number
from json_schema_logits_processor.incremental_parser.object_parser import \
    is_valid_object
from json_schema_logits_processor.incremental_parser.string_parser import \
    is_valid_string
from json_schema_logits_processor.incremental_parser.types import \
    PartialValidationResult
from json_schema_logits_processor.schema import (JsonSchema, NumberJsonSchema,
                                                 ObjectJsonSchema,
                                                 StringJsonSchema)


def parse_partial_json_value(
    json_str: str, schema: JsonSchema
) -> PartialValidationResult:
    match schema:
        case ObjectJsonSchema(_):
            return is_valid_object(json_str, schema)
        case StringJsonSchema():
            return is_valid_string(json_str)
        case NumberJsonSchema():
            return is_valid_number(json_str)
        case other:
            raise NotImplementedError(f"schema type {other} not implemented")
