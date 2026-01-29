"""nf-core modules: list, download/cache, and id normalization.

This module intentionally keeps nf-core module handling *cohesive* (one place to
read) while staying functional.

Key design choice: a canonical ``ModuleId`` does **not** include the ``nf-core/``
prefix.

Why?
- GitHub URLs already bake in the ``modules/nf-core`` root.
- Storing cached modules under their canonical id avoids duplicate paths.
- Callers can still pass ``nf-core/<id>``; we normalize at the boundary.

Examples:
    >>> normalize_module_id("nf-core/fastqc")
    'fastqc'
    >>> normalize_module_id("samtools/view")
    'samtools/view'
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .github_api import fetch_directory_entries, fetch_raw_text, fetch_rate_limit

ModuleId = str

API_BASE = "https://api.github.com/repos/nf-core/modules/contents/modules/nf-core"
RAW_BASE = "https://raw.githubusercontent.com/nf-core/modules/master/modules/nf-core"
MODULES_LIST_FILENAME = "modules_list.txt"


def normalize_module_id(module_id: str) -> ModuleId:
    """Normalize a user-provided module id into the canonical form.

    Canonical form:
    - no ``nf-core/`` prefix
    - no leading/trailing slashes

    Args:
        module_id: Module identifier supplied by the user.

    Returns:
        Canonical module id.

    Example:
        >>> normalize_module_id("nf-core/samtools/view")
        'samtools/view'
    """
    return module_id.removeprefix("nf-core/").strip("/")


@dataclass(frozen=True)
class ModulePaths:
    """Resolved local paths for a cached nf-core module."""

    module_id: ModuleId
    module_dir: Path
    main_nf: Path
    meta_yml: Path


def ensure_cache_dir(cache_dir: Path) -> Path:
    """Ensure the cache directory exists."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def modules_list_path(cache_dir: Path) -> Path:
    """Return the path to the cached modules index file."""
    return ensure_cache_dir(cache_dir) / MODULES_LIST_FILENAME


def read_cached_modules_list(cache_dir: Path) -> list[ModuleId]:
    """Read the cached module identifiers list (or return empty)."""
    path = modules_list_path(cache_dir)
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def write_cached_modules_list(cache_dir: Path, modules: Sequence[ModuleId]) -> None:
    """Write the cached module identifiers list."""
    path = modules_list_path(cache_dir)
    path.write_text("\n".join(modules) + ("\n" if modules else ""))


def module_paths(cache_dir: Path, module_id: str) -> ModulePaths:
    """Return canonical paths for a cached module."""
    module_id = normalize_module_id(module_id)
    directory = ensure_cache_dir(cache_dir) / module_id
    return ModulePaths(
        module_id=module_id,
        module_dir=directory,
        main_nf=directory / "main.nf",
        meta_yml=directory / "meta.yml",
    )


def list_modules(cache_dir: Path, github_token: str | None) -> list[ModuleId]:
    """List top-level modules, using a local cache when available."""
    cached = read_cached_modules_list(cache_dir)
    if cached:
        return cached

    entries = fetch_directory_entries(API_BASE, github_token)
    modules = _extract_directories(entries)
    write_cached_modules_list(cache_dir, modules)
    return modules


def list_submodules(module_id: str, github_token: str | None) -> list[ModuleId]:
    """List submodules under a given module id."""
    module_id = normalize_module_id(module_id)
    entries = fetch_directory_entries(f"{API_BASE}/{module_id}", github_token)
    return _extract_directories(entries)


def get_rate_limit_status(github_token: str | None) -> dict:
    """Return GitHub API rate limit status."""
    return fetch_rate_limit(github_token)


def ensure_module(
    cache_dir: Path,
    module_id: str,
    github_token: str | None,
    *,
    force: bool = False,
) -> ModulePaths:
    """Ensure a module's ``main.nf`` and ``meta.yml`` are cached locally."""
    paths = module_paths(cache_dir, module_id)
    paths.module_dir.mkdir(parents=True, exist_ok=True)

    if _is_cached(paths) and not force:
        return paths

    urls = _raw_file_urls(paths.module_id)
    _write_module_file(paths.main_nf, fetch_raw_text(urls["main_nf"], github_token))
    _write_module_file(paths.meta_yml, fetch_raw_text(urls["meta_yml"], github_token))
    return paths


def _extract_directories(entries: list[dict]) -> list[ModuleId]:
    directories = [item["name"] for item in entries if item.get("type") == "dir"]
    return sorted(directories)


def _raw_file_urls(module_id: ModuleId) -> dict[str, str]:
    return {
        "main_nf": f"{RAW_BASE}/{module_id}/main.nf",
        "meta_yml": f"{RAW_BASE}/{module_id}/meta.yml",
    }


def _is_cached(paths: ModulePaths) -> bool:
    return paths.main_nf.exists() and paths.meta_yml.exists()


def _write_module_file(dest: Path, content: str) -> None:
    dest.write_text(content)
