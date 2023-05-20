from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from json_schema_logits_processor.incremental_parser.enum_parser import \
    is_valid_enum
from json_schema_logits_processor.incremental_parser.types import (
    WHITESPACE, PartialValidationResult)
from json_schema_logits_processor.schema import (EnumJsonSchema, JsonSchema,
                                                 ObjectJsonSchema)


class ObjectState(Enum):
    START = auto()
    KEY = auto()
    VALUE = auto()
    POST_VALUE = auto()
    COLON = auto()
    DONE = auto()


@dataclass
class InnerObjectValidationResult:
    valid: bool
    next_state: ObjectState
    remaining_str: str
    value: str


def is_valid_object(
    partial_json: str, object_schema: ObjectJsonSchema
) -> PartialValidationResult:
    remaining_keys = tuple(object_schema.properties.keys())
    current_value_schema = None
    out = _next(partial_json, ObjectState.START, object_schema, remaining_keys)
    while out.valid and out.remaining_str and out.next_state is not ObjectState.DONE:
        last_state = out.next_state
        out = _next(
            out.remaining_str, out.next_state, current_value_schema, remaining_keys
        )
        if (
            out.valid
            and last_state is ObjectState.KEY
            and out.next_state is ObjectState.COLON
        ):
            current_value_schema = object_schema.properties[out.value]
            remaining_keys = tuple(key for key in remaining_keys if key != out.value)
    return PartialValidationResult(
        valid=out.valid,
        rest=out.remaining_str,
        value=out.value,
        complete=out.next_state is ObjectState.DONE,
    )


def _next(
    remaining_str: str,
    next_state: ObjectState,
    value_schema: Optional[JsonSchema],
    remaining_keys: tuple[str, ...],
) -> InnerObjectValidationResult:
    if next_state is ObjectState.START:
        return _start(remaining_str)
    if next_state is ObjectState.KEY:
        return _key(remaining_str, remaining_keys)
    if next_state is ObjectState.VALUE:
        if value_schema is None:
            raise ValueError("value schema must be provided")
        return _value(remaining_str, value_schema)
    if next_state is ObjectState.POST_VALUE:
        return _post_value(remaining_str)
    if next_state is ObjectState.COLON:
        return _colon(remaining_str)
    raise ValueError(f"Unknown state {next_state}")


def _start(remaining_str: str) -> InnerObjectValidationResult:
    if remaining_str[0] == "{":
        return InnerObjectValidationResult(
            valid=True,
            next_state=ObjectState.KEY,
            remaining_str=remaining_str[1:],
            value="",
        )
    if remaining_str[0] in WHITESPACE:
        return InnerObjectValidationResult(
            valid=True,
            next_state=ObjectState.START,
            remaining_str=remaining_str[1:],
            value="",
        )
    return InnerObjectValidationResult(
        valid=False, next_state=ObjectState.START, remaining_str=remaining_str, value=""
    )


def _key(
    remaining_str: str, remaining_keys: tuple[str, ...]
) -> InnerObjectValidationResult:
    # No keys left to match to, so any key is not valid
    if len(remaining_keys) == 0:
        return InnerObjectValidationResult(
            valid=False,
            next_state=ObjectState.POST_VALUE,
            remaining_str=remaining_str,
            value="",
        )
    out = is_valid_enum(remaining_str, EnumJsonSchema(values=remaining_keys))
    return InnerObjectValidationResult(
        valid=out.valid,
        next_state=ObjectState.COLON if out.complete else ObjectState.KEY,
        remaining_str=out.rest,
        value=out.value,
    )


def _colon(remaining_str: str) -> InnerObjectValidationResult:
    if remaining_str[0] in WHITESPACE:
        return InnerObjectValidationResult(
            valid=True,
            next_state=ObjectState.COLON,
            remaining_str=remaining_str[1:],
            value="",
        )
    if remaining_str[0] == ":":
        return InnerObjectValidationResult(
            valid=True,
            next_state=ObjectState.VALUE,
            remaining_str=remaining_str[1:],
            value="",
        )
    return InnerObjectValidationResult(
        valid=False,
        next_state=ObjectState.COLON,
        remaining_str=remaining_str,
        value="",
    )


def _value(remaining_str: str, value_schema: JsonSchema) -> InnerObjectValidationResult:
    from json_schema_logits_processor.incremental_parser import \
        parse_partial_json_value

    out = parse_partial_json_value(remaining_str, value_schema)
    return InnerObjectValidationResult(
        valid=out.valid,
        next_state=ObjectState.POST_VALUE,
        remaining_str=out.rest,
        value=out.value,
    )


def _post_value(remaining_str: str) -> InnerObjectValidationResult:
    if remaining_str[0] in WHITESPACE:
        return InnerObjectValidationResult(
            valid=True,
            next_state=ObjectState.POST_VALUE,
            remaining_str=remaining_str[1:],
            value="",
        )
    if remaining_str[0] == ",":
        return InnerObjectValidationResult(
            valid=True,
            next_state=ObjectState.KEY,
            remaining_str=remaining_str[1:],
            value="",
        )
    if remaining_str == "}":
        return InnerObjectValidationResult(
            valid=True,
            next_state=ObjectState.DONE,
            remaining_str=remaining_str[1:],
            value="",
        )
    return InnerObjectValidationResult(
        valid=False,
        next_state=ObjectState.POST_VALUE,
        remaining_str=remaining_str,
        value="",
    )
