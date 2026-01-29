"""Module download orchestration for nf-core modules."""

from pathlib import Path

from pynf.types import ModuleId, ModulePaths

def download_module(
    cache_dir: Path,
    module_id: ModuleId,
    github_token: str | None,
    force: bool = False,
) -> ModulePaths:
    """Download main.nf and meta.yml for a module.

    Example:
        >>> download_module(Path("/tmp/cache"), "nf-core/fastqc", None)
        ModulePaths(...)

    DEPENDS_ON:
    pynf.module_cache.module_paths
    pynf.module_downloader._is_cached
    pynf.module_downloader._raw_file_urls
    pynf.module_downloader._write_module_file
    pynf.github_api.fetch_raw_text

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def _is_cached(paths: ModulePaths) -> bool:
    """Return True when expected module files already exist.

    Example:
        >>> _is_cached(paths)
        True

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def _raw_file_urls(module_id: ModuleId) -> dict[str, str]:
    """Construct raw GitHub URLs for module files.

    Example:
        >>> _raw_file_urls("nf-core/fastqc")
        {'main_nf': 'https://...', 'meta_yml': 'https://...'}

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...

def _write_module_file(dest: Path, content: str) -> None:
    """Write a module file to disk.

    Example:
        >>> _write_module_file(Path("/tmp/main.nf"), "workflow")

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...
