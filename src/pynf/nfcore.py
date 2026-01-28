"""nf-core module workflows with a function-first architecture."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .module_cache import ensure_cache_dir, module_file_paths
from .module_catalog import get_rate_limit_status as _get_rate_limit_status
from .module_catalog import list_modules as _list_modules
from .module_catalog import list_submodules as _list_submodules
from .module_downloader import download_module as _download_module

DEFAULT_CACHE_DIR = Path("./nf-core-modules")


def resolve_cache_dir(cache_dir: Path | None) -> Path:
    """Resolve and ensure the cache directory."""
    return ensure_cache_dir(cache_dir or DEFAULT_CACHE_DIR)


def resolve_github_token(explicit_token: str | None) -> str | None:
    """Resolve GitHub token from argument or environment."""
    return explicit_token or os.getenv("GITHUB_TOKEN")


def download_module(tool_name: str, cache_dir: Path | None = None, github_token: str | None = None, force: bool = False) -> "NFCoreModule":
    """Download a module and return a path-focused module reference."""
    resolved_cache_dir = resolve_cache_dir(cache_dir)
    token = resolve_github_token(github_token)
    paths = _download_module(resolved_cache_dir, tool_name, token, force=force)
    return NFCoreModule(tool_name, paths["module_dir"])


def list_available_modules(cache_dir: Path | None = None, github_token: str | None = None) -> list[str]:
    """List available top-level nf-core modules."""
    resolved_cache_dir = resolve_cache_dir(cache_dir)
    token = resolve_github_token(github_token)
    return _list_modules(resolved_cache_dir, token)


def list_available_submodules(module_name: str, github_token: str | None = None) -> list[str]:
    """List submodules for a given module."""
    token = resolve_github_token(github_token)
    return _list_submodules(module_name, token)


def get_rate_limit_status(github_token: str | None = None) -> dict:
    """Return GitHub API rate limit status."""
    token = resolve_github_token(github_token)
    return _get_rate_limit_status(token)


@dataclass(frozen=True)
class NFCoreModule:
    """Represents an nf-core module with its key file paths."""

    tool_name: str
    local_path: Path

    @property
    def main_nf(self) -> Path:
        return self.local_path / "main.nf"

    @property
    def meta_yml(self) -> Path:
        return self.local_path / "meta.yml"

    def exists(self) -> bool:
        return self.main_nf.exists() and self.meta_yml.exists()


class NFCoreModuleManager:
    """Thin compatibility wrapper over the function-first API."""

    def __init__(self, cache_dir: Optional[Path] = None, github_token: Optional[str] = None):
        self.cache_dir = resolve_cache_dir(cache_dir)
        self.github_token = resolve_github_token(github_token)

    def download_module(self, tool_name: str, force: bool = False) -> NFCoreModule:
        return download_module(tool_name, cache_dir=self.cache_dir, github_token=self.github_token, force=force)

    def get_rate_limit_status(self) -> dict:
        return get_rate_limit_status(self.github_token)

    def list_available_modules(self) -> list[str]:
        return list_available_modules(cache_dir=self.cache_dir, github_token=self.github_token)

    def list_submodules(self, module_name: str) -> list[str]:
        return list_available_submodules(module_name, github_token=self.github_token)


def download_nfcore_module(tool_name: str, cache_dir: Optional[Path] = None) -> NFCoreModule:
    """Backwards-compatible convenience wrapper."""
    return download_module(tool_name, cache_dir=cache_dir)
