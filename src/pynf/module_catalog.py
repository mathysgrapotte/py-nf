"""Catalog queries for nf-core modules (composition over IO boundaries)."""

from __future__ import annotations

from pathlib import Path

from .types import ModuleId

from .github_api import fetch_directory_entries, fetch_rate_limit
from .module_cache import read_cached_modules_list, write_cached_modules_list

API_BASE = "https://api.github.com/repos/nf-core/modules/contents/modules/nf-core"


def list_modules(cache_dir: Path, github_token: str | None) -> list[ModuleId]:
    """List top-level modules, using a local cache when available.

    The cache is populated by querying the nf-core/modules GitHub repository when
    missing, and the cached file is written for subsequent fast lookups.

    Args:
        cache_dir: Directory containing the cached modules list.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Sorted list of module identifiers.

    Example:
        >>> list_modules(Path("/tmp/cache"), github_token=None)
        ['fastqc', 'samtools']
    """
    cached = read_cached_modules_list(cache_dir)
    if cached:
        return cached

    entries = fetch_directory_entries(API_BASE, github_token)
    modules = _extract_directories(entries)
    write_cached_modules_list(cache_dir, modules)
    return modules


def list_submodules(module_id: ModuleId, github_token: str | None) -> list[ModuleId]:
    """List submodules under a given module id.

    Args:
        module_id: Parent module identifier.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Sorted list of module identifiers.

    Example:
        >>> list_submodules("nf-core/samtools", None)
        ['view', 'sort']
    """
    entries = fetch_directory_entries(f"{API_BASE}/{module_id}", github_token)
    return _extract_directories(entries)


def get_rate_limit_status(github_token: str | None) -> dict:
    """Return GitHub API rate limit status.

    Args:
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Mapping describing GitHub API rate limit state.

    Example:
        >>> get_rate_limit_status(None)
        {'limit': 60, 'remaining': 59, 'reset_time': 1700000000}
    """
    return fetch_rate_limit(github_token)


def _extract_directories(entries: list[dict]) -> list[ModuleId]:
    """Extract directory names from GitHub API entries.

    Args:
        entries: Parsed GitHub API response entries.

    Returns:
        Sorted list of directory names.

    Example:
        >>> _extract_directories([{"name": "fastqc", "type": "dir"}])
        ['fastqc']
    """
    directories = [item["name"] for item in entries if item.get("type") == "dir"]
    return sorted(directories)
