from dataclasses import dataclass
from typing import Callable

import torch
from transformers import LogitsProcessor, PreTrainedTokenizer

from json_schema_logits_processor.incremental_parser import \
    parse_partial_json_value
from json_schema_logits_processor.incremental_parser.types import \
    PartialValidationResult
from json_schema_logits_processor.schema import JsonSchema


@dataclass
class TrieNode:
    id: int | None = None
    is_root: bool = False

    def __init__(self):
        self.children = {}


class Trie:
    def __init__(self):
        self.root = TrieNode()
        self.root.is_root = True

    def insert(self, token: str, id: int):
        node = self.root
        for char in token:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.id = id

    def _search_for_valid_token_ids(
        self,
        prefix: str,
        node: TrieNode,
        is_valid: Callable[[str], PartialValidationResult],
        valid_token_ids: list[int],
    ):
        partial_validation_result = False
        if not node.is_root:
            partial_validation_result = is_valid(prefix)
        if node.is_root or partial_validation_result:
            if node.id is not None:
                valid_token_ids.append(node.id)
            for letter, child_node in node.children.items():
                new_prefix = prefix + letter
                self._search_for_valid_token_ids(
                    new_prefix, child_node, is_valid, valid_token_ids
                )

    def find_valid_tokens(self, prefix, is_valid):
        valid_tokens = []
        self._search_for_valid_token_ids(prefix, self.root, is_valid, valid_tokens)
        return valid_tokens


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
        self.decoded_token_tree = self._build_decoded_token_tree()

    def _build_decoded_token_tree(self):
        trie = Trie()
        for i, token in enumerate(self.decoded_tokens):
            trie.insert(token, i)
        return trie

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
        valid_tokens_ids = self.decoded_token_tree.find_valid_tokens(
            text, lambda x: is_valid_partial_json_for_schema(x, self.schema)
        )
        return valid_tokens_ids


def is_valid_partial_json_for_schema(
    partial_json: str,
    schema: JsonSchema,
) -> bool:
    out = parse_partial_json_value(partial_json, schema)
    return out.valid and out.rest.strip() == ""
