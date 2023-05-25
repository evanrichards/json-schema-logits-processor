from dataclasses import dataclass
from typing import Callable

import torch
from transformers import LogitsProcessor, PreTrainedTokenizer

from json_schema_logits_processor.iterative_parser import \
    parse_partial_json_value
from json_schema_logits_processor.iterative_parser.types import \
    IterativeParserResult
from json_schema_logits_processor.schema.interative_schema import JsonSchema


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
        next_token: str,
        node: TrieNode,
        is_valid: Callable[[str, str], bool],
        valid_token_ids: list[int],
    ):
        stack = [(prefix, next_token, node)]  # Create a stack with the initial state
        while stack:  # While the stack is not empty
            prefix, next_token, node = stack.pop()

            partial_validation_result = None
            if not node.is_root:
                partial_validation_result = is_valid(prefix, next_token)
            if node.id == 48805:
                print("it does exist", partial_validation_result, prefix, next_token)
                assert False
            if next_token == '"':
                print(
                    "hello",
                    f"'{prefix}'",
                    f"letter: '{next_token}'",
                    node.id,
                    partial_validation_result,
                )
            new_prefix = prefix + next_token

            if partial_validation_result is False:
                continue
            for letter, child_node in node.children.items():
                if letter == '"':
                    print(
                        "hi",
                        f"'{new_prefix}'",
                        f"letter: '{letter}'",
                        node.id,
                        child_node.id,
                    )

                stack.append(
                    (new_prefix, letter, child_node)
                )  # Add children to the stack

            if node.id is not None:
                valid_token_ids.append(node.id)

    def find_valid_tokens(self, prefix: str, is_valid: Callable[[str, str], bool]):
        valid_tokens = []
        self._search_for_valid_token_ids("", prefix, self.root, is_valid, valid_tokens)
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
            text,
            lambda prefix, next_token: is_valid_partial_json_for_schema(
                prefix, next_token, self.schema
            ),
        )
        return valid_tokens_ids


def is_valid_partial_json_for_schema(
    prefix: str,
    next_token: str,
    schema: JsonSchema,
) -> bool:
    print("is_valid_partial_json_for_schema", prefix, next_token)
    out = parse_partial_json_value(prefix, next_token, schema)
    return out.valid
