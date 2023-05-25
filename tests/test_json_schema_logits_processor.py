import re

import pytest
import torch
from transformers import BartTokenizer

from json_schema_logits_processor import JsonSchemaLogitsProcessor
from json_schema_logits_processor.schema.interative_schema import \
    parse_schema_from_string


@pytest.fixture
def tokenizer() -> BartTokenizer:
    return BartTokenizer.from_pretrained("facebook/bart-base")


@pytest.fixture
def decoded_tokens(tokenizer) -> list[str]:
    return tokenizer.batch_decode(
        torch.arange(tokenizer.vocab_size), skip_special_tokens=True
    )


test_data = '</s><s>{"a": "b"}</s><pad>'


def test_end_to_end(tokenizer, decoded_tokens):
    processor = JsonSchemaLogitsProcessor(
        schema=parse_schema_from_string(
            '{"type": "object", "properties": {"a": {"type": "string"}}}'
        ),
        tokenizer=tokenizer,
    )
    input_ids = torch.tensor(
        tokenizer.encode(test_data, add_special_tokens=False)
    ).unsqueeze(0)
    decoded = tokenizer.batch_decode(input_ids, skip_special_tokens=False)
    test_logits = torch.tensor([0.0] * tokenizer.vocab_size).unsqueeze(0)
    for i in range(7, len(input_ids[0])):
        test_input_ids = input_ids[:, :i]
        assert isinstance(test_input_ids, torch.LongTensor)
        assert isinstance(test_logits, torch.FloatTensor)
        processed_logits = processor(input_ids=test_input_ids, scores=test_logits)
        # get the tokens where the logit value is still 0.0
        valid_tokens = [
            decoded_tokens[i]
            for i, logit in enumerate(processed_logits[0])
            if logit == 0.0
        ]
        decoded = tokenizer.batch_decode(test_input_ids, skip_special_tokens=False)
        next_token = input_ids[0][i]
        assert processed_logits[0][next_token] == 0, (
            f"current text: {decoded}, next token: ({next_token}) '{decoded_tokens[next_token]}', "
            f"processed_logits: {processed_logits[0][next_token]}, "
            f"starting at index {i}"
        )
        print(f"current text: {decoded}, next token: {next_token}")
        print(len(valid_tokens))
