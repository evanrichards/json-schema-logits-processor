from json_schema_logits_processor.iterative_parser.string_parser import \
    is_valid_string
from json_schema_logits_processor.iterative_parser.types import (
    IterativeParserResult, pop_string_value)
from json_schema_logits_processor.schema.interative_schema import \
    EnumJsonSchema


def is_valid_enum(
    partial_json: str,
    enum_schema: EnumJsonSchema,
    previous_state: IterativeParserResult,
) -> IterativeParserResult:
    out = is_valid_string(partial_json, enum_schema, previous_state)
    string_value, _ = pop_string_value(out.value_stack, enum_schema.id)
    assert string_value is not None
    if not out.complete:
        valid = (
            any(value.startswith(string_value.value) for value in enum_schema.values)
            and out.valid
        )
        return IterativeParserResult(
            valid=valid,
            complete=out.complete,
            string_index=out.string_index,
            schema_id=enum_schema.id,
            next_state=out.next_state,
            value_stack=out.value_stack,
        )
    return IterativeParserResult(
        valid=out.valid and string_value.value in enum_schema.values,
        complete=out.complete,
        string_index=out.string_index,
        schema_id=enum_schema.id,
        next_state=out.next_state,
        value_stack=out.value_stack,
    )
