"""Local cache helpers for nf-core module metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

MODULES_LIST_FILENAME = "modules_list.txt"


def ensure_cache_dir(cache_dir: Path) -> Path:
    """Ensure the cache directory exists and return it."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def modules_list_path(cache_dir: Path) -> Path:
    """Return the canonical path to the cached modules list."""
    return ensure_cache_dir(cache_dir) / MODULES_LIST_FILENAME


def read_cached_modules_list(cache_dir: Path) -> list[str]:
    """Read cached modules list from disk when present."""
    path = modules_list_path(cache_dir)
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def write_cached_modules_list(cache_dir: Path, modules: Sequence[str]) -> None:
    """Write cached modules list to disk."""
    path = modules_list_path(cache_dir)
    path.write_text("\n".join(modules) + ("\n" if modules else ""))


def module_dir(cache_dir: Path, module_id: str) -> Path:
    """Return the local directory for a module id."""
    return ensure_cache_dir(cache_dir) / module_id


def module_file_paths(cache_dir: Path, module_id: str) -> dict[str, Path]:
    """Return canonical paths for module files."""
    directory = module_dir(cache_dir, module_id)
    return {
        "module_dir": directory,
        "main_nf": directory / "main.nf",
        "meta_yml": directory / "meta.yml",
    }
