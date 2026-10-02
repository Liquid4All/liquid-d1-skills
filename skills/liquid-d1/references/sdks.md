# Calling d1 from code

This file covers Liquid's first-party endpoint with the TypeSafe-compatible
SDKs and plain HTTP. For Vercel AI Gateway and OpenRouter, see `providers.md`;
do not mix credentials or model IDs between providers.

Liquid's decision endpoint implements the System One API, so the TypeSafe SDK
clients work against it once the base URL points at
`https://api.liquid.ai/decisions` and the model is `d1`.
d1 remains a Liquid AI model; the SDK is a compatible client. Nothing else
Liquid-specific is required beyond those settings and a Liquid API key.

SDK details below were taken from https://docs.typesafe.ai/sdk/python.md,
https://docs.typesafe.ai/sdk/python/usage.md, and
https://docs.typesafe.ai/sdk/javascript.md (JS SDK v0.6.0). Check those pages
for the current version before pinning anything.

## curl

```bash
curl https://api.liquid.ai/decisions/v1/systemone \
  -H "Authorization: Bearer $LIQUID_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "d1",
    "state": "Help! My payouts have been failing for 3 days.",
    "questions": {
      "department": {
        "type": "choice",
        "instructions": "Which team should handle this?",
        "criteria": { "billing": "Payments", "technical": "Bugs, outages", "sales": "Pricing" }
      },
      "is_urgent": { "type": "noul", "instructions": "Does this convey urgency?" }
    }
  }'
```

List available models with `GET /decisions/v1/models`.

## Python (typesafe-sdk)

```sh
pip install typesafe-sdk        # or: uv add typesafe-sdk
```

The client reads `TYPESAFE_API_KEY`, `TYPESAFE_BASE_URL`, and
`TYPESAFE_DEFAULT_MODEL` from the environment. Either set those to Liquid
values or pass them explicitly. Explicit values are clearer in application
code:

```python
import os

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

client = TypeSafeClient(
    api_key=os.environ["LIQUID_API_KEY"],
    base_url="https://api.liquid.ai/decisions",
    model="d1",
)

result = client.system_one(
    {"ticket": "Help! My payouts have been failing for 3 days."},
    {
        "department": Choice(
            instructions="Which team should handle `ticket`?",
            criteria={
                "billing": "Payments, invoicing, refunds",
                "technical": "Bugs, outages, integrations",
                "sales": "Pricing, upgrades, new accounts",
            },
        ),
        "is_urgent": Noul(instructions="Does `ticket` convey urgency?"),
        "frustration": Score(
            instructions="How frustrated is the customer in `ticket`?",
            criteria=["Calm", "Frustrated", "Very angry"],
        ),
    },
)

print(result.choices["department"].choice)         # "technical"
print(result.choices["department"].probabilities)  # {"billing": 0.31, ...}
print(result.choices["department"].confidence)
print(result.nouls["is_urgent"].noul)              # 0.95
print(result.scores["frustration"].score)          # 1.05
```

Answers are grouped by type on the result: `result.choices`, `result.scores`,
`result.nouls`, each keyed by question id. `result.request_id` and
`result.raw_http_response` are available for debugging.

Async client, same shape:

```python
from typesafe_sdk import AsyncTypeSafeClient

async with AsyncTypeSafeClient(
    api_key=os.environ["LIQUID_API_KEY"],
    base_url="https://api.liquid.ai/decisions",
    model="d1",
) as client:
    result = await client.system_one(state, questions)
```

Typed responses, when the answer set is fixed:

```python
from typesafe_sdk import ChoiceAnswer, NoulAnswer, SystemOneResponse

class TicketAnswers(SystemOneResponse):
    department: ChoiceAnswer
    is_urgent: NoulAnswer

result = client.system_one(state, questions, response_model=TicketAnswers)
result.department.choice
```

Retries and errors:

```python
from typesafe_sdk import RetryPolicy, TypeSafeAPIError

client = TypeSafeClient(
    api_key=os.environ["LIQUID_API_KEY"],
    base_url="https://api.liquid.ai/decisions",
    model="d1",
    retry=RetryPolicy(max_retries=3, backoff_max=0.2, timeout=1.0),
)

try:
    client.system_one(state, questions)
except TypeSafeAPIError as error:
    print(error.status, error.request_id)
```

Raw question dictionaries are accepted in place of the `Choice`/`Score`/`Noul`
helpers, which is useful when questions live in config:

```python
client.system_one(state, {"is_urgent": {"type": "noul", "instructions": "..."}})
```

Add the `http2` extra (`typesafe-sdk[http2]`) and pass
`http_client=httpx2.Client(http2=True)` when sending many concurrent
requests.

## TypeScript / JavaScript (@typesafe-ai/sdk)

```sh
npm install @typesafe-ai/sdk      # Node.js 20+
```

Constructor options are `apiKey`, `baseURL`, `defaultModel`, `timeout`,
`retry`, `defaultHeaders`, `fetch`, `logLevel`, `logger`. Environment
fallbacks are `TYPESAFE_API_KEY`, `TYPESAFE_BASE_URL`, `TYPESAFE_DEFAULT_MODEL`.
The client refuses to run in a browser unless `dangerouslyAllowBrowser: true`
is passed; keep it on the server.

```ts
import { choice, noul, score, TypeSafeClient } from "@typesafe-ai/sdk";

const client = new TypeSafeClient({
  apiKey: process.env.LIQUID_API_KEY,
  baseURL: "https://api.liquid.ai/decisions",
  defaultModel: "d1",
});

const { answers, usage } = await client.systemOne({
  state: { ticket: "Help! My payouts have been failing for 3 days." },
  questions: {
    department: choice("Which team should handle `ticket`?", {
      billing: "Payments, invoicing, refunds",
      technical: "Bugs, outages, integrations",
      sales: "Pricing, upgrades, new accounts",
    }),
    isUrgent: noul("Does `ticket` convey urgency?"),
    frustration: score("How frustrated is the customer in `ticket`?", [
      "Calm",
      "Frustrated",
      "Very angry",
    ]),
  },
});

answers.department.choice;         // "billing" | "technical" | "sales"
answers.department.probabilities;  // Record<option, number>
answers.department.confidence;
answers.isUrgent.noul;             // number in [0, 1]
answers.frustration.score;         // number, may fall between levels
```

Answer types are inferred from the question literals, so `answers.department.choice`
is a union of the option names. `choice()` takes a map of option to description
(or `null`); `score()` takes an ordered array indexed from 0; `noul()` takes
optional `{ true, false }` criteria.

Per-call options (second argument to `systemOne`): `timeout`, `retry`,
`headers`, `signal`. Errors: `APIError` (non-2xx after retries, has `status`),
`APIConnectionError`, `APITimeoutError`, `APIUserAbortError`, and
`TypeSafeError` for local validation. The default retry policy honors
`Retry-After`, which is what Liquid sends on 429.

```ts
import { APIError } from "@typesafe-ai/sdk";

try {
  await client.systemOne({ state, questions });
} catch (err) {
  if (err instanceof APIError && err.status === 429) {
    // Retries were already exhausted; back off at the application level.
  }
  throw err;
}
```

List models: `await client.models.list()`.

## Plain HTTP from any language

Any HTTP client works. The request is a single JSON POST; see
`references/api.md` for the exact contract and `scripts/d1.py` for a
dependency-free Python example that also serves as a smoke test.

## Where to put questions and thresholds

Keep questions, criteria, and any probability or confidence thresholds in one
module or config file. They are the part humans most need to review, and they
change more often than the surrounding code. Questions written by an agent
usually need a human editing pass.
