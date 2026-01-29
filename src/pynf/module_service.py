"""High-level workflows that orchestrate module caching and execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import jpype
import yaml

from .execution import execute_nextflow
from .jvm_bridge import load_nextflow_classes, start_jvm_if_needed
from .module_downloader import download_module
from .process_introspection import get_process_inputs
from .runtime_config import assert_nextflow_jar_exists, resolve_nextflow_jar_path
from .types import ExecutionRequest, ModuleId, ModulePaths


def ensure_module(
    cache_dir: Path,
    module_id: ModuleId,
    github_token: str | None,
    force: bool = False,
) -> ModulePaths:
    """Ensure an nf-core module is cached locally.

    Args:
        cache_dir: Directory for cached module artifacts.
        module_id: Module identifier (e.g., ``fastqc``).
        github_token: Optional GitHub token for authenticated requests.
        force: When ``True``, re-download even if cached.

    Returns:
        ``ModulePaths`` describing cached module files.

    Example:
        >>> ensure_module(Path("/tmp/cache"), "nf-core/fastqc", None)
        ModulePaths(...)
    """
    return download_module(cache_dir, module_id, github_token, force=force)


def inspect_module(
    cache_dir: Path, module_id: ModuleId, github_token: str | None
) -> dict[str, Any]:
    """Inspect module metadata and return a structured summary.

    Args:
        cache_dir: Directory for cached module artifacts.
        module_id: Module identifier.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Dictionary containing module metadata, paths, and previews.

    Example:
        >>> inspect_module(Path("/tmp/cache"), "nf-core/fastqc", None)
    """
    paths = ensure_module(cache_dir, module_id, github_token)
    meta = _read_yaml(paths.meta_yml)
    main_preview = _preview_lines(paths.main_nf)
    main_lines = paths.main_nf.read_text().splitlines()

    return {
        "name": module_id,
        "path": str(paths.module_dir),
        "meta": meta,
        "meta_raw": paths.meta_yml.read_text(),
        "main_nf_lines": len(main_lines),
        "main_nf_preview": main_preview,
    }


def get_module_inputs(
    cache_dir: Path, module_id: ModuleId, github_token: str | None
) -> list[dict]:
    """Return module input definitions via Nextflow introspection.

    Args:
        cache_dir: Directory for cached module artifacts.
        module_id: Module identifier.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        List of input channel definitions extracted from the module.

    Example:
        >>> get_module_inputs(Path("/tmp/cache"), "nf-core/fastqc", None)
        [{'type': 'tuple', 'params': [{'name': 'reads', 'type': 'path'}]}]
    """
    paths = ensure_module(cache_dir, module_id, github_token)
    jar_path = resolve_nextflow_jar_path(None)
    assert_nextflow_jar_exists(jar_path)
    start_jvm_if_needed(jar_path)

    classes = load_nextflow_classes()
    ScriptLoaderFactory = classes["ScriptLoaderFactory"]
    Session = classes["Session"]
    ScriptMeta = classes["ScriptMeta"]

    SessionCls = Session
    ScriptFile = jpype.JClass("nextflow.script.ScriptFile")
    ArrayList = jpype.JClass("java.util.ArrayList")

    session = SessionCls()
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
    force_download: bool = False,
) -> Any:
    """Ensure a module is cached and execute it with Nextflow.

    Args:
        cache_dir: Directory for cached module artifacts.
        module_id: Module identifier.
        github_token: Optional GitHub token for authenticated requests.
        request: Execution request describing how to run the module. The
            ``script_path`` value is ignored and replaced with the module's
            ``main.nf`` path.
        force_download: When ``True``, re-download even if cached.

    Returns:
        Execution result object (currently ``NextflowResult``).

    Example:
        >>> run_nfcore_module(Path("/tmp/cache"), "nf-core/fastqc", None, request)
        NextflowResult(...)
    """
    paths = ensure_module(cache_dir, module_id, github_token, force=force_download)
    module_request = ExecutionRequest(
        script_path=paths.main_nf,
        executor=request.executor,
        params=request.params,
        inputs=request.inputs,
        docker=request.docker,
        verbose=request.verbose,
    )
    return execute_nextflow(module_request)


def _read_yaml(path: Path) -> dict:
    """Read YAML into a dictionary.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML content.

    Example:
        >>> _read_yaml(Path("/tmp/meta.yml"))
    """
    return yaml.safe_load(path.read_text())


def _preview_lines(path: Path, limit: int = 20) -> list[str]:
    """Read a file and return the first ``limit`` lines.

    Args:
        path: Path to the file.
        limit: Maximum number of lines to return.

    Returns:
        List of line strings.

    Example:
        >>> _preview_lines(Path("/tmp/main.nf"))
        ['workflow {', '  ...']
    """
    return path.read_text().splitlines()[:limit]


def _introspect_only_request(script_path: Path) -> ExecutionRequest:
    """Build a request used only for introspection.

    Args:
        script_path: Script path to introspect.

    Returns:
        Execution request with default settings and no inputs.

    Example:
        >>> _introspect_only_request(Path("main.nf"))
    """
    return ExecutionRequest(script_path=script_path)
