# Where to call Liquid d1

The hosted models `d1` and `d1-ultra` are developed and owned by Liquid AI.
They implement the System One decision contract across three access paths.
For open weights and local servers, read `local-inference.md`. Preserve the provider the
user selected. Do not silently exchange one provider for another: credentials,
billing, limits, availability, request APIs, and response metadata may differ.

| Access path | Model ID | Credential | Primary interface |
| --- | --- | --- | --- |
| Liquid direct | `d1`, `d1-ultra` | `LIQUID_API_KEY` | `POST https://api.liquid.ai/decisions/v1/systemone` |
| Vercel AI Gateway | `liquid/d1`, `liquid/d1-ultra` | `AI_GATEWAY_API_KEY` or Vercel OIDC | AI SDK `experimental_decide` |
| OpenRouter | `liquid/d1`, `liquid/d1-ultra` | `OPENROUTER_API_KEY` | `POST https://openrouter.ai/api/alpha/decisions` |

Provider listings and prices change. Verify the live model pages before stating
current pricing or availability:

- Vercel: https://vercel.com/ai-gateway/models/d1
- Vercel ultra: https://vercel.com/ai-gateway/models/d1-ultra
- OpenRouter: https://openrouter.ai/liquid/d1
- OpenRouter ultra: https://openrouter.ai/liquid/d1-ultra
- Liquid hosted reference: https://docs.liquid.ai/lfm/models/d1

Examples below use `d1`; select the corresponding `d1-ultra` ID for harder
decisions. Verify provider-specific image support and encoding before porting
a Liquid image request to a gateway.

## Liquid direct

Use Liquid direct when the application already uses a Liquid API key or wants
the first-party endpoint. The request and response contract is in `api.md`;
TypeSafe SDK and HTTP examples are in `sdks.md`. The bundled `scripts/d1.py`
runner also targets this path by default.

## Vercel AI Gateway

Use AI SDK's decision API with `ai >= 7.0.128`. Configure
`AI_GATEWAY_API_KEY` or Vercel OIDC in the server environment:

```bash
npm install 'ai@^7.0.128' @ai-sdk/gateway
```

The older `experimental_evaluate` name remains a deprecated compatibility alias.
Source: https://vercel.com/i/ai-sdk-evaluation-to-decisions

Call the gateway model ID `liquid/d1`:

```ts
import { experimental_decide as decide } from "ai";

const result = await decide({
  model: "liquid/d1",
  state: "Help! My payouts have been failing for 3 days.",
  questions: {
    department: {
      type: "choice",
      instructions: "Which team should handle this?",
      criteria: {
        billing: "Payments, invoicing, refunds",
        technical: "Bugs, outages, integrations",
        sales: "Pricing, upgrades, new accounts",
      },
    },
    isUrgent: {
      type: "boolean",
      instructions: "Does this message convey urgency?",
    },
  },
});
```

AI SDK calls the yes/no primitive `boolean`; the raw System One wire contract
calls it `noul`. Treat this as an adapter-level naming difference and consume
the normalized result returned by the installed AI SDK version. Keep gateway
credentials server-side.

## OpenRouter

OpenRouter's Decisions API accepts the System One request shape. Use the
OpenRouter model ID, not Liquid's direct `d1` ID:

```bash
curl https://openrouter.ai/api/alpha/decisions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "liquid/d1",
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
      "is_urgent": {
        "type": "noul",
        "instructions": "Does this message convey urgency?"
      }
    }
  }'
```

Do not send d1 to OpenRouter's chat-completions endpoint: d1 returns structured
decisions rather than generated chat text. OpenRouter may add fields such as a
request id, provider, or cost around the normalized answers; use its live API
documentation or installed SDK types for those provider-specific fields.
