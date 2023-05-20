from dataclasses import dataclass
from enum import Enum, auto

from json_schema_logits_processor.incremental_parser.types import (
    WHITESPACE, PartialValidationResult)

NUMBERS = "0123456789"
NUMBERS_AND_DOT = NUMBERS + "."
NUMBERS_AND_SPACE = NUMBERS + " "
END_OF_NUMBER_CHARS = " ,}]"


class NumberState(Enum):
    START = auto()
    INTEGER = auto()
    NEGATIVE = auto()
    DOT = auto()
    DECIMAL = auto()
    DONE = auto()


@dataclass
class InnerNumberValidationResult:
    valid: bool
    next_state: NumberState
    remaining_str: str


def is_valid_number(partial_json: str) -> PartialValidationResult:
    out = _next(partial_json, NumberState.START)
    while out.valid and out.remaining_str and out.next_state is not NumberState.DONE:
        out = _next(out.remaining_str, out.next_state)
    return PartialValidationResult(
        valid=out.valid,
        rest=out.remaining_str,
        value=partial_json[: len(partial_json) - len(out.remaining_str)],
        complete=out.next_state is NumberState.DONE,
    )


def _next(partial_json: str, next_state: NumberState) -> InnerNumberValidationResult:
    if next_state is NumberState.START:
        return _start(partial_json)
    if next_state is NumberState.INTEGER:
        return _integer(partial_json)
    if next_state is NumberState.DOT:
        return _dot(partial_json)
    if next_state is NumberState.DECIMAL:
        return _decimal(partial_json)
    if next_state is NumberState.NEGATIVE:
        return _negative(partial_json)
    raise ValueError(f"Unknown state {next_state}")


def _start(remaining_str: str):
    if remaining_str[0] == "-":
        return InnerNumberValidationResult(
            valid=True, next_state=NumberState.NEGATIVE, remaining_str=remaining_str[1:]
        )
    if remaining_str[0] in NUMBERS:
        return InnerNumberValidationResult(
            valid=True, next_state=NumberState.INTEGER, remaining_str=remaining_str[1:]
        )
    if remaining_str[0] in WHITESPACE:
        return InnerNumberValidationResult(
            valid=True, next_state=NumberState.START, remaining_str=remaining_str[1:]
        )
    return InnerNumberValidationResult(
        valid=False, next_state=NumberState.START, remaining_str=remaining_str
    )


def _integer(remaining_str: str) -> InnerNumberValidationResult:
    if remaining_str[0] in NUMBERS:
        return InnerNumberValidationResult(
            valid=True, next_state=NumberState.INTEGER, remaining_str=remaining_str[1:]
        )
    if remaining_str[0] == ".":
        return InnerNumberValidationResult(
            valid=True, next_state=NumberState.DOT, remaining_str=remaining_str[1:]
        )
    if remaining_str[0] in END_OF_NUMBER_CHARS:
        return InnerNumberValidationResult(
            valid=True, next_state=NumberState.DONE, remaining_str=remaining_str
        )
    return InnerNumberValidationResult(
        valid=False, next_state=NumberState.INTEGER, remaining_str=remaining_str
    )


def _negative(remaining_str: str):
    if remaining_str[0] in NUMBERS:
        return InnerNumberValidationResult(
            valid=True, next_state=NumberState.INTEGER, remaining_str=remaining_str[1:]
        )
    if remaining_str[0] == ".":
        return InnerNumberValidationResult(
            valid=True, next_state=NumberState.DOT, remaining_str=remaining_str[1:]
        )
    return InnerNumberValidationResult(
        valid=False, next_state=NumberState.NEGATIVE, remaining_str=remaining_str
    )


def _dot(remaining_str: str):
    if remaining_str[0] in NUMBERS:
        return InnerNumberValidationResult(
            valid=True, next_state=NumberState.DECIMAL, remaining_str=remaining_str[1:]
        )
    return InnerNumberValidationResult(
        valid=False, next_state=NumberState.DOT, remaining_str=remaining_str
    )


def _decimal(remaining_str: str):
    if remaining_str[0] in NUMBERS:
        return InnerNumberValidationResult(
            valid=True, next_state=NumberState.DECIMAL, remaining_str=remaining_str[1:]
        )
    if remaining_str[0] in END_OF_NUMBER_CHARS:
        return InnerNumberValidationResult(
            valid=True, next_state=NumberState.DONE, remaining_str=remaining_str
        )
    return InnerNumberValidationResult(
        valid=False, next_state=NumberState.DECIMAL, remaining_str=remaining_str
    )
