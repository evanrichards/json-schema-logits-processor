from functools import cache
from typing import Optional

from transformers.utils.import_utils import lru_cache

from json_schema_logits_processor.iterative_parser.enum_parser import \
    is_valid_enum
from json_schema_logits_processor.iterative_parser.string_parser import (
    StringState, is_valid_string)
from json_schema_logits_processor.iterative_parser.types import (
    WHITESPACE, IncrementalObjectValue, IncrementalStringValue,
    IterativeParserResult, find_value, replace_value)
from json_schema_logits_processor.schema.interative_schema import (
    EnumJsonSchema, JsonSchema, ObjectJsonSchema, SchemaId, StringJsonSchema)
from json_schema_logits_processor.schema.types import SchemaType


class ObjectState:
    START = 0
    KEY = 1
    VALUE = 2
    POST_VALUE = 3
    COLON = 4
    DONE = 5


def _resume(
    object_schema: ObjectJsonSchema,
    previous_state: Optional[IterativeParserResult],
) -> IterativeParserResult:
    print("resume", previous_state)
    if previous_state is None:
        return IterativeParserResult(
            valid=True,
            complete=False,
            string_index=0,
            schema_id=object_schema.id,
            next_state=ObjectState.START,
            value=(
                (
                    object_schema.id,
                    IncrementalObjectValue(
                        remaining_keys=tuple(object_schema.properties.keys()),
                        current_value_schema_id=None,
                        current_key_value=None,
                    ),
                ),
            ),
        )
    object_value = find_value(previous_state.value, object_schema.id)

    if object_value is None:
        print("object_value is None")
        return IterativeParserResult(
            valid=previous_state.valid,
            complete=previous_state.complete,
            string_index=previous_state.string_index,
            schema_id=object_schema.id,
            next_state=previous_state.next_state,
            value=replace_value(
                previous_state.value,
                object_schema.id,
                IncrementalObjectValue(
                    remaining_keys=tuple(object_schema.properties.keys()),
                    current_value_schema_id=None,
                    current_key_value=None,
                ),
            ),
        )
    assert isinstance(object_value, IncrementalObjectValue)

    keys_schema = object_schema.keys_schema
    keys_value = find_value(previous_state.value, keys_schema.id)
    if keys_value is None:
        return IterativeParserResult(
            valid=previous_state.valid,
            complete=previous_state.complete,
            string_index=previous_state.string_index,
            schema_id=object_schema.id,
            next_state=previous_state.next_state,
            value=replace_value(
                previous_state.value,
                object_schema.id,
                object_value,
            ),
        )
    assert isinstance(keys_value, IncrementalStringValue)

    assert keys_value.value is not None
    print("keys_value", keys_value.value)
    assert keys_value.value in object_value.remaining_keys
    value_schema_id = object_schema.properties[keys_value.value]
    # This means we are coming back from completing parsing a key.
    # We need to set our next state appropriately, remove the new key from
    # remaining keys, and remove the key entry from the value
    if previous_state.next_state == ObjectState.START:
        return IterativeParserResult(
            valid=previous_state.valid,
            complete=False,
            string_index=previous_state.string_index,
            schema_id=object_schema.id,
            next_state=ObjectState.COLON,
            value=replace_value(
                previous_state.value,
                object_schema.id,
                IncrementalObjectValue(
                    remaining_keys=tuple(
                        object_schema.properties.keys() - (keys_value.value,)
                    ),
                    current_value_schema_id=value_schema_id,
                    current_key_value=None,
                ),
            ),
        )

    assert False, f"Unknown state {previous_state}"


def is_valid_object(
    partial_json: str,
    object_schema: ObjectJsonSchema,
    global_schema: JsonSchema,
    maybe_previous_state: Optional[IterativeParserResult],
) -> IterativeParserResult:
    previous_state = _resume(object_schema, maybe_previous_state)
    out = _next(
        partial_json,
        global_schema,
        previous_state,
    )
    return out


