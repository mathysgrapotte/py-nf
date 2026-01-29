"""nf-core modules support (catalog + cache + execution orchestration).

This module is intentionally **functional** and **cohesive**:
- one place to understand nf-core module ids
- one place to download/cache module files
- one place to run and introspect modules

## Module identifiers
Canonical ``ModuleId`` values are **relative to** ``modules/nf-core/`` in the
nf-core/modules repository.

Examples:
- ``fastqc``
- ``samtools/view``

The optional ``nf-core/`` prefix is accepted and ignored at the boundary."""

from __future__ import annotations

from typing import Any

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
    'samtools/view'"""
    ...

def ensure_cache_dir(cache_dir: Path) -> Path:
    """Ensure the cache directory exists."""
    ...

def modules_list_path(cache_dir: Path) -> Path:
    """Return the cached modules list path, creating the cache dir if needed."""
    ...

def read_cached_modules_list(cache_dir: Path) -> list[ModuleId]:
    """Read cached module identifiers from disk (or return empty)."""
    ...

def write_cached_modules_list(cache_dir: Path, modules: Sequence[ModuleId]) -> None:
    """Write module identifiers to the cache file."""
    ...

def module_paths(cache_dir: Path, module_id: str) -> ModulePaths:
    """Return canonical local paths for a cached module."""
    ...

def list_modules(cache_dir: Path, github_token: str | None) -> list[ModuleId]:
    """List top-level modules, using a local cache when available."""
    ...

def list_submodules(module_id: str, github_token: str | None) -> list[ModuleId]:
    """List submodules under a given module id."""
    ...

def get_rate_limit_status(github_token: str | None) -> dict:
    """Return GitHub API rate limit status."""
    ...

def ensure_module(
    cache_dir: Path,
    module_id: ModuleId,
    github_token: str | None,
    *,
    force: bool = False,
) -> ModulePaths:
    """Ensure an nf-core module is cached locally.

Args:
    cache_dir: Directory for cached module artifacts.
    module_id: Module identifier (canonical form: ``fastqc`` or ``samtools/view``).
    github_token: Optional GitHub token for authenticated requests.
    force: When ``True``, re-download even if cached.

Returns:
    ``ModulePaths`` describing cached module files."""
    ...

def inspect_module(cache_dir: Path, module_id: ModuleId, github_token: str | None) -> dict:
    """Inspect module metadata and return a structured summary."""
    ...

def get_module_inputs(cache_dir: Path, module_id: ModuleId, github_token: str | None) -> list[dict]:
    """Return module input definitions via Nextflow introspection."""
    ...

def run_nfcore_module(
    cache_dir: Path,
    module_id: ModuleId,
    github_token: str | None,
    request: ExecutionRequest,
    *,
    force_download: bool = False,
) -> Any:
    """Ensure a module is cached and execute it with Nextflow."""
    ...

