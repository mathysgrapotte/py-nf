"""Module download orchestration for nf-core modules."""

from __future__ import annotations

from pathlib import Path

from .github_api import fetch_raw_text
from .module_cache import ensure_cache_dir, module_file_paths

RAW_BASE = "https://raw.githubusercontent.com/nf-core/modules/master/modules/nf-core"


def download_module(cache_dir: Path, module_id: str, github_token: str | None, force: bool = False) -> dict[str, Path]:
    """Download main.nf and meta.yml for a module."""
    ensure_cache_dir(cache_dir)
    paths = module_file_paths(cache_dir, module_id)
    paths["module_dir"].mkdir(parents=True, exist_ok=True)

    if _is_cached(paths) and not force:
        return paths

    urls = _raw_file_urls(module_id)
    _write_module_file(paths["main_nf"], fetch_raw_text(urls["main_nf"], github_token))
    _write_module_file(paths["meta_yml"], fetch_raw_text(urls["meta_yml"], github_token))
    return paths


def _is_cached(paths: dict[str, Path]) -> bool:
    return paths["main_nf"].exists() and paths["meta_yml"].exists()


def _raw_file_urls(module_id: str) -> dict[str, str]:
    return {
        "main_nf": f"{RAW_BASE}/{module_id}/main.nf",
        "meta_yml": f"{RAW_BASE}/{module_id}/meta.yml",
    }


def _write_module_file(dest: Path, content: str) -> None:
    dest.write_text(content)
