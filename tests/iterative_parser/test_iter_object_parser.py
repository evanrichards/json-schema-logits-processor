import pytest

from json_schema_logits_processor.iterative_parser.enum_parser import \
    is_valid_enum
from json_schema_logits_processor.iterative_parser.object_parser import (
    ObjectState, _colon, _key, _post_value, _start, _value, is_valid_object)
from json_schema_logits_processor.iterative_parser.string_parser import (
    StringState, is_valid_string)
from json_schema_logits_processor.iterative_parser.types import (
    IncrementalObjectValue, IncrementalStringValue, IterativeParserResult)
from json_schema_logits_processor.schema.interative_schema import (
    EnumJsonSchema, JsonSchema, ObjectJsonSchema, SchemaId, StringJsonSchema,
    parse_schema_from_string)
from json_schema_logits_processor.schema.types import SchemaType


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
def start_state(global_schema: JsonSchema) -> IterativeParserResult:
    object_schema = global_schema[SchemaId(0)]
    assert isinstance(object_schema, ObjectJsonSchema)
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


@pytest.fixture
def a_word_key_state(global_schema: JsonSchema) -> IterativeParserResult:
    object_schema = global_schema[SchemaId(0)]
    assert isinstance(object_schema, ObjectJsonSchema)
    a_word_schema_id = object_schema.properties["a_word"]
    assert a_word_schema_id is not None
    return IterativeParserResult(
        valid=True,
        complete=False,
        string_index=0,
        schema_id=object_schema.id,
        next_state=ObjectState.KEY,
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


@pytest.fixture
def a_word_value_state(global_schema: JsonSchema) -> IterativeParserResult:
    object_schema = global_schema[SchemaId(0)]
    assert isinstance(object_schema, ObjectJsonSchema)
    return IterativeParserResult(
        valid=True,
        complete=False,
        string_index=0,
        schema_id=object_schema.id,
        next_state=ObjectState.VALUE,
        value=(
            (
                object_schema.id,
                IncrementalObjectValue(
                    remaining_keys=tuple(object_schema.properties.keys() - ("a_word",)),
                    current_value_schema_id=SchemaId(1),
                    current_key_value=IncrementalStringValue(
                        value="a_word", start_index=0
                    ),
                ),
            ),
        ),
    )


@pytest.mark.skip
def test_state_changes(start_state: IterativeParserResult, global_schema: JsonSchema):
    object_schema = global_schema[SchemaId(0)]
    assert isinstance(object_schema, ObjectJsonSchema)
    test_string = '{"a_word": "a_value"}'
    expected_states = [
        None,  # {
        (SchemaId(3), StringState.START, 1),  # 1 "
        (SchemaId(3), StringState.STRING, 2),  # 2 a
        (SchemaId(3), StringState.STRING, 3),  # 3 _
        (SchemaId(3), StringState.STRING, 4),  # 4 w
        (SchemaId(3), StringState.STRING, 5),  # 5 o
        (SchemaId(3), StringState.STRING, 6),  # 6 r
        (SchemaId(3), StringState.STRING, 7),  # 7 d
        (SchemaId(3), StringState.STRING, 8),  # 8 "
        (SchemaId(0), ObjectState.START, 9),  # 9 :
        (SchemaId(0), ObjectState.VALUE, 10),  # 10 
        (SchemaId(1), StringState.START, 11),  # 11 "
        (SchemaId(1), StringState.STRING, 12),  # 12 a
        (SchemaId(1), StringState.STRING, 13),  # 13 _
        (SchemaId(1), StringState.STRING, 14),  # 14 v
        (SchemaId(1), StringState.STRING, 15),  # 15 a
        (SchemaId(1), StringState.STRING, 16),  # 16 l
        (SchemaId(1), StringState.STRING, 17),  # 17 u
        (SchemaId(1), StringState.STRING, 18),  # 18 e
        (SchemaId(1), StringState.STRING, 19),  # 19 "
        (SchemaId(0), StringState.START, 20),  # 20 }
        (SchemaId(0), ObjectState.START, 21),  # 21 
    ]
    print(global_schema.__dict__)
    result = start_state
    for i in range(1, len(test_string)):
        sub_string = test_string[:i]
        current_schema = global_schema[result.schema_id]
        match current_schema.type:
            case SchemaType.OBJECT:
                result = is_valid_object(
                    sub_string, object_schema, global_schema, result
                )
            case SchemaType.STRING:
                assert isinstance(current_schema, StringJsonSchema)
                result = is_valid_string(sub_string, current_schema, result)
            case SchemaType.ENUM:
                assert isinstance(current_schema, EnumJsonSchema)
                result = is_valid_enum(sub_string, current_schema, result)
            case default:
                raise ValueError(f"Invalid schema type: {default}")
        assert result.valid, result
        assert (
            result.string_index == expected_states[i][2]
        ), f"{i}: string_index: {result.string_index} != {expected_states[i][2]}"
        assert (
            result.schema_id == expected_states[i][0]
        ), f"{i}: schema_id: {result.schema_id} != {expected_states[i][0]}"
        assert (
            result.next_state == expected_states[i][1]
        ), f"{i}: next_state: {result.next_state} != {expected_states[i][1]}"


# Test for valid start character
def test_start(start_state: IterativeParserResult, global_schema: JsonSchema):
    partial_json = "{"
    result = _start(partial_json, global_schema, start_state)
    assert result.valid is True
    assert result.complete is False
    assert result.next_state == StringState.START
    assert result.schema_id == SchemaId(3)
    assert result.string_index == 1
    print(result.value)
    assert result.value == start_state.value

    # Test for whitespace
    partial_json = " "
    result = _start(partial_json, global_schema, start_state)
    assert result.valid is True
    assert result.complete is False
    assert result.next_state == ObjectState.START
    assert result.schema_id == SchemaId(0)
    assert result.string_index == 1
    assert result.value == start_state.value

    # Test for invalid start character
    partial_json = "x"
    result = _start(partial_json, global_schema, start_state)
    assert result.valid is False
    assert result.complete is False
    assert result.next_state == ObjectState.DONE
    assert result.string_index == 0
    assert result.value == start_state.value


def test_key(a_word_key_state: IterativeParserResult, global_schema: JsonSchema):
    # Test for valid value
    partial_json = '"a_word"'
    result = _key(partial_json, global_schema, a_word_key_state)
    assert result.valid
    assert not result.complete
    assert result.next_state == StringState.STRING
    assert result.string_index == 1
    assert result.schema_id == SchemaId(3)
    assert len(result.value) == 1
    schema_id, value = result.value[0]
    assert schema_id == SchemaId(0)
    assert isinstance(value, IncrementalObjectValue)
    assert value.remaining_keys == ("a_word", "second_word")
    assert value.current_key_value is not None
    assert value.current_key_value.value == ""
    assert value.current_value_schema_id is None

    # Test for partial invalid key
    partial_json = "z"
    result = _key(partial_json, global_schema, a_word_key_state)
    assert result.valid is False
    assert result.complete is False
    assert result.next_state == ObjectState.KEY
    assert result.string_index == 0
    assert len(result.value) == 1
    schema_id, value = result.value[0]
    assert schema_id == SchemaId(0)
    assert isinstance(value, IncrementalObjectValue)
    assert value.remaining_keys == (
        "a_word",
        "second_word",
    )


def test_colon(start_state: IterativeParserResult):
    # Test for valid colon character
    partial_json = ":"
    result = _colon(partial_json, start_state)
    assert result.valid is True
    assert result.complete is False
    assert result.next_state == ObjectState.VALUE
    assert result.string_index == 1
    assert result.value == start_state.value

    # Test for whitespace
    partial_json = " "
    result = _colon(partial_json, start_state)
    assert result.valid is True
    assert result.complete is False
    assert result.next_state == ObjectState.COLON
    assert result.string_index == 1
    assert result.value == start_state.value

    # Test for invalid character
    partial_json = "x"
    result = _colon(partial_json, start_state)
    assert result.valid is False
    assert result.complete is False
    assert result.next_state == ObjectState.COLON
    assert result.string_index == 0
    assert result.value == start_state.value


def test_value(a_word_value_state: IterativeParserResult, global_schema: JsonSchema):
    # Test for valid complete value
    result = _value('"some value"', global_schema, a_word_value_state)
    assert result.valid
    assert not result.complete
    assert result.next_state == StringState.STRING
    assert result.schema_id == SchemaId(1)
    assert result.string_index == 1
    print(result.value)
    assert len(result.value) == 2


def test_post_value(start_state: IterativeParserResult):
    # Test for whitespace
    partial_json = " "
    result = _post_value(partial_json, start_state)
    assert result.valid is True
    assert result.complete is False
    assert result.next_state == ObjectState.POST_VALUE
    assert result.string_index == 1
    assert result.value == start_state.value

    # Test for comma
    partial_json = ","
    result = _post_value(partial_json, start_state)
    assert result.valid is True
    assert result.complete is False
    assert result.next_state == ObjectState.KEY
    assert result.string_index == 1
    assert result.value == start_state.value

    # Test for closing bracket
    partial_json = "}"
    result = _post_value(partial_json, start_state)
    assert result.valid is True
    assert result.complete is True
    assert result.next_state == ObjectState.DONE
    assert result.string_index == 1
    assert result.value == start_state.value

    # Test for invalid character
    partial_json = "x"
    result = _post_value(partial_json, start_state)
    assert result.valid is False
    assert result.complete is False
    assert result.next_state == ObjectState.POST_VALUE
    assert result.string_index == 0
    assert result.value == start_state.value
