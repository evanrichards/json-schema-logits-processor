from dataclasses import dataclass
from typing import Optional, Union

from json_schema_logits_processor.schema.interative_schema import SchemaId


@dataclass
class IncrementalStringValue:
    value: str
    start_index: int

    def __hash__(self):
        return hash((self.value, self.start_index))


@dataclass
class IncrementalObjectValue:
    remaining_keys: tuple[str, ...]
    current_value_schema_id: Optional[SchemaId]
    current_key_value: Optional[IncrementalStringValue]

    def __hash__(self):
        return hash(
            (
                self.remaining_keys,
                self.current_value_schema_id,
                self.current_key_value,
            )
        )


IterativeParserValue = tuple[
    tuple[
        SchemaId,
        Union[
            IncrementalStringValue,
            IncrementalObjectValue,
        ],
    ],
    ...,
]


def push_value(
    value_stack: IterativeParserValue,
    schema_id: SchemaId,
    value: Union[IncrementalStringValue, IncrementalObjectValue],
) -> IterativeParserValue:
    return value_stack + ((schema_id, value),)


def pop_string_value(
    value_stack: IterativeParserValue,
    schema_id: SchemaId,
) -> tuple[Optional[IncrementalStringValue], IterativeParserValue]:
    if len(value_stack) == 0:
        return None, value_stack
    if len(value_stack) == 1:
        rest, value = (), value_stack[0]
    else:
        rest, value = value_stack[:-1], value_stack[-1]
    if value[0] != schema_id:
        return None, value_stack
    assert value[0] == schema_id
    assert isinstance(value[1], IncrementalStringValue)
    return value[1], rest


def pop_object_value(
    valueStack: IterativeParserValue,
    schema_id: SchemaId,
) -> tuple[IncrementalObjectValue, IterativeParserValue]:
    rest, value = valueStack[:-1], valueStack[-1]
    assert value[0] == schema_id
    assert isinstance(value[1], IncrementalObjectValue)
    return value[1], rest


def find_value(
    value: IterativeParserValue, schema_id: SchemaId
) -> Optional[Union[IncrementalStringValue, IncrementalObjectValue]]:
    for v in value:
        if v[0] == schema_id:
            return v[1]
    return None


def replace_value(
    previous_value: IterativeParserValue | None,
    schema_id: SchemaId,
    return_value: IncrementalStringValue | IncrementalObjectValue,
) -> IterativeParserValue:
    if previous_value is None:
        return ((schema_id, return_value),)
    new_value = []
    found = False
    for value in previous_value:
        if value[0] == schema_id:
            new_value.append((schema_id, return_value))
            found = True
        else:
            new_value.append(value)
    if not found:
        new_value.append((schema_id, return_value))
    return tuple(new_value)


@dataclass
class IterativeParserResult:
    valid: bool
    complete: bool
    string_index: int
    schema_id: SchemaId
    next_state: int
    value_stack: IterativeParserValue

    def __hash__(self):
        return hash(
            (
                self.valid,
                self.complete,
                self.string_index,
                self.schema_id,
                self.next_state,
                self.value_stack,
            )
        )


WHITESPACE = " \t\n\r"
