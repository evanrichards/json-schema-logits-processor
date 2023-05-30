from json_schema_logits_processor.iterative_parser.types import (
    WHITESPACE, IncrementalObjectValue, IterativeParserResult,
    IterativeParserValue, pop_object_value, pop_string_value, pop_value,
    push_value)
from json_schema_logits_processor.schema.interative_schema import \
    ObjectJsonSchema


class ObjectState:
    START = 0
    POST_VALUE = 1
    COLON = 2
    DONE = 3


def _resume(
    object_schema: ObjectJsonSchema,
    previous_state: IterativeParserResult,
) -> tuple[int, int, tuple[str, ...], str | None, IterativeParserValue]:
    keys_value, rest = pop_string_value(
        previous_state.value_stack, object_schema.keys_schema.id
    )
    schema_id, property_value = None, None
    for schema_id in object_schema.properties.values():
        property_value, rest = pop_value(rest, schema_id)
        if property_value is not None:
            break

    object_value, rest = pop_object_value(rest, object_schema.id)

    if object_value is None:
        assert keys_value is None
        assert property_value is None
        return (
            previous_state.string_index,
            previous_state.next_state,
            object_schema.keys_schema.values,
            None,
            rest,
        )

    if keys_value is None and property_value is None:
        return (
            previous_state.string_index,
            previous_state.next_state,
            object_value.remaining_keys,
            object_value.latest_added_key,
            rest,
        )

    if keys_value is not None:
        # This means we are coming back from completing parsing a key.
        # We need to set our next state appropriately, remove the new key from
        # remaining keys, and remove the key entry from the value
        assert keys_value.value in object_value.remaining_keys
        return (
            previous_state.string_index,
            ObjectState.COLON,
            tuple(
                [key for key in object_value.remaining_keys if key != keys_value.value]
            ),
            keys_value.value,
            rest,
        )

    if property_value is not None:
        # This means we are coming back from completing parsing a value.
        # We need to set our next state appropriately
        assert schema_id is not None
        return (
            previous_state.string_index,
            ObjectState.POST_VALUE,
            object_value.remaining_keys,
            object_value.latest_added_key,
            rest,
        )

    assert False, f"Unknown state {previous_state}"


def is_valid_object(
    partial_json: str,
    object_schema: ObjectJsonSchema,
    previous_state: IterativeParserResult,
) -> IterativeParserResult:
    string_index, next_state, remaining_keys, latest_key, rest = _resume(
        object_schema, previous_state
    )
    out = _next(
        partial_json,
        string_index,
        next_state,
        object_schema,
        latest_key,
    )
    return IterativeParserResult(
        string_index=out.string_index,
        next_state=out.next_state,
        valid=out.valid,
        complete=out.complete,
        schema_id=out.schema_id,
        value_stack=push_value(
            rest, object_schema.id, IncrementalObjectValue(remaining_keys, latest_key)
        ),
    )


def _next(
    partial_json: str,
    string_index: int,
    next_state: int,
    object_schema: ObjectJsonSchema,
    latest_key: str | None = None,
) -> IterativeParserResult:
    if next_state is ObjectState.START:
        return _start(partial_json, string_index, object_schema)
    if next_state is ObjectState.POST_VALUE:
        return _post_value(partial_json, string_index, object_schema)
    if next_state is ObjectState.COLON:
        return _colon(partial_json, string_index, object_schema, latest_key)
    raise ValueError(f"Unknown state {next_state}")


def _start(
    partial_json: str,
    string_index: int,
    object_schema: ObjectJsonSchema,
) -> IterativeParserResult:
    if partial_json[string_index] == "{":
        return IterativeParserResult(
            valid=True,
            complete=False,
            string_index=string_index + 1,
            schema_id=object_schema.keys_schema.id,
            next_state=0,
            value_stack=(),
        )
    if partial_json[string_index] in WHITESPACE:
        return IterativeParserResult(
            valid=True,
            complete=False,
            string_index=string_index + 1,
            schema_id=object_schema.id,
            next_state=ObjectState.START,
            value_stack=(),
        )
    return IterativeParserResult(
        valid=False,
        complete=False,
        string_index=string_index,
        schema_id=object_schema.id,
        next_state=ObjectState.DONE,
        value_stack=(),
    )


def _colon(
    partial_json: str,
    string_index: int,
    object_schema: ObjectJsonSchema,
    latest_key: str,
) -> IterativeParserResult:
    if partial_json[string_index] in WHITESPACE:
        return IterativeParserResult(
            valid=True,
            complete=False,
            string_index=string_index + 1,
            schema_id=object_schema.id,
            next_state=ObjectState.COLON,
            value_stack=(),
        )
    if partial_json[string_index] == ":":
        assert latest_key is not None
        schema_id = object_schema.properties[latest_key]
        return IterativeParserResult(
            valid=True,
            complete=False,
            string_index=string_index + 1,
            schema_id=schema_id,
            next_state=0,
            value_stack=(),
        )
    return IterativeParserResult(
        valid=False,
        complete=False,
        string_index=string_index,
        schema_id=object_schema.id,
        next_state=ObjectState.COLON,
        value_stack=(),
    )


def _post_value(
    partial_json: str,
    string_index: int,
    object_schema: ObjectJsonSchema,
) -> IterativeParserResult:
    if partial_json[string_index] in WHITESPACE:
        return IterativeParserResult(
            valid=True,
            complete=False,
            string_index=string_index + 1,
            schema_id=object_schema.id,
            next_state=ObjectState.POST_VALUE,
            value_stack=(),
        )
    if partial_json[string_index] == ",":
        return IterativeParserResult(
            valid=True,
            complete=False,
            string_index=string_index + 1,
            schema_id=object_schema.keys_schema.id,
            next_state=0,
            value_stack=(),
        )
    if partial_json[string_index] == "}":
        return IterativeParserResult(
            valid=True,
            complete=True,
            string_index=string_index + 1,
            schema_id=object_schema.id,
            next_state=ObjectState.DONE,
            value_stack=(),
        )
    return IterativeParserResult(
        valid=False,
        complete=False,
        string_index=string_index,
        schema_id=object_schema.id,
        next_state=ObjectState.POST_VALUE,
        value_stack=(),
    )
