"""GitHub API boundary for nf-core module metadata and files."""

from __future__ import annotations

from typing import Any

def fetch_directory_entries(
    api_url: str, github_token: str | None
) -> list[dict[str, Any]]:
    """Fetch directory entries from the GitHub API.

Args:
    api_url: GitHub API URL for the target directory.
    github_token: Optional GitHub token for authenticated requests.

Returns:
    List of directory entries as returned by the GitHub API.

Raises:
    ValueError: If the GitHub API request fails.

Example:
    >>> fetch_directory_entries("https://api.github.com/...", None)
    [{'name': 'fastqc', 'type': 'dir'}]"""
    ...

def fetch_raw_text(raw_url: str, github_token: str | None = None) -> str:
    """Fetch a raw file's text content.

Args:
    raw_url: Raw GitHub URL for the file.
    github_token: Optional GitHub token for authenticated requests.

Returns:
    Text content of the remote file.

Raises:
    ValueError: If the file does not exist or the request fails.

Example:
    >>> fetch_raw_text("https://raw.githubusercontent.com/.../meta.yml")
    'contents of meta.yml'"""
    ...

def fetch_rate_limit(github_token: str | None) -> dict[str, Any]:
    """Fetch GitHub API rate limit status.

Args:
    github_token: Optional GitHub token for authenticated requests.

Returns:
    Mapping with ``limit``, ``remaining``, and ``reset_time`` fields.

Raises:
    ValueError: If the GitHub API request fails.

Example:
    >>> fetch_rate_limit(None)
    {'limit': 60, 'remaining': 59, 'reset_time': 1700000000}"""
    ...

