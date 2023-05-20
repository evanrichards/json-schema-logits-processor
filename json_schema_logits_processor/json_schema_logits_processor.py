import torch
from transformers import LogitsProcessor, PreTrainedTokenizer

from json_schema_logits_processor.incremental_parser import \
    parse_partial_json_value
from json_schema_logits_processor.schema import JsonSchema


class JsonSchemaLogitsProcessor(LogitsProcessor):
    def __init__(
        self, schema: JsonSchema, tokenizer: PreTrainedTokenizer, verbose: bool = False
    ):
        super().__init__()
        self.verbose = verbose
        self.schema = schema
        self.tokenizer = tokenizer
        self.bos_token_id = tokenizer.bos_token_id
        self.padding_token_id = tokenizer.pad_token_id
        self.eos_token_id = tokenizer.eos_token_id
        self.decoded_tokens = self.tokenizer.batch_decode(
            torch.arange(self.tokenizer.vocab_size), skip_special_tokens=True
        )

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor):
        # Decode the text so far.
        text_batch = self.tokenizer.batch_decode(input_ids, skip_special_tokens=True)
        # Determine which tokens would be valid next.
        return_tensor = torch.full_like(scores, -1e10, dtype=torch.float32)
        for i, text in enumerate(text_batch):
            if (
                self.padding_token_id is not None
                and input_ids[i][-1] == self.padding_token_id
            ) or (
                self.eos_token_id is not None and input_ids[i][-1] == self.eos_token_id
            ):
                return_tensor[i] = scores[i]
                continue
            valid_tokens = self._get_next_valid_tokens(text)

            if self.verbose:
                print(f"input_ids[{i}] = {text}, valid_tokens = {len(valid_tokens)}")
            if len(valid_tokens) == 0:
                valid_tokens = [self.eos_token_id, self.padding_token_id]
            invalid_tensor = torch.full_like(scores[i], -1e10, dtype=torch.float32)
            # set the original scores for the valid tokens in the new tensor
            invalid_tensor[valid_tokens] = scores[i][valid_tokens]
            return_tensor[i] = invalid_tensor
        return return_tensor

    def _get_next_valid_tokens(self, text: str) -> list[int]:
        valid_tokens = []
        for token_id in range(self.tokenizer.vocab_size):
            token = self.decoded_tokens[token_id]
            if is_valid_partial_json_for_schema(text + token, self.schema):
                valid_tokens.append(token_id)
        return valid_tokens


def is_valid_partial_json_for_schema(
    partial_json: str,
    schema: JsonSchema,
) -> bool:
    out = parse_partial_json_value(partial_json, schema)
    return out.valid and out.rest.strip() == ""
