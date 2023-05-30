import pytest

from json_schema_logits_processor.iterative_parser.object_parser import (
    ObjectState, _colon, _post_value, _start)
from json_schema_logits_processor.iterative_parser.types import (
    IncrementalObjectValue, IterativeParserResult)
from json_schema_logits_processor.schema.interative_schema import (
    JsonSchema, ObjectJsonSchema, SchemaId, parse_schema_from_string)


@pytest.fixture
def global_schema() -> JsonSchema:
    schema_text = """
    {
        "type": "object",
        "properties": {
            "a_word": {"type": "string"},
            "second_word": {"type": "string"}
         }
    }
    """
    return parse_schema_from_string(schema_text)


@pytest.fixture
def object_schema(global_schema: JsonSchema) -> ObjectJsonSchema:
    object_schema = global_schema[SchemaId(0)]
    assert isinstance(object_schema, ObjectJsonSchema)
    return object_schema


@pytest.fixture
def start_state(global_schema: JsonSchema) -> IterativeParserResult:
    object_schema = global_schema[SchemaId(0)]
    assert isinstance(object_schema, ObjectJsonSchema)
    return IterativeParserResult(
        valid=True,
        complete=False,
        string_index=0,
        schema_id=object_schema.id,
        next_state=ObjectState.START,
        value_stack=(
            (
                object_schema.id,
                IncrementalObjectValue(
                    remaining_keys=tuple(object_schema.properties.keys()),
                    latest_added_key=None,
                ),
            ),
        ),
    )


# Test for valid start character
def test_start(start_state: IterativeParserResult, object_schema: ObjectJsonSchema):
    partial_json = "{"
    result = _start(partial_json, start_state.string_index, object_schema)
    assert result.valid is True
    assert result.complete is False
    assert result.next_state == 0
    assert result.schema_id == SchemaId(3)
    assert result.string_index == 1
    assert result.value_stack == ()

    # Test for whitespace
    partial_json = " "
    result = _start(partial_json, start_state.string_index, object_schema)
    assert result.valid is True
    assert result.complete is False
    assert result.next_state == ObjectState.START
    assert result.schema_id == SchemaId(0)
    assert result.string_index == 1
    assert result.value_stack == ()

    # Test for invalid start character
    partial_json = "x"
    result = _start(partial_json, start_state.string_index, object_schema)
    assert result.valid is False
    assert result.complete is False
    assert result.next_state == ObjectState.DONE
    assert result.string_index == 0
    assert result.value_stack == ()


def test_colon(start_state: IterativeParserResult, object_schema: ObjectJsonSchema):
    # Test for valid colon character
    partial_json = ":"
    result = _colon(partial_json, start_state.string_index, object_schema, "a_word")
    assert result.valid is True
    assert result.complete is False
    assert result.next_state == ObjectState.START
    assert result.schema_id == SchemaId(1)
    assert result.string_index == 1
    assert result.value_stack == ()

    # Test for whitespace
    partial_json = " "
    result = _colon(partial_json, start_state.string_index, object_schema, "a_word")
    assert result.valid is True
    assert result.complete is False
    assert result.next_state == ObjectState.COLON
    assert result.schema_id == SchemaId(0)
    assert result.string_index == 1
    assert result.value_stack == ()

    # Test for invalid character
    partial_json = "x"
    result = _colon(partial_json, start_state.string_index, object_schema, "a_word")
    assert result.valid is False
    assert result.complete is False
    assert result.next_state == ObjectState.COLON
    assert result.schema_id == SchemaId(0)
    assert result.string_index == 0
    assert result.value_stack == ()


def test_post_value(
    start_state: IterativeParserResult, object_schema: ObjectJsonSchema
):
    # Test for whitespace
    partial_json = " "
    result = _post_value(partial_json, start_state.string_index, object_schema)
    assert result.valid is True
    assert result.complete is False
    assert result.next_state == ObjectState.POST_VALUE
    assert result.schema_id == SchemaId(0)
    assert result.string_index == 1
    assert result.value_stack == ()

    # Test for comma
    partial_json = ","
    result = _post_value(partial_json, start_state.string_index, object_schema)
    assert result.valid is True
    assert result.complete is False
    assert result.next_state == ObjectState.START
    assert result.schema_id == SchemaId(3)
    assert result.string_index == 1
    assert result.value_stack == ()

    # Test for closing bracket
    partial_json = "}"
    result = _post_value(partial_json, start_state.string_index, object_schema)
    assert result.valid is True
    assert result.complete is True
    assert result.next_state == ObjectState.DONE
    assert result.schema_id == SchemaId(0)
    assert result.string_index == 1
    assert result.value_stack == ()

    # Test for invalid character
    partial_json = "x"
    result = _post_value(partial_json, start_state.string_index, object_schema)
    assert result.valid is False
    assert result.complete is False
    assert result.next_state == ObjectState.POST_VALUE
    assert result.string_index == 0
    assert result.value_stack == ()
