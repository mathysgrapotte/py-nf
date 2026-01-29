"""Catalog queries for nf-core modules (pure composition over IO boundaries)."""

from pathlib import Path

from pynf.types import ModuleId

def list_modules(cache_dir: Path, github_token: str | None) -> list[ModuleId]:
    """List top-level modules, using cache when available.

    Example:
        >>> list_modules(Path("/tmp/cache"), None)
        ['nf-core/fastqc', 'nf-core/samtools']

    DEPENDS_ON:
    pynf.module_cache.read_cached_modules_list
    pynf.module_cache.write_cached_modules_list
    pynf.github_api.fetch_directory_entries
    pynf.module_catalog._extract_directories

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def list_submodules(module_id: ModuleId, github_token: str | None) -> list[ModuleId]:
    """List submodules under a module id.

    Example:
        >>> list_submodules("nf-core/samtools", None)
        ['view', 'sort']

    DEPENDS_ON:
    pynf.github_api.fetch_directory_entries
    pynf.module_catalog._extract_directories

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...

def get_rate_limit_status(github_token: str | None) -> dict:
    """Return GitHub API rate limit status.

    Example:
        >>> get_rate_limit_status(None)
        {'limit': 60, 'remaining': 59, 'reset_time': 1700000000}

    DEPENDS_ON:
    pynf.github_api.fetch_rate_limit

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...

def _extract_directories(entries: list[dict]) -> list[str]:
    """Extract directory names from GitHub API entries.

    Example:
        >>> _extract_directories([{"name": "fastqc", "type": "dir"}])
        ['fastqc']

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...
