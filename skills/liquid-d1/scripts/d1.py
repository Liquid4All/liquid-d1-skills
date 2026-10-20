#!/usr/bin/env python3
"""Call a hosted Liquid or compatible local System One endpoint with no dependencies beyond the stdlib.

Usage:
    python d1.py                       # runs the built-in demo request
    python d1.py request.json          # sends the JSON body in request.json
    echo '{...}' | python d1.py -      # reads the body from stdin
    python d1.py --models              # lists decision models you can call

Reads LIQUID_API_KEY from the environment. Set LIQUID_BASE_URL to override the
base URL (default https://api.liquid.ai/decisions). For llama.cpp use
http://127.0.0.1:8080 and a request file without a hosted model ID. Custom
servers may omit LIQUID_API_KEY; if set, it is sent as a bearer token.
The no-argument demo targets hosted d1. --models requires GET /v1/models.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse

BASE_URL = os.environ.get("LIQUID_BASE_URL", "https://api.liquid.ai/decisions").rstrip("/")
API_KEY = os.environ.get("LIQUID_API_KEY")

DEMO = {
    "model": "d1",
    "state": "Help! My payouts have been failing for 3 days.",
    "questions": {
        "department": {
            "type": "choice",
            "instructions": "Which team should handle this?",
            "criteria": {
                "billing": "Payments, invoicing, refunds",
                "technical": "Bugs, outages, integrations",
                "sales": "Pricing, upgrades, new accounts",
            },
        },
        "is_urgent": {"type": "noul", "instructions": "Does this convey urgency?"},
        "frustration": {
            "type": "score",
            "instructions": "How frustrated is the customer?",
            "criteria": ["Calm", "Frustrated", "Very angry"],
        },
    },
}


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    return headers


def request(method: str, path: str, body: dict | None = None) -> tuple[int, dict, dict]:
    """Return (status, headers, parsed_json). Raises nothing on HTTP errors."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, method=method, headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, dict(resp.headers), json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as err:
        raw = err.read()
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = {"raw": raw.decode(errors="replace")}
        return err.code, dict(err.headers), parsed
    except urllib.error.URLError as err:
        sys.exit(f"Could not reach {BASE_URL}: {err.reason}")


def system_one(body: dict) -> dict:
    if urlparse(BASE_URL).hostname == "api.liquid.ai" and not API_KEY:
        sys.exit("LIQUID_API_KEY is required to call Liquid d1")
    status, headers, payload = request("POST", "/v1/systemone", body)
    if status == 200:
        return payload
    hint = {
        401: "missing or invalid bearer token; set LIQUID_API_KEY for this server",
        422: "request failed validation; check question shapes and prompt size",
        429: f"rate limited or model unavailable; Retry-After={headers.get('Retry-After')}",
    }.get(status, "unexpected status")
    sys.exit(f"HTTP {status}: {hint}\n{json.dumps(payload, indent=2)}")


def list_models() -> dict:
    status, _, payload = request("GET", "/v1/models")
    if status != 200:
        sys.exit(f"HTTP {status}: {json.dumps(payload, indent=2)}")
    return payload


def main(argv: list[str]) -> None:
    if "--models" in argv:
        print(json.dumps(list_models(), indent=2))
        return
    if len(argv) > 1 and argv[1] == "-":
        body = json.load(sys.stdin)
    elif len(argv) > 1:
        with open(argv[1]) as fh:
            body = json.load(fh)
    else:
        body = DEMO
    print(json.dumps(system_one(body), indent=2))


if __name__ == "__main__":
    main(sys.argv)
