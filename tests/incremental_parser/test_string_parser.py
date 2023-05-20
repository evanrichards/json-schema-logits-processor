from json_schema_logits_processor.incremental_parser.string_parser import \
    is_valid_string


def test_valid_string():
    tests = [
        (" ", ""),
        (' "', ""),
        (' "h', "h"),
        (' "he', "he"),
        (' "hel', "hel"),
        (' "hell', "hell"),
        (' "hello', "hello"),
        (' "hello\\', "hello\\"),
        (' "hello\\"', 'hello\\"'),
        (' "hello\\""', 'hello\\"'),
        (' "hello\\"" ', 'hello\\"'),
    ]
    for input, output in tests:
        out = is_valid_string(input)
        assert out.valid, f"expected valid for {input}"
        assert (
            output == out.value
        ), f"expected value for {input} to be {output}, got {out.value}"
