from json_schema_logits_processor.incremental_parser.enum_parser import \
    is_valid_enum
from json_schema_logits_processor.schema import EnumJsonSchema

enum_schema = EnumJsonSchema(values=tuple(["a", "b", "c is a bit longer"]))

valid_tests = ['"a"', '"b"', '"c is a bit longer"']

invalid_tests = [
    '"d"',
    "1",
    '""',
]


def test_valid_enum_parsing():
    for test in valid_tests:
        for substr in [test[: i + 1] for i in range(len(test) - 1)]:
            out = is_valid_enum(substr, enum_schema)
            assert out.valid, f"expected valid for {substr}"
            assert out.rest == "", "expected rest to be empty"


def test_invalid_enum_parsing():
    for test in invalid_tests:
        out = is_valid_enum(test, enum_schema)
        assert not out.valid, f"expected invalid for {test}"
