import torch
from transformers import BartTokenizer, EncoderDecoderModel

from json_schema_logits_processor import JsonSchemaLogitsProcessor
from json_schema_logits_processor.schema.interative_schema import \
    parse_schema_from_string

bart_tokenizer = BartTokenizer.from_pretrained("facebook/bart-base")

schema = parse_schema_from_string(
    """
  {
    "type": "object",
    "properties": {
      "artifactType": {
        "type": "string"
      },
      "originLocation": {
        "type": "string"
      },
      "other": {
        "type": "string"
      }
    }
  }
  """
)

logits_processor = JsonSchemaLogitsProcessor(
    schema=schema, tokenizer=bart_tokenizer, verbose=True
)

model = EncoderDecoderModel.from_pretrained("looppayments/layout-bart-summary")

model.config.decoder_start_token_id = model.config.decoder.decoder_start_token_id
model.config.pad_token_id = model.config.decoder.pad_token_id
model.config.max_length = 1024


# Make sure your model is in the right device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# Initialize the tokenizer for BART (decoder)
input_ids = torch.tensor(bart_tokenizer.encode("", add_special_tokens=True)).unsqueeze(
    0
)  # Batch size 1

output = model.generate(
    input_ids,
    logits_processor=[logits_processor],
    max_length=200,
)
print(bart_tokenizer.batch_decode(output, skip_special_tokens=True))