def _next(
    partial_json: str,
    global_schema: JsonSchema,
    previous_state: IterativeParserResult,
) -> IterativeParserResult:
    if previous_state.next_state is ObjectState.START:
        return _start(partial_json, global_schema, previous_state)
    if previous_state.next_state is ObjectState.KEY:
        return _key(
            partial_json,
            global_schema,
            previous_state,
        )
    if previous_state.next_state is ObjectState.VALUE:
        return _value(partial_json, global_schema, previous_state)
    if previous_state.next_state is ObjectState.POST_VALUE:
        return _post_value(partial_json, previous_state)
    if previous_state.next_state is ObjectState.COLON:
        return _colon(partial_json, previous_state)
    raise ValueError(f"Unknown state {previous_state.next_state}")


def _start(
    partial_json: str,
    global_schema: JsonSchema,
    previous_state: IterativeParserResult,
) -> IterativeParserResult:
    string_idx = previous_state.string_index
    if partial_json[string_idx] == "{":
        object_schema = global_schema[previous_state.schema_id]
        assert isinstance(object_schema, ObjectJsonSchema), object_schema
        keys_schema = object_schema.keys_schema
        new_value = replace_value(
            previous_state.value,
            object_schema.id,
            IncrementalObjectValue(
                remaining_keys=tuple(object_schema.properties.keys()),
                current_value_schema_id=None,
                current_key_value=None,
            ),
        )
        return IterativeParserResult(
            valid=True,
            complete=False,
            string_index=string_idx + 1,
            schema_id=keys_schema.id,
            next_state=StringState.START,
            value=new_value,
        )
    if partial_json[string_idx] in WHITESPACE:
        return IterativeParserResult(
            valid=True,
            complete=False,
            string_index=string_idx + 1,
            schema_id=previous_state.schema_id,
            next_state=ObjectState.START,
            value=previous_state.value,
        )
    return IterativeParserResult(
        valid=False,
        complete=False,
        string_index=string_idx,
        schema_id=previous_state.schema_id,
        next_state=ObjectState.DONE,
        value=previous_state.value,
    )


def _key(
    partial_json: str,
    global_schema: JsonSchema,
    previous_state: IterativeParserResult,
) -> IterativeParserResult:
    previous_object_value = find_value(previous_state.value, previous_state.schema_id)
    assert isinstance(
        previous_object_value, IncrementalObjectValue
    ), previous_object_value
    object_schema = global_schema[previous_state.schema_id]
    assert isinstance(object_schema, ObjectJsonSchema), object_schema
    keys_schema = object_schema.keys_schema
    assert keys_schema.parent_id is not None
    # No keys left to match to, so any key is not valid

    if len(previous_object_value.remaining_keys) == 0:
        return IterativeParserResult(
            valid=False,
            complete=False,
            string_index=previous_state.string_index,
            schema_id=previous_state.schema_id,
            next_state=ObjectState.KEY,
            value=previous_state.value,
        )
    out = is_valid_enum(
        partial_json,
        keys_schema,
        IterativeParserResult(
            valid=True,
            complete=False,
            string_index=previous_state.string_index,
            schema_id=previous_state.schema_id,
            next_state=0,
            value=previous_state.value,
        ),
    )
    key_value = find_value(out.value, keys_schema.id)
    assert isinstance(key_value, IncrementalStringValue)
    valid = not out.complete or key_value.value in previous_object_value.remaining_keys
    if not out.valid or not valid:
        return IterativeParserResult(
            valid=False,
            complete=False,
            string_index=previous_state.string_index,
            schema_id=previous_state.schema_id,
            next_state=ObjectState.KEY,
            value=previous_state.value,
        )
    next_value = previous_state.value
    value_schema_id = None
    if out.complete:
        current_key_value = key_value.value
        assert current_key_value
        value_schema_id = object_schema.properties[current_key_value]
    new_value = IncrementalObjectValue(
        remaining_keys=tuple(
            key
            for key in previous_object_value.remaining_keys
            if key != key_value.value
        ),
        current_value_schema_id=value_schema_id,
        current_key_value=key_value,
    )
    next_value = replace_value(previous_state.value, keys_schema.parent_id, new_value)

    return IterativeParserResult(
        valid=valid,
        complete=out.complete,
        string_index=out.string_index,
        schema_id=keys_schema.parent_id if out.complete else out.schema_id,
        next_state=ObjectState.COLON if out.complete else out.next_state,
        value=next_value,
    )


