"""GitHub API boundary for nf-core module metadata and files."""

from __future__ import annotations

from typing import Any

import requests


def _auth_headers(github_token: str | None) -> dict[str, str]:
    """Build HTTP headers for GitHub API requests.

    Args:
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Headers dictionary including the Authorization header when supplied.
    """
    if not github_token:
        return {}
    return {"Authorization": f"token {github_token}"}


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
    """
    try:
        response = requests.get(
            f"{api_url}?per_page=100", headers=_auth_headers(github_token)
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ValueError(f"Failed to fetch from GitHub API: {exc}") from exc

    data = response.json()
    if not isinstance(data, list):
        return []
    return data


def fetch_raw_text(raw_url: str, github_token: str | None = None) -> str:
    """Fetch a raw file's text content.

    Args:
        raw_url: Raw GitHub URL for the file.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Text content of the remote file.

    Raises:
        ValueError: If the file does not exist or the request fails.
    """
    response = requests.get(raw_url, headers=_auth_headers(github_token))
    if response.status_code == 404:
        raise ValueError(f"Module file not found: {raw_url}")
    response.raise_for_status()
    return response.text


def fetch_rate_limit(github_token: str | None) -> dict[str, Any]:
    """Fetch GitHub API rate limit status.

    Args:
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Mapping with ``limit``, ``remaining``, and ``reset_time`` fields.

    Raises:
        ValueError: If the GitHub API request fails.
    """
    try:
        response = requests.get(
            "https://api.github.com/rate_limit", headers=_auth_headers(github_token)
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ValueError(f"Failed to fetch rate limit status: {exc}") from exc

    data = response.json()
    core = data.get("resources", {}).get("core", {})
    return {
        "limit": core.get("limit"),
        "remaining": core.get("remaining"),
        "reset_time": core.get("reset"),
    }
