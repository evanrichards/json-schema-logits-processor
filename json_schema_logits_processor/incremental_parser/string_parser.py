from functools import lru_cache

from json_schema_logits_processor.incremental_parser.types import (
    WHITESPACE, PartialValidationResult)

START = 0
STRING = 1
ESCAPE = 2
DONE = 3


def is_valid_string(partial_json: str) -> PartialValidationResult:
    partial_json_len = len(partial_json)
    valid, next_state, new_index = _next(partial_json, 0, START)
    while valid and new_index < partial_json_len and next_state != DONE:
        valid, next_state, new_index = _next(partial_json, new_index, next_state)
    value = partial_json[:new_index]
    return_value = _parse_value(value)

    return PartialValidationResult(
        valid=valid,
        rest=partial_json[new_index:],
        value=return_value,
        complete=next_state == DONE,
    )


@lru_cache(maxsize=1024)
def _parse_value(value: str):
    value = value.strip()
    # remove functional quotes
    if len(value) > 0 and value[0] == '"':
        value = value[1:]
    if len(value) > 0 and value[-1] == '"' and len(value) > 1 and value[-2] != "\\":
        value = value[:-1]
    return value


@lru_cache(maxsize=1024)
def _next(partial_json: str, start_idx: int, next_state: int) -> tuple[bool, int, int]:
    if next_state == START:
        return _start(partial_json, start_idx)
    if next_state == STRING:
        return _string(partial_json, start_idx)
    if next_state == ESCAPE:
        return True, STRING, start_idx + 1
    raise ValueError(f"Unknown state {next_state}")


@lru_cache(maxsize=1024)
def _start(partial_json: str, start_idx: int) -> tuple[bool, int, int]:
    if partial_json[start_idx] in WHITESPACE:
        return (True, START, start_idx + 1)
    if partial_json[start_idx][0] == '"':
        return (True, STRING, start_idx + 1)
    return (False, START, start_idx)


@lru_cache(maxsize=1024)
def _string(partial_json: str, start_idx: int) -> tuple[bool, int, int]:
    if partial_json[start_idx][0] == '"':
        return (True, DONE, start_idx + 1)
    if partial_json[start_idx][0] == "\\":
        return (True, ESCAPE, start_idx + 1)
    return (True, STRING, start_idx + 1)
