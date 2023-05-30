from transformers.utils.import_utils import lru_cache

from json_schema_logits_processor.iterative_parser.enum_parser import \
    is_valid_enum
from json_schema_logits_processor.iterative_parser.object_parser import \
    is_valid_object
from json_schema_logits_processor.iterative_parser.string_parser import \
    is_valid_string
from json_schema_logits_processor.iterative_parser.types import \
    IterativeParserResult
from json_schema_logits_processor.schema.interative_schema import (
    EnumJsonSchema, JsonSchema, ObjectJsonSchema, SchemaId, StringJsonSchema)


def parse_partial_json_value(
    root_string: str,
    next_token: str,
    schema: JsonSchema,
) -> tuple[bool, bool]:
    penultimate_state = _parse_partial_json_value(root_string, schema)
    if not penultimate_state.valid:
        return (
            penultimate_state.valid,
            penultimate_state.complete and penultimate_state.schema_id == SchemaId(0),
        )
    if len(root_string) + 1 < penultimate_state.string_index:
        return (
            penultimate_state.valid,
            penultimate_state.complete and penultimate_state.schema_id == SchemaId(0),
        )
    out = _parse_one_token(root_string + next_token, penultimate_state, schema)
    return out.valid, out.complete and out.schema_id == SchemaId(0)


@lru_cache(maxsize=1_000_000)
def _parse_partial_json_value(
    json_str: str, schema: JsonSchema
) -> IterativeParserResult:
    if json_str == "":
        return IterativeParserResult(
            valid=True,
            complete=False,
            string_index=0,
            schema_id=SchemaId(0),
            next_state=0,
            value_stack=(),
        )
    previous_result = _parse_partial_json_value(json_str[:-1], schema)
    if not previous_result.valid:
        return previous_result

    new_result = _parse_one_token(json_str, previous_result, schema)
    return new_result


@lru_cache(maxsize=1_000_000)
def _parse_one_token(
    json_str: str, state: IterativeParserResult, schema: JsonSchema
) -> IterativeParserResult:
    curr_schema = schema[state.schema_id]
    if state.complete:
        if curr_schema.parent_id is None:  # root node
            # we should be done, if we have more non-whitespace characters
            # then we are invalid
            return IterativeParserResult(
                valid=len(json_str[state.string_index :].strip()) == 0,
                complete=len(json_str) == state.string_index,
                string_index=state.string_index + 1,
                schema_id=state.schema_id,
                next_state=0,
                value_stack=state.value_stack,
            )
        curr_schema = schema[curr_schema.parent_id]
    match curr_schema:
        case StringJsonSchema():
            return is_valid_string(json_str, curr_schema, state)
        case ObjectJsonSchema():
            return is_valid_object(json_str, curr_schema, state)
        case EnumJsonSchema():
            return is_valid_enum(json_str, curr_schema, state)
        case default:
            raise ValueError(f"Unknown schema type {default}")
