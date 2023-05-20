from json_schema_logits_processor.incremental_parser.string_parser import \
    is_valid_string
from json_schema_logits_processor.incremental_parser.types import \
    PartialValidationResult
from json_schema_logits_processor.schema import EnumJsonSchema


def is_valid_enum(
    partial_json: str, enum_schema: EnumJsonSchema
) -> PartialValidationResult:
    out = is_valid_string(partial_json)
    if not out.complete:
        valid = (
            any(value.startswith(out.value) for value in enum_schema.values)
            and out.valid
        )
        return PartialValidationResult(
            valid=valid,
            rest=out.rest,
            value=out.value,
            complete=out.complete,
        )
    return PartialValidationResult(
        valid=out.valid and out.value in enum_schema.values,
        rest=out.rest,
        value=out.value,
        complete=out.complete,
    )
