"""Public API composition layer (stubs)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pynf._core.types import ExecutionRequest, ModuleId

DEFAULT_CACHE_DIR: Path

def run_script(request: ExecutionRequest, nextflow_jar_path: str | None = ...) -> Any: ...

def run_module(
    module_id: ModuleId,
    request: ExecutionRequest,
    cache_dir: Path = ...,
    github_token: str | None = ...,
    force_download: bool = ...,
) -> Any: ...

def list_modules(cache_dir: Path = ..., github_token: str | None = ...) -> list[str]: ...

def list_submodules(module_id: ModuleId, github_token: str | None = ...) -> list[str]: ...

def inspect_module(
    module_id: ModuleId,
    cache_dir: Path = ...,
    github_token: str | None = ...,
) -> dict: ...

def get_module_inputs(
    module_id: ModuleId,
    cache_dir: Path = ...,
    github_token: str | None = ...,
) -> list[dict]: ...

def get_rate_limit_status(github_token: str | None = ...) -> dict: ...

def read_output_file(path: Path) -> str | None: ...
