"""GitHub API IO boundary (stubs)."""

from __future__ import annotations

from typing import Any


def fetch_directory_entries(url: str, github_token: str | None = ...) -> list[dict[str, Any]]: ...

def fetch_raw_text(url: str, github_token: str | None = ...) -> str: ...

def fetch_rate_limit(github_token: str | None = ...) -> dict: ...
