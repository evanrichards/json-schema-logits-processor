from json_schema_logits_processor.incremental_parser.object_parser import \
    is_valid_object
from json_schema_logits_processor.schema import (ObjectJsonSchema,
                                                 StringJsonSchema)

test_schema = ObjectJsonSchema(
    properties={
        "a": StringJsonSchema(),
        "b": StringJsonSchema(),
    },
)

valid_objects = ['{"a": "hello", "b": "world"}', '{"a": "hello"}']
invalid_objects = [
    # valid json, invalid for schema
    '"a"',
    # invalid json
    '{"a"[]}',
    # valid json, extra fields
    '{"a": "hello", "b": "world", "c": "!"}',
    # valid json, invalid value type
    '{"a": "hello", "b": 1}',
    # invalid json, multiple of the same key
    '{"a": "hello", "a": "world"}',
]


def test_valid_objects():
    for test in valid_objects:
        for substring in range(len(test) - 1):
            print(f'testing "{test[: substring + 1]}"')
            out = is_valid_object(test[: substring + 1], test_schema)
            assert out.valid, f"expected valid for {test[:substring + 1]}"
            assert out.rest == "", "expected rest to be empty"


def test_invalid_objects():
    for test in invalid_objects:
        print(f'testing "{test}"')
        out = is_valid_object(test, test_schema)
        assert not out.valid, f"expected invalid for {test}"
