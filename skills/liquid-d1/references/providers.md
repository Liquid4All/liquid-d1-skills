# Where to call Liquid d1

d1 is developed and owned by Liquid AI. It implements the System One decision
contract and is available through three access paths. Preserve the provider the
user selected. Do not silently exchange one provider for another: credentials,
billing, limits, availability, request APIs, and response metadata may differ.

| Access path | Model ID | Credential | Primary interface |
| --- | --- | --- | --- |
| Liquid direct | `d1` | `LIQUID_API_KEY` | `POST https://api.liquid.ai/decisions/v1/systemone` |
| Vercel AI Gateway | `liquid/d1` | `AI_GATEWAY_API_KEY` or Vercel OIDC | AI SDK `experimental_evaluate` |
| OpenRouter | `liquid/d1` | `OPENROUTER_API_KEY` | `POST https://openrouter.ai/api/alpha/decisions` |

Provider listings and prices change. Verify the live model pages before stating
current pricing or availability:

- Vercel: https://vercel.com/ai-gateway/models/d1
- OpenRouter: https://openrouter.ai/liquid/d1

## Liquid direct

Use Liquid direct when the application already uses a Liquid API key or wants
the first-party endpoint. The request and response contract is in `api.md`;
TypeSafe SDK and HTTP examples are in `sdks.md`. The bundled `scripts/d1.py`
runner also targets this path by default.

## Vercel AI Gateway

Use AI SDK's evaluation API with the gateway model ID `liquid/d1`:

```ts
import { experimental_evaluate as evaluate } from "ai";

const result = await evaluate({
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
