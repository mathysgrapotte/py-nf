"""nf-core module catalog/cache/orchestration (stubs)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from pynf._core.types import ExecutionRequest, ModuleId, ModulePaths

API_BASE: str
RAW_BASE: str
MODULES_LIST_FILENAME: str

def normalize_module_id(module_id: str) -> ModuleId: ...

def ensure_cache_dir(cache_dir: Path) -> Path: ...

def modules_list_path(cache_dir: Path) -> Path: ...

def read_cached_modules_list(cache_dir: Path) -> list[ModuleId]: ...

def write_cached_modules_list(cache_dir: Path, modules: Sequence[ModuleId]) -> None: ...

def module_paths(cache_dir: Path, module_id: str) -> ModulePaths: ...

def list_modules(cache_dir: Path, github_token: str | None) -> list[ModuleId]: ...

def list_submodules(module_id: str, github_token: str | None) -> list[ModuleId]: ...

def get_rate_limit_status(github_token: str | None) -> dict: ...

def ensure_module(cache_dir: Path, module_id: ModuleId, github_token: str | None, *, force: bool = ...) -> ModulePaths: ...

def inspect_module(cache_dir: Path, module_id: ModuleId, github_token: str | None) -> dict: ...

def get_module_inputs(cache_dir: Path, module_id: ModuleId, github_token: str | None) -> list[dict]: ...

def run_nfcore_module(
    cache_dir: Path,
    module_id: ModuleId,
    github_token: str | None,
    request: ExecutionRequest,
    *,
    force_download: bool = ...,
) -> Any: ...
