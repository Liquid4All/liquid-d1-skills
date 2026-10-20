# Liquid direct decision API reference

Sources: https://docs.liquid.ai/lfm/models/d1 and
https://console.liquid.ai/docs (Decision models group). Model and image support
were refreshed on 2026-10-20. Numeric validation limits and error details below
come from the console snapshot captured on 2026-09-29; recheck the live contract
before relying on those limits. They apply to the hosted API, not local servers.

## Base URLs

This file describes Liquid's first-party endpoint. For Vercel AI Gateway and
OpenRouter endpoints, model IDs, and credentials, see `providers.md`.

| Purpose | Base URL |
| --- | --- |
| Decision models (d1) | `https://api.liquid.ai/decisions` |
| OpenAI-compatible chat, embeddings, files, batches (LFM models) | `https://api.liquid.ai/openai/v1` |

For current TypeSafe SDK configuration, use the Liquid examples in `sdks.md`.
The SDK base URL is `https://api.liquid.ai`; raw HTTP uses the full route above.

## Authentication

`Authorization: Bearer $LIQUID_API_KEY`. Keys are created on the console's API
keys page (`/dashboard/api-keys`), shown once, belong to the organization, and
can be revoked at any time.

## POST /decisions/v1/systemone

Implements the System One API. d1 is developed and owned by Liquid AI; System
One describes the compatible request and response contract. Send a state and a
map of typed questions; get one structured answer per question, read from the
model's probabilities in one forward pass with no generated tokens.

### Request body

| Field | Required | Description |
| --- | --- | --- |
| `model` | yes | Hosted model ID: `"d1"` or `"d1-ultra"`. |
| `questions` | yes | Object of named questions (the older console snapshot lists up to 128). Answers come back under the same keys. |
| `state` | no | What the questions are about: plain text or structured JSON (a chat log, a record). Omit or send `null` when the questions stand alone. |
| `images` | no | Supported by both `d1` and `d1-ultra`. Each is a Base64 image data URL or an object with `content_type` and `base64` fields. Remote image URLs are not accepted; download and encode them first. Every question evaluates all supplied images. Check the live contract for image count, format, size, and total body limits. |

### Question shapes

Every question has a `type` and `instructions` (a string or JSON).

| Type | `criteria` |
| --- | --- |
| `choice` | Object mapping 2 to 255 option names to a description or `null`. |
| `score` | Ordered array of 2 to 10 level descriptions, indexed from 0. |
| `noul` | Optional `{ "true": ..., "false": ... }`, used only when both are given and say more than a bare yes and no. |

Each question is its own prompt carrying the whole state, and usage counts
each one. The older hosted console snapshot lists 32,768 tokens and 256 KiB per prompt
and 422 above either. Verify current limits for the selected hosted model.
Both hosted models use the same endpoint, question types, and response format.
Audio input is documented for local `d1-omni-600M`, not this hosted API.

### Response

| Field | Description |
| --- | --- |
| `model` | The model that answered. |
| `answers` | One answer per question id. |
| `usage` | `{ "input_tokens", "output_tokens" }` plus `cost` in USD when the model is priced. `output_tokens` is always 0. |

Answer shapes:

| Type | Fields |
| --- | --- |
| `choice` | `choice` (selected option name), `probabilities` (per option), `confidence` |
| `score` | `score` (probability-weighted; may fall between levels), `legend` (index to level text), `probabilities` (per level index), `confidence` |
| `noul` | `noul` (probability of yes) |

`confidence` runs from 0 (probability spread evenly) to 1 (all on one answer).

### Example

Request:

```json
{
  "model": "d1",
  "state": "Help! My payouts have been failing for 3 days.",
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which team should handle this?",
      "criteria": {
        "billing": "Payments, invoicing, refunds",
        "technical": "Bugs, outages, integrations",
        "sales": "Pricing, upgrades, new accounts"
      }
    },
    "is_urgent": { "type": "noul", "instructions": "Does this convey urgency?" },
    "frustration": {
      "type": "score",
      "instructions": "How frustrated is the customer?",
      "criteria": ["Calm", "Frustrated", "Very angry"]
    }
  }
}
```

Response (200):

```json
{
  "model": "d1",
  "answers": {
    "department": {
      "type": "choice",
      "choice": "technical",
      "probabilities": { "billing": 0.31, "technical": 0.67, "sales": 0.02 },
      "confidence": 0.5
    },
    "is_urgent": { "type": "noul", "noul": 0.95 },
    "frustration": {
      "type": "score",
      "score": 1.05,
      "legend": { "0": "Calm", "1": "Frustrated", "2": "Very angry" },
      "probabilities": { "0": 0, "1": 0.95, "2": 0.05 },
      "confidence": 0.92
    }
  },
  "usage": { "input_tokens": 912, "output_tokens": 0 }
}
```

### Status codes

| Code | Meaning |
| --- | --- |
| 200 | Success. |
| 401 | Missing or invalid API key. |
| 422 | Validation error: bad question shape, prompt exceeding the selected model's current limits, unsupported media or unknown fields. |
| 429 | Organization/model request limit exceeded (see `Retry-After`), or the model has no healthy inference target (error code `model_unavailable`). |

### Rate limiting

Requests share an organization/model sliding-window limit across API keys and
sessions. Locally checked responses include:

- `x-ratelimit-limit-requests`
- `x-ratelimit-remaining-requests`
- `x-ratelimit-reset-requests` (an integral duration such as `42s`)

A request over the limit returns 429 with `Retry-After`. Invalid, unauthorized,
unknown-model, and unavailable-model requests do not consume quota.

## GET /decisions/v1/models

Lists the decision models the organization can pass as `model`. These are
separate from the OpenAI-compatible model list.

Use the actual response to discover hosted model availability for the organization;
do not treat a bundled example as an exhaustive model list. Local servers may
not implement this route or return the same metadata.
