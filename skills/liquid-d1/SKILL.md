---
name: liquid-d1
description: >
  Build typed System One decisions with Liquid AI's d1 family: hosted d1 and
  d1-ultra, and open-weight d1-3B and d1-omni-600M. Use for classification,
  routing, scoring, ranking, and yes/no judgments with Choice, Score, and Noul,
  including image decisions and omni audio input. Covers Liquid, Vercel AI
  Gateway, OpenRouter, and local inference.
---

# Build with the Liquid d1 family

d1 is developed and owned by Liquid AI and implements the System One API
contract. System One compatibility describes its interface, not its ownership.
Send a **state** (text or JSON), supported media, and a map of
**questions**, and it returns one typed answer per question: a Choice among named
options, a Score against ordered levels, or a Noul (probability of yes). Answers
are read straight from the model's probabilities. Nothing is generated, so there
is nothing to parse and no output-token cost.

Code owns the workflow. d1 supplies the judgment where plain code would need
semantic understanding: which team a ticket belongs to, how severe a log line is,
whether a claim is supported by its evidence.

## Choose a model and deployment

| Model | Access | Inputs | Use when |
| --- | --- | --- | --- |
| `d1` | Hosted | Text, images | Lower-priced hosted decisions |
| `d1-ultra` | Hosted | Text, images | Most capable hosted model for harder decisions |
| `d1-3B` | Open weights, 3.1B | Text, images | Local inference, self-hosting, or fine-tuning |
| `d1-omni-600M` | Open weights, 587M | Text with images or audio | Smallest model or speech input |

Hosted models are available through Liquid, Vercel AI Gateway, and OpenRouter.
Preserve the user's chosen provider and runtime. The question primitives are
shared; setup, media encoding, limits, authentication, and response metadata
can differ. Open-weight models can run through Transformers or a compatible
local server; read `references/local-inference.md` for those paths.

d1 is not a chat model. For text generation on Liquid, use the LFM models on the
OpenAI-compatible endpoint (`https://api.liquid.ai/openai/v1`). This skill is
about decisions only.

## Read the live docs

Start with Liquid's current documentation:

- Model selection: https://docs.liquid.ai/lfm/models/decision-models
- Hosted API and SDK examples: https://docs.liquid.ai/lfm/models/d1
- Open weights: https://docs.liquid.ai/lfm/models/d1-3b and
  https://docs.liquid.ai/lfm/models/d1-omni-600m
- Migration patterns: https://docs.liquid.ai/guides/decision-model-guide

The console reference at https://console.liquid.ai/docs provides the hosted
API contract and OpenAPI exports. TypeSafe's primitive and confidence pages
at https://docs.typesafe.ai/llms.txt supplement the shared System One contract
and question design. TypeSafe does not own or serve d1.

If live access is unavailable, use the bundled references below and say so; do
not invent fields, limits, or model names.

| Task | Read |
| --- | --- |
| Exact request/response shape, limits, errors, rate limits | `references/api.md` |
| Call from Python, TypeScript, or curl | `references/sdks.md` |
| Choose and configure Liquid direct, Vercel, or OpenRouter | `references/providers.md` |
| Run open weights with Transformers, llama.cpp, or MLX | `references/local-inference.md` |
| Try a hosted or compatible local HTTP request without dependencies | `scripts/d1.py` |
| Design questions well | TypeSafe primitives and confidence pages (links above) |

## The direct Liquid contract in one screen

```
POST https://api.liquid.ai/decisions/v1/systemone
Authorization: Bearer $LIQUID_API_KEY
Content-Type: application/json

{
  "model": "d1",
  "state": "Help! My payouts have been failing for 3 days.",
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which team should handle this?",
      "criteria": { "billing": "Payments, invoicing, refunds",
                    "technical": "Bugs, outages, integrations",
                    "sales": "Pricing, upgrades, new accounts" }
    },
    "is_urgent":   { "type": "noul",  "instructions": "Does this convey urgency?" },
    "frustration": { "type": "score", "instructions": "How frustrated is the customer?",
                     "criteria": ["Calm", "Frustrated", "Very angry"] }
  }
}
```

