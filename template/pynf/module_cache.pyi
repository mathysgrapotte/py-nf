"""Local cache helpers for nf-core module metadata."""

from pathlib import Path
from typing import Sequence

from pynf.types import ModuleId, ModulePaths

def ensure_cache_dir(cache_dir: Path) -> Path:
    """Ensure the cache directory exists.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    pathlib

    CHECKS:
    cache_dir must be writable
    """
    ...

def module_paths(cache_dir: Path, module_id: ModuleId) -> ModulePaths:
    """Construct deterministic local module paths.

    DEPENDS_ON:
    pynf.module_cache.ensure_cache_dir
    pynf.types.ModulePaths

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def read_cached_modules_list(cache_dir: Path) -> list[ModuleId]:
    """Read cached modules list from disk when present.

    DEPENDS_ON:
    pynf.module_cache.ensure_cache_dir

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def write_cached_modules_list(cache_dir: Path, modules: Sequence[ModuleId]) -> None:
    """Write cached modules list to disk.

    DEPENDS_ON:
    pynf.module_cache.ensure_cache_dir

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...
