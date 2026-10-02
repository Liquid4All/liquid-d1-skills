# Liquid direct decision API reference

Source: https://console.liquid.ai/docs (Decision models group). The console
also publishes the full reference as Markdown, OpenAPI JSON, and OpenAPI YAML.
Verify against the live page before relying on anything below; it was
captured on 2026-09-29.

## Base URLs

This file describes Liquid's first-party endpoint. For Vercel AI Gateway and
OpenRouter endpoints, model IDs, and credentials, see `providers.md`.

| Purpose | Base URL |
| --- | --- |
| Decision models (d1) | `https://api.liquid.ai/decisions` |
| OpenAI-compatible chat, embeddings, files, batches (LFM models) | `https://api.liquid.ai/openai/v1` |

TypeSafe SDKs work unchanged with their base URL set to
`https://api.liquid.ai/decisions`.

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
| `model` | yes | Decision model id, e.g. `"d1"`. |
| `questions` | yes | Object of up to 128 named questions. Answers come back under the same keys. |
| `state` | no | What the questions are about: plain text or structured JSON (a chat log, a record). Omit or send `null` when the questions stand alone. |
| `images` | no | Up to 8 images, only for image-capable decision models (such as LFM2.5-S1-VL). d1 returns 422. Each is a `data:image/...;base64,` URL or `{ "content_type", "base64" }`; JPEG, PNG, WebP, or GIF; 5 MB each within the 4.5 MB request body limit. Images precede the state in the prompt, in the order sent, and every question sees all of them. This is an endpoint extension to the core System One contract; omit it for portable System One requests. |

### Question shapes

Every question has a `type` and `instructions` (a string or JSON).

| Type | `criteria` |
| --- | --- |
| `choice` | Object mapping 2 to 255 option names to a description or `null`. |
| `score` | Ordered array of 2 to 10 level descriptions, indexed from 0. |
| `noul` | Optional `{ "true": ..., "false": ... }`, used only when both are given and say more than a bare yes and no. |

Each question is its own prompt carrying the whole state, and usage counts
each one. `d1` caps each prompt at 32,768 tokens and 256 KiB and returns 422
over either.

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
| 422 | Validation error: bad question shape, prompt over 32,768 tokens or 256 KiB, images sent to a text-only model, unknown fields. |
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

```json
{
  "models": [
    {
      "name": "d1",
      "description": "Fast, calibrated Choice, Score, and Noul decisions.",
      "release_date": "2026-09-22"
    }
  ]
}
```
