from json_schema_logits_processor.iterative_parser.types import (
    WHITESPACE, IncrementalStringValue, IterativeParserResult,
    IterativeParserValue, pop_string_value, push_value)
from json_schema_logits_processor.schema.interative_schema import (
    EnumJsonSchema, SchemaId, StringJsonSchema)


class StringState:
    START = 0
    STRING = 1
    ESCAPE = 2
    DONE = 3


def _resume(
    schema_id: SchemaId, previous_state: IterativeParserResult
) -> tuple[int, int, int, IterativeParserValue]:
    value, rest = pop_string_value(previous_state.value_stack, schema_id)
    if value is None:
        return (
            previous_state.string_index,
            previous_state.string_index,
            previous_state.next_state,
            rest,
        )

    return (
        value.start_index,
        previous_state.string_index,
        previous_state.next_state,
        rest,
    )


def is_valid_string(
    partial_json: str,
    schema: StringJsonSchema | EnumJsonSchema,
    previous_state: IterativeParserResult,
) -> IterativeParserResult:
    value_start_idx, string_idx, next_state, rest = _resume(schema.id, previous_state)

    valid, next_state, new_index = _next(partial_json, string_idx, next_state)
    return_value = _parse_value(partial_json, value_start_idx, new_index)
    new_value = IncrementalStringValue(value=return_value, start_index=value_start_idx)
    return IterativeParserResult(
        valid=valid,
        complete=next_state == StringState.DONE,
        string_index=new_index,
        schema_id=schema.id,
        next_state=next_state if next_state != StringState.DONE else 0,
        value_stack=push_value(rest, schema.id, new_value),
    )


def _parse_value(value: str, start_idx: int, end_idx: int):
    value = value[start_idx:end_idx]
    value = value.lstrip()
    # remove functional quotes
    if len(value) > 0 and value.startswith('"'):
        value = value[1:]
    if len(value) > 0 and value.endswith('"') and len(value) > 1 and value[-2] != "\\":
        value = value[:-1]
    return value


def _next(partial_json: str, start_idx: int, next_state: int):
    if next_state == StringState.START:
        return _start(partial_json, start_idx)
    if next_state == StringState.STRING:
        return _string(partial_json, start_idx)
    if next_state == StringState.ESCAPE:
        return True, StringState.STRING, start_idx + 1
    raise ValueError(f"Unknown state {next_state}")


def _start(partial_json: str, start_idx: int):
    if partial_json[start_idx] in WHITESPACE:
        return (True, StringState.START, start_idx + 1)
    if partial_json[start_idx].startswith('"'):
        return (True, StringState.STRING, start_idx + 1)
    return (False, StringState.START, start_idx)


def _string(partial_json: str, start_idx: int):
    if partial_json[start_idx].startswith('"'):
        return (True, StringState.DONE, start_idx + 1)
    if partial_json[start_idx].startswith("\\"):
        return (True, StringState.ESCAPE, start_idx + 1)
    return (True, StringState.STRING, start_idx + 1)
