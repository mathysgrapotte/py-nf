"""Module download orchestration for nf-core modules."""

from __future__ import annotations

from pathlib import Path

from .types import ModuleId, ModulePaths

from .github_api import fetch_raw_text
from .module_cache import ensure_cache_dir, module_paths

RAW_BASE = "https://raw.githubusercontent.com/nf-core/modules/master/modules/nf-core"


def download_module(
    cache_dir: Path,
    module_id: ModuleId,
    github_token: str | None,
    force: bool = False,
) -> ModulePaths:
    """Download ``main.nf`` and ``meta.yml`` for a module.

    Args:
        cache_dir: Directory where modules are cached.
        module_id: Module identifier (e.g., ``fastqc``).
        github_token: Optional GitHub token for authenticated requests.
        force: When ``True``, re-download even if cached.

    Returns:
        ``ModulePaths`` describing the downloaded files.
    """
    ensure_cache_dir(cache_dir)
    paths = module_paths(cache_dir, module_id)
    paths.module_dir.mkdir(parents=True, exist_ok=True)

    if _is_cached(paths) and not force:
        return paths

    urls = _raw_file_urls(module_id)
    _write_module_file(paths.main_nf, fetch_raw_text(urls["main_nf"], github_token))
    _write_module_file(paths.meta_yml, fetch_raw_text(urls["meta_yml"], github_token))
    return paths


def _is_cached(paths: ModulePaths) -> bool:
    """Return ``True`` when cached module files exist.

    Args:
        paths: Resolved module file paths.

    Returns:
        ``True`` when both ``main.nf`` and ``meta.yml`` exist.
    """
    return paths.main_nf.exists() and paths.meta_yml.exists()


def _raw_file_urls(module_id: ModuleId) -> dict[str, str]:
    """Construct raw GitHub URLs for module files.

    Args:
        module_id: Module identifier.

    Returns:
        Mapping with ``main_nf`` and ``meta_yml`` URLs.
    """
    return {
        "main_nf": f"{RAW_BASE}/{module_id}/main.nf",
        "meta_yml": f"{RAW_BASE}/{module_id}/meta.yml",
    }


def _write_module_file(dest: Path, content: str) -> None:
    """Write downloaded module contents to disk.

    Args:
        dest: Destination path for the module file.
        content: Raw text content to write.
    """
    dest.write_text(content)
