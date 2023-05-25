import pytest

from json_schema_logits_processor.iterative_parser import \
    parse_partial_json_value
from json_schema_logits_processor.iterative_parser.types import \
    IncrementalStringValue
from json_schema_logits_processor.schema.interative_schema import (
    JsonSchema, SchemaId, parse_schema_from_string)


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
def str_only_json_schema() -> JsonSchema:
    schema_str = '{"type": "string"}'
    schema = parse_schema_from_string(schema_str)
    return schema


def test_iterative_parser(str_only_json_schema: JsonSchema):
    test_str = '"test"'
    tests = [(test_str[:i], test_str[i], i) for i in range(len(test_str) - 1)]
    for partial_json, next_char, count in tests:
        result = parse_partial_json_value(partial_json, next_char, str_only_json_schema)
        assert result.valid
        assert not result.complete
        assert result.string_index == count + 1
        assert len(result.value) == 1
        assert isinstance(result.value[0][1], IncrementalStringValue)
        assert result.value[0][1].start_index == 0
        assert result.value[0][1].value == (partial_json + next_char).replace('"', "")
    result = parse_partial_json_value('"test', '"', str_only_json_schema)
    assert result.valid
    assert result.complete
    assert result.string_index == 6
    assert len(result.value) == 1
    assert isinstance(result.value[0][1], IncrementalStringValue)
    assert result.value[0][1].start_index == 0
    assert result.value[0][1].value == "test"


def test_iterative_parser_invalid(str_only_json_schema: JsonSchema):
    result = parse_partial_json_value("tes", "t", str_only_json_schema)
    assert not result.valid
    assert not result.complete
    assert result.string_index == 0


def test_state_changes(global_schema: JsonSchema):
    test_str = '{"a_word": "test"}'
    tests = [(test_str[:i], test_str[i], i) for i in range(len(test_str) - 1)]
    for partial_json, next_char, count in tests:
        print(f"testing {partial_json}, {next_char}")
        result = parse_partial_json_value(partial_json, next_char, global_schema)
        print("test result", result)
        assert result.valid, f"failed at {count}, {partial_json}, {next_char}"
        assert result.string_index == count + 1

def test_invalid_input_state_changes(global_schema: JsonSchema):
    test_str = '{"a_word": "test", "a_word": "test"}'
    tests = [(test_str[:i], test_str[i], i) for i in range(len(test_str) - 1)]
    failed = False
    for partial_json, next_char, count in tests:
        result = parse_partial_json_value(partial_json, next_char, global_schema)
        if not result.valid:
            failed = True
            break
    assert failed, "should have failed on double key"


