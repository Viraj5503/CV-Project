"""Smoke-test the Anthropic API setup: key present, report model reachable.

Free to run — models.retrieve() bills no tokens.
Usage: python scripts/check_api.py
"""

import os

import anthropic

from pcb_vision.report import MODEL  # importing this also loads .env


def main() -> int:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key.startswith("sk-ant-"):
        print("FAIL: no API key — paste yours into .env (ANTHROPIC_API_KEY=sk-ant-...)")
        return 1
    client = anthropic.Anthropic()
    try:
        model = client.models.retrieve(MODEL)
    except anthropic.AuthenticationError:
        print("FAIL: key rejected by the API (invalid or revoked)")
        return 1
    except anthropic.NotFoundError:
        print(f"FAIL: model {MODEL!r} not available on this account")
        return 1
    print(f"OK: key valid, report model reachable — {model.id} ({model.display_name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
