"""Tiny client to demo API usage.

Run with active backend server:
    python backend/api_demo.py
"""

import json
import os
from typing import Any

import requests

BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://127.0.0.1:8000/api/v1")


def pretty(o: Any) -> str:
    return json.dumps(o, indent=2, ensure_ascii=False)


def main() -> None:
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    print("/health ->", r.status_code)
    print(pretty(r.json()))

    # Use a known character id from data/characters.json (e.g., "coach")
    r = requests.post(
        f"{BASE_URL}/chat",
        json={"character_id": "coach", "message": "Hello there!"},
        timeout=20,
    )
    print("/chat ->", r.status_code)
    print(pretty(r.json()))


if __name__ == "__main__":
    main()
