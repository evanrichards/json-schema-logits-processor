# JSON Schema Logits Processor

The JSON Schema Logits Processor is a Python tool that uses PyTorch and the Transformers library to process logits based on a given JSON Schema. The tool is designed to process sequences of tokens and determine which tokens would be valid next according to a given schema.

## Features

Uses `JsonSchemaLogitsProcessor`, a class that inherits from LogitsProcessor in the Transformers library.
Utilizes a tokenizer from the Transformers library.
Decodes input sequences and determines the next valid tokens based on the JSON schema.
Includes a method for validating partial JSON against a given schema.

## Usage

The main class in this tool is JsonSchemaLogitsProcessor. An instance of this class can be created with a JsonSchema object and a PreTrainedTokenizer object.

```python
from json_schema_logits_processor.schema import JsonSchema
from transformers import PreTrainedTokenizer
from json_schema_logits_processor.json_schema_logits_processor import JsonSchemaLogitsProcessor
from json_schema_logits_processor.schema import parse_schema_from_string

schema = parse_schema_from_string(
    '{"type": "object", "properties": {"a": {"type": "string"}}}'
)

# Assuming `schema` is a JsonSchema object and `tokenizer` is a PreTrainedTokenizer object
processor = JsonSchemaLogitsProcessor(schema, tokenizer)
```

Usage in transformers models:

```python

output = model.generate(*inputs, logits_processor=[logits_processor])

```

The processor decodes the input sequence and determines the next valid tokens based on the JSON schema. The returned tensor contains the scores for the valid tokens and a very low score for invalid tokens.

### Dependencies

- PyTorch
- Transformers

### Disclaimer

Please note that this project is a work in progress and the functionality may change over time.

For more information, please review the source code or contact the author. Contributions and suggestions are welcome!

Contact
Evan Richards

- Github: @evanrichards

### License

mit
