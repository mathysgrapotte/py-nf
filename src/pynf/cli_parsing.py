"""Pure CLI parsing helpers."""

from __future__ import annotations

import json
from typing import Any


def parse_params_option(raw: str | None) -> dict[str, Any]:
    """Parse params as JSON or comma-separated key=value pairs."""
    if not raw:
        return {}

    if raw.strip().startswith("{"):
        return json.loads(raw)

    parsed: dict[str, Any] = {}
    for pair in raw.split(","):
        key, value = pair.strip().split("=", 1)
        try:
            parsed[key] = json.loads(value)
        except json.JSONDecodeError:
            parsed[key] = value
    return parsed


def parse_inputs_option(raw: str | None) -> list[dict[str, Any]] | None:
    """Parse inputs as a JSON list of dicts."""
    if not raw:
        return None
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValueError("Error: inputs must be a JSON list of dicts")
    return parsed
