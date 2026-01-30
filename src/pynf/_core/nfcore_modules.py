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

The optional ``nf-core/`` prefix is accepted and ignored at the boundary.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import jpype
import yaml

from .github_api import fetch_directory_entries, fetch_raw_text, fetch_rate_limit
from .types import ExecutionRequest, ModuleId, ModulePaths
from .execution import (
    assert_nextflow_jar_exists,
    execute_nextflow,
    get_process_inputs,
    load_nextflow_classes,
    resolve_nextflow_jar_path,
    start_jvm_if_needed,
)
from .seqera_execution import execute_seqera_module

API_BASE = "https://api.github.com/repos/nf-core/modules/contents/modules/nf-core"
RAW_BASE = "https://raw.githubusercontent.com/nf-core/modules/master/modules/nf-core"
MODULES_LIST_FILENAME = "modules_list.txt"


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
        'samtools/view'
    """
    return module_id.removeprefix("nf-core/").strip("/")


def ensure_cache_dir(cache_dir: Path) -> Path:
    """Ensure the cache directory exists."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def modules_list_path(cache_dir: Path) -> Path:
    """Return the cached modules list path, creating the cache dir if needed."""
    return ensure_cache_dir(cache_dir) / MODULES_LIST_FILENAME


def read_cached_modules_list(cache_dir: Path) -> list[ModuleId]:
    """Read cached module identifiers from disk (or return empty)."""
    path = modules_list_path(cache_dir)
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def write_cached_modules_list(cache_dir: Path, modules: Sequence[ModuleId]) -> None:
    """Write module identifiers to the cache file."""
    path = modules_list_path(cache_dir)
    path.write_text("\n".join(modules) + ("\n" if modules else ""))


def module_paths(cache_dir: Path, module_id: str) -> ModulePaths:
    """Return canonical local paths for a cached module."""
    module_id = normalize_module_id(module_id)
    directory = ensure_cache_dir(cache_dir) / module_id
    return ModulePaths(
        module_id=module_id,
        module_dir=directory,
        main_nf=directory / "main.nf",
        meta_yml=directory / "meta.yml",
    )


def list_modules(cache_dir: Path, github_token: str | None) -> list[ModuleId]:
    """List top-level modules, using a local cache when available."""
    cached = read_cached_modules_list(cache_dir)
    if cached:
        return cached

    entries = fetch_directory_entries(API_BASE, github_token)
    modules = _extract_directories(entries)
    write_cached_modules_list(cache_dir, modules)
    return modules


def list_submodules(module_id: str, github_token: str | None) -> list[ModuleId]:
    """List submodules under a given module id."""
    module_id = normalize_module_id(module_id)
    entries = fetch_directory_entries(f"{API_BASE}/{module_id}", github_token)
    return _extract_directories(entries)


def get_rate_limit_status(github_token: str | None) -> dict:
    """Return GitHub API rate limit status."""
    return fetch_rate_limit(github_token)


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
        ``ModulePaths`` describing cached module files.
    """
    paths = module_paths(cache_dir, module_id)
    paths.module_dir.mkdir(parents=True, exist_ok=True)

    if _is_cached(paths) and not force:
        return paths

    urls = _raw_file_urls(paths.module_id)
    _write_module_file(paths.main_nf, fetch_raw_text(urls["main_nf"], github_token))
    _write_module_file(paths.meta_yml, fetch_raw_text(urls["meta_yml"], github_token))
    return paths


def inspect_module(
    cache_dir: Path, module_id: ModuleId, github_token: str | None
) -> dict:
    """Inspect module metadata and return a structured summary."""
    paths = ensure_module(cache_dir, module_id, github_token)
    meta = _read_yaml(paths.meta_yml)
    main_preview = _preview_lines(paths.main_nf)
    main_lines = paths.main_nf.read_text().splitlines()

    return {
        "name": normalize_module_id(module_id),
        "path": str(paths.module_dir),
        "meta": meta,
        "meta_raw": paths.meta_yml.read_text(),
        "main_nf_lines": len(main_lines),
        "main_nf_preview": main_preview,
    }


def get_module_inputs(
    cache_dir: Path, module_id: ModuleId, github_token: str | None
) -> list[dict]:
    """Return module input definitions via Nextflow introspection."""
    paths = ensure_module(cache_dir, module_id, github_token)

    jar_path = resolve_nextflow_jar_path(None)
    assert_nextflow_jar_exists(jar_path)
    start_jvm_if_needed(jar_path)

    classes = load_nextflow_classes()
    ScriptLoaderFactory = classes["ScriptLoaderFactory"]
    Session = classes["Session"]
    ScriptMeta = classes["ScriptMeta"]

    ScriptFile = jpype.JClass("nextflow.script.ScriptFile")
    ArrayList = jpype.JClass("java.util.ArrayList")

    session = Session()
    script_file = ScriptFile(jpype.java.nio.file.Paths.get(str(paths.main_nf)))
    session.init(script_file, ArrayList(), None, None)
    session.start()

    loader = ScriptLoaderFactory.create(session)
    java_path = jpype.java.nio.file.Paths.get(str(paths.main_nf))
    loader.parse(java_path)
    script = loader.getScript()

    inputs = get_process_inputs(loader, script, ScriptMeta)
    session.destroy()
    return inputs


def run_nfcore_module(
    cache_dir: Path,
    module_id: ModuleId,
    github_token: str | None,
    request: ExecutionRequest,
    *,
    force_download: bool = False,
) -> Any:
    """Ensure a module is cached and execute it locally or remotely."""
    paths = ensure_module(cache_dir, module_id, github_token, force=force_download)
    if request.backend == "seqera":
        return execute_seqera_module(request, paths)
    module_request = ExecutionRequest(
        script_path=paths.main_nf,
        executor=request.executor,
        params=request.params,
        inputs=request.inputs,
        docker=request.docker,
        verbose=request.verbose,
        backend=request.backend,
        seqera=request.seqera,
    )
    return execute_nextflow(module_request)


def _extract_directories(entries: list[dict]) -> list[ModuleId]:
    directories = [item["name"] for item in entries if item.get("type") == "dir"]
    return sorted(directories)


def _raw_file_urls(module_id: ModuleId) -> dict[str, str]:
    module_id = normalize_module_id(module_id)
    return {
        "main_nf": f"{RAW_BASE}/{module_id}/main.nf",
        "meta_yml": f"{RAW_BASE}/{module_id}/meta.yml",
    }


def _is_cached(paths: ModulePaths) -> bool:
    return paths.main_nf.exists() and paths.meta_yml.exists()


def _write_module_file(dest: Path, content: str) -> None:
    dest.write_text(content)


def _read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _preview_lines(path: Path, limit: int = 20) -> list[str]:
    return path.read_text().splitlines()[:limit]
