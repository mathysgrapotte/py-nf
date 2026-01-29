"""nf-core modules: list, download/cache, and id normalization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

ModuleId = str

API_BASE: str
RAW_BASE: str
MODULES_LIST_FILENAME: str


def normalize_module_id(module_id: str) -> ModuleId: ...


@dataclass(frozen=True)
class ModulePaths:
    module_id: ModuleId
    module_dir: Path
    main_nf: Path
    meta_yml: Path


def ensure_cache_dir(cache_dir: Path) -> Path: ...

def modules_list_path(cache_dir: Path) -> Path: ...

def read_cached_modules_list(cache_dir: Path) -> list[ModuleId]: ...

def write_cached_modules_list(cache_dir: Path, modules: Sequence[ModuleId]) -> None: ...

def module_paths(cache_dir: Path, module_id: str) -> ModulePaths: ...

def list_modules(cache_dir: Path, github_token: str | None) -> list[ModuleId]: ...

def list_submodules(module_id: str, github_token: str | None) -> list[ModuleId]: ...

def get_rate_limit_status(github_token: str | None) -> dict: ...

def ensure_module(
    cache_dir: Path,
    module_id: str,
    github_token: str | None,
    *,
    force: bool = ...,
) -> ModulePaths: ...