def _colon(
    partial_json: str,
    previous_state: IterativeParserResult,
) -> IterativeParserResult:
    if partial_json[previous_state.string_index] in WHITESPACE:
        return IterativeParserResult(
            valid=True,
            complete=False,
            string_index=previous_state.string_index + 1,
            schema_id=previous_state.schema_id,
            next_state=ObjectState.COLON,
            value=previous_state.value,
        )
    if partial_json[previous_state.string_index] == ":":
        return IterativeParserResult(
            valid=True,
            complete=False,
            string_index=previous_state.string_index + 1,
            schema_id=previous_state.schema_id,
            next_state=ObjectState.VALUE,
            value=previous_state.value,
        )
    return IterativeParserResult(
        valid=False,
        complete=False,
        string_index=previous_state.string_index,
        schema_id=previous_state.schema_id,
        next_state=ObjectState.COLON,
        value=previous_state.value,
    )


def _value(
    partial_json: str,
    global_schema: JsonSchema,
    previous_state: IterativeParserResult,
) -> IterativeParserResult:
    out = None
    current_schema = global_schema[previous_state.schema_id]
    assert isinstance(current_schema, ObjectJsonSchema)
    object_value = find_value(previous_state.value, previous_state.schema_id)
    assert isinstance(object_value, IncrementalObjectValue), object_value
    value_schema_id = object_value.current_value_schema_id
    assert value_schema_id is not None
    value_schema = global_schema[value_schema_id]

    match value_schema.type:
        case SchemaType.STRING:
            assert isinstance(value_schema, StringJsonSchema)
            out = is_valid_string(
                partial_json,
                value_schema,
                IterativeParserResult(
                    valid=True,
                    complete=False,
                    string_index=previous_state.string_index,
                    schema_id=value_schema.id,
                    next_state=0,
                    value=previous_state.value,
                ),
            )
        case default:
            raise ValueError(f"Unknown schema type {default}")
    if out.complete:
        return IterativeParserResult(
            valid=out.valid,
            complete=out.complete,
            string_index=out.string_index,
            schema_id=previous_state.schema_id,
            next_state=ObjectState.VALUE
            if not out.complete
            else ObjectState.POST_VALUE,
            value=previous_state.value,
        )
    return out


def _post_value(
    partial_json: str,
    previous_state: IterativeParserResult,
) -> IterativeParserResult:
    if partial_json[previous_state.string_index] in WHITESPACE:
        return IterativeParserResult(
            valid=True,
            complete=False,
            string_index=previous_state.string_index + 1,
            schema_id=previous_state.schema_id,
            next_state=ObjectState.POST_VALUE,
            value=previous_state.value,
        )
    if partial_json[previous_state.string_index] == ",":
        return IterativeParserResult(
            valid=True,
            complete=False,
            string_index=previous_state.string_index + 1,
            schema_id=previous_state.schema_id,
            next_state=ObjectState.KEY,
            value=previous_state.value,
        )
    if partial_json[previous_state.string_index] == "}":
        return IterativeParserResult(
            valid=True,
            complete=True,
            string_index=previous_state.string_index + 1,
            schema_id=previous_state.schema_id,
            next_state=ObjectState.DONE,
            value=previous_state.value,
        )
    return IterativeParserResult(
        valid=False,
        complete=False,
        string_index=previous_state.string_index,
        schema_id=previous_state.schema_id,
        next_state=ObjectState.POST_VALUE,
        value=previous_state.value,
    )
