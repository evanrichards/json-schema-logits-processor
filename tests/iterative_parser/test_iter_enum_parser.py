import pytest

from json_schema_logits_processor.iterative_parser.enum_parser import \
    is_valid_enum
from json_schema_logits_processor.iterative_parser.types import (
    IterativeParserResult, pop_string_value)
from json_schema_logits_processor.schema.interative_schema import (
    EnumJsonSchema, SchemaId, parse_schema_from_string)


@pytest.fixture
def enum_schema() -> EnumJsonSchema:
    schema_str = '{"type": "enum", "values": ["a", "b", "c"]}'
    schema = parse_schema_from_string(schema_str)
    enum_schema = schema[SchemaId(0)]
    assert isinstance(enum_schema, EnumJsonSchema)
    return enum_schema


@pytest.fixture
def start_state() -> IterativeParserResult:
    return IterativeParserResult(
        valid=True,
        complete=False,
        string_index=0,
        schema_id=SchemaId(0),
        value_stack=(),
        next_state=0,
    )


def test_enum_valid(enum_schema: EnumJsonSchema, start_state: IterativeParserResult):
    result = is_valid_enum('"a"', enum_schema, start_state)
    assert result.valid
    assert not result.complete
    assert result.string_index == 1
    value, rest = pop_string_value(result.value_stack, enum_schema.id)
    assert value is not None
    assert value.start_index == 0
    assert value.value == ""
    assert len(rest) == 0


def test_enum_invalid(enum_schema: EnumJsonSchema, start_state: IterativeParserResult):
    result = is_valid_enum("z", enum_schema, start_state)
    assert not result.valid


def test_state_changes(enum_schema: EnumJsonSchema, start_state: IterativeParserResult):
    out = is_valid_enum('"a"', enum_schema, start_state)
    while not out.complete and out.valid:
        out = is_valid_enum('"a"', enum_schema, out)
    assert out.valid
    assert out.complete
    assert out.string_index == 3
    value, rest = pop_string_value(out.value_stack, enum_schema.id)
    assert value is not None
    assert value.start_index == 0
    assert value.value == "a"
    assert len(rest) == 0
