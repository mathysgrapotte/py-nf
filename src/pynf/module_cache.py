"""Local cache helpers for nf-core module metadata.

This module centralizes cache directory management and provides consistent
filesystem paths for cached module artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .types import ModuleId, ModulePaths

MODULES_LIST_FILENAME = "modules_list.txt"


def ensure_cache_dir(cache_dir: Path) -> Path:
    """Ensure the cache directory exists on disk before caching modules.

    Args:
        cache_dir: Directory used to store cached module artifacts.

    Returns:
        The same ``Path`` instance for convenience.

    Example:
        >>> ensure_cache_dir(Path("/tmp/nf-core-modules"))
        PosixPath('/tmp/nf-core-modules')
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def modules_list_path(cache_dir: Path) -> Path:
    """Return the cached modules list path, creating the cache directory if needed.

    Args:
        cache_dir: Directory containing the modules list file.

    Returns:
        Path to ``modules_list.txt`` inside ``cache_dir``.

    Example:
        >>> modules_list_path(Path("/tmp/nf-core-modules"))
        PosixPath('/tmp/nf-core-modules/modules_list.txt')
    """
    return ensure_cache_dir(cache_dir) / MODULES_LIST_FILENAME


def read_cached_modules_list(cache_dir: Path) -> list[ModuleId]:
    """Read cached module identifiers from disk.

    Args:
        cache_dir: Directory containing the cached list.

    Returns:
        A list of cached module identifiers. Returns an empty list when the
        cache file does not exist.

    Example:
        >>> read_cached_modules_list(Path("/tmp/nf-core-modules"))
        ['nf-core/fastqc']
    """
    path = modules_list_path(cache_dir)
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def write_cached_modules_list(cache_dir: Path, modules: Sequence[ModuleId]) -> None:
    """Write module identifiers to the cache file, ensuring the directory exists.

    Args:
        cache_dir: Directory containing the cached list.
        modules: Module identifiers to persist.

    Example:
        >>> write_cached_modules_list(Path("/tmp/nf-core-modules"), ["nf-core/fastqc"])
    """
    path = modules_list_path(cache_dir)
    path.write_text("\n".join(modules) + ("\n" if modules else ""))


def module_dir(cache_dir: Path, module_id: ModuleId) -> Path:
    """Return the local directory for a module id.

    Args:
        cache_dir: Directory containing cached modules.
        module_id: Module identifier (e.g., ``samtools/view``).

    Returns:
        Directory path for the module.

    Example:
        >>> module_dir(Path("/tmp/nf-core-modules"), "samtools/view")
        PosixPath('/tmp/nf-core-modules/samtools/view')
    """
    return ensure_cache_dir(cache_dir) / module_id


def module_paths(cache_dir: Path, module_id: ModuleId) -> ModulePaths:
    """Return canonical paths for a cached module.

    Args:
        cache_dir: Directory containing cached modules.
        module_id: Module identifier (e.g., ``samtools/view``).

    Returns:
        ``ModulePaths`` with deterministic locations for module files.

    Example:
        >>> module_paths(Path("/tmp/nf-core-modules"), "samtools/view")
        ModulePaths(...)
    """
    directory = module_dir(cache_dir, module_id)
    return ModulePaths(
        module_id=module_id,
        module_dir=directory,
        main_nf=directory / "main.nf",
        meta_yml=directory / "meta.yml",
    )


def module_file_paths(cache_dir: Path, module_id: ModuleId) -> dict[str, Path]:
    """Return module paths as a dictionary for legacy callers.

    Args:
        cache_dir: Directory containing cached modules.
        module_id: Module identifier.

    Returns:
        Dictionary with ``module_dir``, ``main_nf``, and ``meta_yml`` keys.

    Example:
        >>> module_file_paths(Path("/tmp/nf-core-modules"), "samtools/view")
        {'module_dir': ..., 'main_nf': ..., 'meta_yml': ...}
    """
    paths = module_paths(cache_dir, module_id)
    return {
        "module_dir": paths.module_dir,
        "main_nf": paths.main_nf,
        "meta_yml": paths.meta_yml,
    }
