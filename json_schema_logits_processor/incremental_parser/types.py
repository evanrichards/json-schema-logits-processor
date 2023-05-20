
from dataclasses import dataclass


@dataclass
class PartialValidationResult:
    valid: bool
    rest: str
    value: str
    complete: bool

WHITESPACE = " \t\n\r"
