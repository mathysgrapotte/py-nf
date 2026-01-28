"""Compatibility wrappers for nf-core module workflows."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .module_catalog import get_rate_limit_status as _get_rate_limit_status
from .module_catalog import list_modules as _list_modules
from .module_catalog import list_submodules as _list_submodules
from .module_service import ensure_module as _ensure_module
from .types import ModuleId, ModulePaths

DEFAULT_CACHE_DIR = Path("./nf-core-modules")


def resolve_cache_dir(cache_dir: Path | None) -> Path:
    """Resolve the cache directory for module artifacts.

    Args:
        cache_dir: Optional cache directory override.

    Returns:
        Concrete cache directory path.
    """
    return cache_dir or DEFAULT_CACHE_DIR


def resolve_github_token(explicit_token: str | None) -> str | None:
    """Resolve a GitHub token from arguments or environment.

    Args:
        explicit_token: Token provided by the caller.

    Returns:
        Token string or ``None`` when unavailable.
    """
    return explicit_token or os.getenv("GITHUB_TOKEN")


def download_module(
    tool_name: ModuleId,
    cache_dir: Path | None = None,
    github_token: str | None = None,
    force: bool = False,
) -> "NFCoreModule":
    """Download a module and return a convenience wrapper.

    Args:
        tool_name: Module identifier.
        cache_dir: Optional cache directory override.
        github_token: Optional GitHub token for authenticated requests.
        force: When ``True``, re-download even if cached.

    Returns:
        ``NFCoreModule`` wrapper describing cached paths.
    """
    resolved_cache_dir = resolve_cache_dir(cache_dir)
    token = resolve_github_token(github_token)
    paths = _ensure_module(resolved_cache_dir, tool_name, token, force=force)
    return NFCoreModule.from_paths(paths)


def list_available_modules(
    cache_dir: Path | None = None, github_token: str | None = None
) -> list[ModuleId]:
    """List available top-level nf-core modules.

    Args:
        cache_dir: Optional cache directory override.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Sorted list of module identifiers.
    """
    resolved_cache_dir = resolve_cache_dir(cache_dir)
    token = resolve_github_token(github_token)
    return _list_modules(resolved_cache_dir, token)


def list_available_submodules(
    module_name: ModuleId, github_token: str | None = None
) -> list[ModuleId]:
    """List submodules for a given module.

    Args:
        module_name: Parent module identifier.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Sorted list of submodule identifiers.
    """
    token = resolve_github_token(github_token)
    return _list_submodules(module_name, token)


def get_rate_limit_status(github_token: str | None = None) -> dict:
    """Return GitHub API rate limit status.

    Args:
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Mapping describing GitHub API rate limit state.
    """
    token = resolve_github_token(github_token)
    return _get_rate_limit_status(token)


@dataclass(frozen=True)
class NFCoreModule:
    """Convenience wrapper around cached module file paths.

    Attributes:
        tool_name: Module identifier.
        local_path: Directory containing cached module files.
    """

    tool_name: ModuleId
    local_path: Path

    @property
    def main_nf(self) -> Path:
        """Return the path to ``main.nf`` for this module."""
        return self.local_path / "main.nf"

    @property
    def meta_yml(self) -> Path:
        """Return the path to ``meta.yml`` for this module."""
        return self.local_path / "meta.yml"

    def exists(self) -> bool:
        """Return ``True`` when the module's core files exist."""
        return self.main_nf.exists() and self.meta_yml.exists()

    @staticmethod
    def from_paths(paths: ModulePaths) -> "NFCoreModule":
        """Build an ``NFCoreModule`` wrapper from ``ModulePaths``.

        Args:
            paths: Resolved module file paths.

        Returns:
            ``NFCoreModule`` wrapper instance.
        """
        return NFCoreModule(paths.module_id, paths.module_dir)


class NFCoreModuleManager:
    """Compatibility wrapper exposing the previous manager-style API."""

    def __init__(
        self, cache_dir: Optional[Path] = None, github_token: Optional[str] = None
    ):
        self.cache_dir = resolve_cache_dir(cache_dir)
        self.github_token = resolve_github_token(github_token)

    def download_module(self, tool_name: ModuleId, force: bool = False) -> NFCoreModule:
        """Download a module through the manager interface.

        Args:
            tool_name: Module identifier.
            force: When ``True``, re-download even if cached.

        Returns:
            ``NFCoreModule`` wrapper instance.
        """
        return download_module(
            tool_name,
            cache_dir=self.cache_dir,
            github_token=self.github_token,
            force=force,
        )

    def get_rate_limit_status(self) -> dict:
        """Return GitHub API rate limit status for this manager."""
        return get_rate_limit_status(self.github_token)

    def list_available_modules(self) -> list[ModuleId]:
        """Return the available top-level module identifiers."""
        return list_available_modules(
            cache_dir=self.cache_dir, github_token=self.github_token
        )

    def list_submodules(self, module_name: ModuleId) -> list[ModuleId]:
        """Return the available submodules for a module."""
        return list_available_submodules(module_name, github_token=self.github_token)


def download_nfcore_module(
    tool_name: ModuleId, cache_dir: Optional[Path] = None
) -> NFCoreModule:
    """Backwards-compatible convenience wrapper.

    Args:
        tool_name: Module identifier.
        cache_dir: Optional cache directory override.

    Returns:
        ``NFCoreModule`` wrapper instance.
    """
    return download_module(tool_name, cache_dir=cache_dir)
