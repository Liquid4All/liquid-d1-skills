# Open-weight d1 inference

Sources, checked 2026-10-20:

- https://docs.liquid.ai/lfm/models/d1-3b
- https://docs.liquid.ai/lfm/models/d1-omni-600m

Examples below are adapted from those pages. They have not been tested against
loaded model weights in this repository. Check current runtime requirements
and model cards before installing; hosted authentication, billing, rate limits,
and payload limits do not describe local runtime behavior.

## Select a model and format

| Model | Context | Modalities | Weights |
| --- | --- | --- | --- |
| `LiquidAI/d1-3B` | 32K | Text, images | [HF](https://huggingface.co/LiquidAI/d1-3B), [GGUF](https://huggingface.co/LiquidAI/d1-3B-GGUF), [MLX 8-bit](https://huggingface.co/LiquidAI/d1-3B-MLX-8bit) |
| `LiquidAI/d1-omni-600M` | 16K | Text with images or audio | [HF](https://huggingface.co/LiquidAI/d1-omni-600M), [GGUF](https://huggingface.co/LiquidAI/d1-omni-600M-GGUF), [MLX 8-bit](https://huggingface.co/LiquidAI/d1-omni-600M-MLX-8bit) |

The model pages also link other quantizations. MLX runs on Apple Silicon via
mlx-vlm. The documentation says d1 support landed after mlx-vlm 0.7.6 and calls
for installation from GitHub until a supporting release; check the current
model card for Python, CLI, and server instructions.

The weights use the [LFM Open License](https://docs.liquid.ai/lfm/help/model-license);
the skill repository's MIT license applies to its code and documentation.

## Transformers: text and images

For d1-3B:

```bash
pip install "transformers>=5.14" torch accelerate torchvision pillow
```

For omni (including audio):

```bash
pip install "transformers>=5.15" torch accelerate torchvision pillow soundfile
```

Run this example with either model. Use an accelerator supported by the chosen
dtype and runtime; these are the dtypes used in Liquid's examples.

```python
from PIL import Image
from transformers import AutoModel

model_id = "LiquidAI/d1-3B"
# For omni instead:
# model_id = "LiquidAI/d1-omni-600M"
dtype = "float16" if model_id.endswith("600M") else "bfloat16"
model = AutoModel.from_pretrained(
    model_id, trust_remote_code=True, dtype=dtype, device_map="auto",
)
questions = {
    "refund": {"type": "noul", "instructions": "Is the customer asking for a refund?"},
    "team": {
        "type": "choice",
        "instructions": "Which team should handle this?",
        "criteria": {"billing": "Charges and refunds", "technical": "Bugs and outages"},
    },
    "urgency": {
        "type": "score",
        "instructions": "How urgent is this?",
        "criteria": ["Can wait", "Today", "Blocking the customer now"],
    },
}
print(model.system_one("I was charged twice. Please refund one charge.", questions))

with Image.open("image.jpg") as photo:
    image_questions = {
        "damaged": {"type": "noul", "instructions": "Is the item visibly damaged?"},
    }
    print(model.system_one(None, image_questions, images=[photo]))
```

## Transformers: omni audio

Use 16 kHz mono audio lasting 0.5–30 seconds. This is text with audio input;
do not assume simultaneous image and audio input is supported.

```python
import soundfile as sf
from transformers import AutoModel

model = AutoModel.from_pretrained(
    "LiquidAI/d1-omni-600M", trust_remote_code=True,
    dtype="float16", device_map="auto",
)
wave, rate = sf.read("command.wav", dtype="int16")
assert rate == 16000 and wave.ndim == 1
assert 0.5 <= len(wave) / rate <= 30
questions = {
    "kind": {
        "type": "choice",
        "instructions": "What kind of utterance is this?",
        "criteria": {"request": "A request", "question": "Asking for information", "other": "Other speech"},
    },
}
print(model.system_one(None, questions, audio=wave))
```

## MLX: Apple Silicon

Follow the decision-specific sections of the linked model cards, rather than
Hugging Face's generic generated-text usage snippets. Install a d1-capable
mlx-vlm version; the cards currently specify:

```bash
pip install -U git+https://github.com/Blaizzy/mlx-vlm.git
```

Both models expose decisions through `predict`:

```python
from mlx_vlm import load, predict

model_id = "LiquidAI/d1-3B-MLX-8bit"
# For omni instead:
# model_id = "LiquidAI/d1-omni-600M-MLX-8bit"
model, processor = load(model_id)
questions = {
    "refund": {"type": "noul", "instructions": "Is the customer asking for a refund?"},
}
result = predict(model, processor, "I was charged twice. Please refund one charge.", questions)
print(result["answers"])

image_questions = {
    "damaged": {"type": "noul", "instructions": "Is the item visibly damaged?"},
}
print(predict(model, processor, None, image_questions, images=["image.jpg"]))
# With omni loaded, a 16 kHz mono WAV lasting 0.5–30 s:
# print(predict(model, processor, None,
#     {"question": {"type": "noul", "instructions": "Is the speaker asking a question?"}},
#     audio="command.wav"))
```

MLX answer fields differ from hosted System One: Choice and Score use `value`,
Noul uses `probability`, and Choice confidence is under `metadata.confidence`.
The documented mlx-vlm server exposes `/v1/decisions`; the bundled runner
appends `/v1/systemone` and therefore does not directly target that MLX route.
Use `predict` or the model card's MLX server examples instead.

## llama.cpp: local HTTP

Both model pages require llama.cpp 0.7.0 or later; older builds may report
`unsupported decision model type`. Start one model at a time:

```bash
llama-server -hf LiquidAI/d1-3B-GGUF:Q8_0
```

Or:

```bash
llama-server -hf LiquidAI/d1-omni-600M-GGUF:Q8_0 -b 4096 -ub 4096
```

The loaded weights select the model. Unlike hosted requests, the documented
local request omits `model`. Save this as `request.json`:

```json
{
  "state": "I was charged twice. Please refund one charge.",
  "questions": {
    "refund": {"type": "noul", "instructions": "Is the customer asking for a refund?"}
  }
}
```

Call it directly, or use the bundled runner from the repository root:

```bash
curl http://127.0.0.1:8080/v1/systemone \
  -H 'Content-Type: application/json' --data-binary @request.json

LIQUID_BASE_URL=http://127.0.0.1:8080 LIQUID_API_KEY= \
  python3 skills/liquid-d1/scripts/d1.py request.json
```

Set `LIQUID_API_KEY` only if the configured local server requires a bearer
token. The runner passes request bodies unchanged. Its default demo contains
hosted `model: "d1"`, so use a request file or stdin for local inference.
`--models` works only if the server implements `GET /v1/models`.

For images, both model pages use an `images` array of Base64 image data URLs.
For omni audio, the llama.cpp example uses a `files` array of Base64 WAV data
URLs. This differs from Transformers' `audio=wave` argument. With the
appropriate server running, choose one media example below and pipe to the
runner:

```bash
python3 - <<'PY' | LIQUID_BASE_URL=http://127.0.0.1:8080 LIQUID_API_KEY= python3 skills/liquid-d1/scripts/d1.py -
import base64
import json
from pathlib import Path

# Image input works with either model.
field, mime, path = "images", "image/jpeg", "image.jpg"
question = "Is the item visibly damaged?"
# For omni audio instead, use a 16 kHz mono WAV lasting 0.5–30 s:
# field, mime, path = "files", "audio/wav", "command.wav"
# question = "Is the speaker asking a question?"
encoded = base64.b64encode(Path(path).read_bytes()).decode("ascii")
print(json.dumps({
    "state": None,
    field: [f"data:{mime};base64,{encoded}"],
    "questions": {"check": {"type": "noul", "instructions": question}},
}))
PY
```

Inspect the actual local result when integrating; do not assume hosted usage,
cost fields, or provider metadata are returned by every runtime.
