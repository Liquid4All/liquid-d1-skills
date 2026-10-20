# Calling hosted d1 from code

Source: https://docs.liquid.ai/lfm/models/d1 (checked 2026-10-20).
These examples follow Liquid's current SDK configuration. Use `d1-ultra`
in place of `d1` for harder decisions. For gateway calls read `providers.md`;
for open weights read `local-inference.md`.

The shared System One contract does not imply identical SDK versions or
constructor settings. Check the installed SDK against the current Liquid docs.
The current SDK examples support text; use raw HTTP for images.

## Python (typesafe-sdk)

```sh
pip install typesafe-sdk
```

```python
import os
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

client = TypeSafeClient(
    api_key=os.environ["LIQUID_API_KEY"],
    base_url="https://api.liquid.ai",
)
result = client.system_one(
    model="d1",
    state="I was charged twice this month. Please refund one charge.",
    questions={
        "team": Choice(
            instructions="Which team should handle this?",
            criteria={"billing": "Charges and refunds", "technical": "Bugs and outages"},
        ),
        "refund": Noul(instructions="Is the customer asking for a refund?"),
        "urgency": Score(
            instructions="How urgent is this?",
            criteria=["Can wait", "Handle today", "Blocking the customer now"],
        ),
    },
)
print(result.answers["team"].choice)
print(result.answers["team"].probabilities)
print(result.answers["team"].confidence)
print(result.answers["refund"].noul)
print(result.answers["urgency"].score)
```

## TypeScript / JavaScript (@typesafe-ai/sdk)

```sh
npm install @typesafe-ai/sdk
```

```ts
import { TypeSafeClient } from "@typesafe-ai/sdk";

const client = new TypeSafeClient({
  apiKey: process.env.LIQUID_API_KEY!,
  baseURL: "https://api.liquid.ai",
  compression: false, // Liquid does not accept zstd-compressed request bodies.
});
const result = await client.systemOne({
  model: "d1",
  state: "I was charged twice this month. Please refund one charge.",
  questions: {
    team: {
      type: "choice",
      instructions: "Which team should handle this?",
      criteria: { billing: "Charges and refunds", technical: "Bugs and outages" },
    },
    refund: { type: "noul", instructions: "Is the customer asking for a refund?" },
    urgency: {
      type: "score",
      instructions: "How urgent is this?",
      criteria: ["Can wait", "Handle today", "Blocking the customer now"],
    },
  },
});
console.log(result.answers.team.choice);
console.log(result.answers.refund.noul);
console.log(result.answers.urgency.score);
```

## Raw HTTP: text or images

Keep keys on the server. Every question is billed for its text and all supplied
images. Remote image URLs are not accepted by the hosted endpoint.

This dependency-free example uses the bundled runner and encodes `image.jpg`:

```bash
python3 - <<'PY' | python3 skills/liquid-d1/scripts/d1.py -
import base64
import json
from pathlib import Path

image = base64.b64encode(Path("image.jpg").read_bytes()).decode("ascii")
print(json.dumps({
    "model": "d1",
    "state": "Inspect the attached image.",
    "images": ["data:image/jpeg;base64," + image],
    "questions": {"damaged": {"type": "noul", "instructions": "Is the item visibly damaged?"}},
}))
PY
```

For a text-only request, omit `images`. For any language, POST the JSON body to
`https://api.liquid.ai/decisions/v1/systemone` with
`Authorization: Bearer $LIQUID_API_KEY` and `Content-Type: application/json`.
Read `api.md` for the wire contract and hosted errors.

## Runner and configuration

Paths in these shell examples assume the repository root; resolve the runner
relative to the installed skill directory when using an installed copy.

```bash
python3 skills/liquid-d1/scripts/d1.py              # hosted d1 demo
python3 skills/liquid-d1/scripts/d1.py request.json # body passed unchanged
python3 skills/liquid-d1/scripts/d1.py --models     # hosted model discovery
```

`LIQUID_BASE_URL` defaults to `https://api.liquid.ai/decisions`; the runner
appends `/v1/systemone` or `/v1/models`. This differs from the SDK base URL.
Custom servers may omit authentication. If `LIQUID_API_KEY` is set, the runner
sends it as a bearer token to the configured server. Model discovery requires
the server to implement `GET /v1/models`.

Keep questions, criteria, and thresholds in one module or config file so they
can be reviewed and tuned against representative application data.
