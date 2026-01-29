"""Utilities for parsing CLI strings into typed structures."""

from __future__ import annotations

import json
from typing import Any


def parse_params_option(raw: str | None) -> dict[str, Any]:
    """Parse the CLI params option into a dictionary.

    Accepts either a JSON object string or a comma-separated list of
    ``key=value`` pairs. Each value is parsed as JSON when possible to allow
    booleans, numbers, lists, and nested objects.

    Args:
        raw: Raw CLI parameter string or ``None``.

    Returns:
        Parsed parameters. Returns an empty dictionary when ``raw`` is empty.

    Raises:
        json.JSONDecodeError: If JSON parsing fails for a JSON object string.
        ValueError: If a ``key=value`` pair is missing the separator.
    """
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
    """Parse the CLI inputs option as a list of mappings.

    Args:
        raw: Raw CLI inputs JSON string or ``None``.

    Returns:
        List of input group mappings, or ``None`` when ``raw`` is empty.

    Raises:
        json.JSONDecodeError: If the inputs string is not valid JSON.
        ValueError: If the parsed JSON is not a list.
    """
    if not raw:
        return None
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValueError("Error: inputs must be a JSON list of dicts")
    return parsed
