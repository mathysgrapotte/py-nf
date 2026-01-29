"""Local cache helpers for nf-core module metadata."""

from pathlib import Path
from typing import Sequence

from pynf.types import ModuleId, ModulePaths

def ensure_cache_dir(cache_dir: Path) -> Path:
    """Ensure the cache directory exists and return it for convenience.

    Example:
        >>> ensure_cache_dir(Path("/tmp/nf-core-modules"))
        PosixPath('/tmp/nf-core-modules')

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

    Example:
        >>> module_paths(Path("/tmp/nf-core-modules"), "samtools/view")
        ModulePaths(...)

    DEPENDS_ON:
    pynf.module_cache.ensure_cache_dir
    pynf.types.ModulePaths

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def read_cached_modules_list(cache_dir: Path) -> list[ModuleId]:
    """Read cached modules list from disk when present.

    Example:
        >>> read_cached_modules_list(Path("/tmp/nf-core-modules"))
        ['nf-core/fastqc']

    DEPENDS_ON:
    pynf.module_cache.ensure_cache_dir

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def write_cached_modules_list(cache_dir: Path, modules: Sequence[ModuleId]) -> None:
    """Write cached modules list to disk.

    Example:
        >>> write_cached_modules_list(Path("/tmp/nf-core-modules"), ["nf-core/fastqc"])

    DEPENDS_ON:
    pynf.module_cache.ensure_cache_dir

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...
