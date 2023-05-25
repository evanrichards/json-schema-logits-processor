import pytest

from json_schema_logits_processor.iterative_parser.string_parser import \
    is_valid_string
from json_schema_logits_processor.iterative_parser.types import (
    IncrementalStringValue, IterativeParserResult, pop_string_value)
from json_schema_logits_processor.schema.interative_schema import (
    SchemaId, StringJsonSchema, parse_schema_from_string)


@pytest.fixture
def string_schema() -> StringJsonSchema:
    schema_str = '{"type": "string"}'
    schema = parse_schema_from_string(schema_str)
    string_schema = schema[SchemaId(0)]
    assert isinstance(string_schema, StringJsonSchema)
    return string_schema


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


def test_start_string(
    string_schema: StringJsonSchema, start_state: IterativeParserResult
):
    out = is_valid_string('"test"', string_schema, start_state)
    assert out.valid
    assert not out.complete
    assert out.string_index == 1
    value, rest = pop_string_value(out.value_stack, string_schema.id)
    assert value is not None
    assert value.start_index == 0
    assert value.value == ""
    assert len(rest) == 0


def test_mid_string(string_schema: StringJsonSchema):
    out = is_valid_string(
        'some garbage that gets skipped "test"    ',
        string_schema,
        IterativeParserResult(
            valid=True,
            complete=False,
            # string index of the second quote
            string_index=36,
            schema_id=SchemaId(0),
            value_stack=(
                (SchemaId(-1), IncrementalStringValue(start_index=0, value="skip me")),
                (SchemaId(0), IncrementalStringValue(start_index=31, value="test")),
            ),
            next_state=1,
        ),
    )
    assert out.valid
    assert out.complete
    assert out.string_index == 37
    value, rest = pop_string_value(out.value_stack, string_schema.id)
    assert value is not None
    assert value.start_index == 31
    assert value.value == "test"
    assert len(rest) == 1


def test_state_changes(
    string_schema: StringJsonSchema, start_state: IterativeParserResult
):
    out = is_valid_string('"test"', string_schema, start_state)
    while not out.complete and out.valid:
        out = is_valid_string('"test"', string_schema, out)
    assert out.valid
    assert out.complete
    assert out.string_index == 6
    value, rest = pop_string_value(out.value_stack, string_schema.id)
    assert value is not None
    assert value.start_index == 0
    assert value.value == "test"
    assert len(rest) == 0
