from json_schema_logits_processor.incremental_parser.number_parser import is_valid_number


def test_valid_number():
    tests = [
        ("a", "skip", False),
        ("1", "", True),
        ("1.0", "", True),
        ("1.0 ", " ", True),
        ("1.0,", ",", True),
        ("1.0}", "}", True),
        ("1.0]", "]", True),
        ("1.0 2", " 2", True),
        ("-1.0", "", True),
        ("  -1.0", "", True),
        ("1a", "skip", False),
        ("1.0a", "skip", False),
        ("1.0.0", "skip", False),
        ("--1.0", "skip", False),
    ]
    for test in tests:
        partial_number, expected_rest, expected = test
        out = is_valid_number(partial_number)
        assert out.valid == expected, f"expected {expected} for {partial_number}"
        if out.valid:
            assert (
                out.rest == expected_rest
            ), f"expected rest to be '{expected_rest}' for '{partial_number}', got '{out.rest}'"