Response: `answers` keyed by the same question ids. Choice returns `choice`,
`probabilities` per option, `confidence`. Score returns `score` (probability-
weighted, can land between levels), `legend`, `probabilities` per level,
`confidence`. Noul returns `noul`, the probability of yes. `usage` carries
`input_tokens` and `output_tokens` (always 0), plus `cost` in USD when the model
is priced.

On Liquid's direct endpoint, use `d1` or `d1-ultra` with a Liquid API key. List
available models with `GET /decisions/v1/models`. On Vercel AI Gateway and OpenRouter,
use `liquid/d1` or `liquid/d1-ultra`; read `references/providers.md` before writing
provider-specific code.

Keys come from the console's API keys page and are shown once. Send them from a
server. Never put a key in browser code.

## Find the useful shape

Start from what the application will show, select, change, or hand off, then
work back to the judgments it needs. Keep rules, math, exact lookups, and
execution in code. Add d1 where the code needs to understand meaning.

Patterns worth reaching for, beyond plain classification:

- **Route and fill arguments.** One Choice picks the handler; branch-specific
  questions asked in the same request supply its parameters. Code reads only the
  branch it took.
- **Select instead of generate.** Have code enumerate candidate values or spans,
  then ask d1 which one is intended. The model cannot pick a value you left out,
  so check candidate coverage.
- **Rank with comparable Scores.** Ask the same Score question per item and
  sort on `score`. Levels must describe concrete situations that stand on their
  own.
- **Verify and escalate.** A Noul per claim against its evidence. Send low-
  confidence or failing cases to a person or a reasoning model.
- **Score once, decide many ways.** Store raw probabilities. Weights, thresholds,
  and display filters can change without rerunning inference.

For an open-ended request, offer the two or three directions that best serve the
goal and recommend one. For a concrete request, pick the pattern and build.

## Design the questions

Choose the primitive by what the answer means:

| Need | Primitive | Watch for |
| --- | --- | --- |
| One of a defined set | `choice` | Define options; add a no-match option when nothing may fit |
| Whether a condition holds | `noul` | Probability of yes, no separate confidence; one per label when several may apply |
| Degree along a dimension | `score` | Define ordered levels; `score` may fall between them |

Check option and level count limits for the chosen API or runtime.

Give each question enough state: the source text, identities, relationships,
policies, current facts. Prefer named JSON fields when the state has several
parts, and reference them in instructions with backticked paths like
`ticket.messages[0].text`. Put the judgment in `instructions` and define the
answers in `criteria`. Question ids are for code and are not sent to the model,
so the question has to carry its full meaning.

Ask one coherent judgment per question. Split dimensions that are independently
useful. For hosted Liquid calls, each question is its own prompt carrying the whole
state and supplied images, and usage counts each one. Check `references/api.md`
and the live contract for hosted limits; do not apply them to local runtimes.

Both hosted models accept a top-level `images` array. Use raw HTTP for hosted
image requests; current TypeSafe SDK examples cover text inputs. Open-model
image and audio formats depend on the runtime; omni supports text with images
or text with audio, including up to 30 seconds of speech.

## Compose and verify

Ask independent questions over the same state in one request, including
speculative ones. They run in parallel and cannot see each other's answers.
Make a second request only when an earlier answer is needed to fetch evidence
or build new state.

Use probabilities and confidence to drive behavior, with thresholds tuned on
the user's own data. Confidence runs from 0 (spread evenly) to 1 (all on one
answer) and describes how concentrated the distribution is, not whether the
workflow is correct. A Noul near 0.5 means yes and no are about equally likely,
not "medium". Several acceptable options can legitimately spread probability.

For hosted Liquid calls, handle 429 by honoring `Retry-After`; requests share an organization/model
sliding-window limit, exposed in `x-ratelimit-*` headers. A 429 with error code
`model_unavailable` means no healthy inference target, not quota. 401 means a
missing or invalid key, and 422 means the request failed validation.

Test representative cases and look at the resulting application behavior, not
just the raw answers. For failures, inspect the exact state, questions,
candidates, probabilities, and how code composed them. Separate missing
evidence, model error, code error, and service failure.
