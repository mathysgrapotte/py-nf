"""Public API composition layer for pynf."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .execution import execute_nextflow
from .module_catalog import get_rate_limit_status as _get_rate_limit_status
from .module_catalog import list_modules as _list_modules
from .module_catalog import list_submodules as _list_submodules
from .module_service import get_module_inputs as _get_module_inputs
from .module_service import inspect_module as _inspect_module
from .module_service import run_nfcore_module
from .types import ExecutionRequest, ModuleId

DEFAULT_CACHE_DIR = Path("./nf-core-modules")


def run_script(request: ExecutionRequest, nextflow_jar_path: str | None = None) -> Any:
    """Execute an arbitrary Nextflow script.

    Args:
        request: Execution request describing the script execution.
        nextflow_jar_path: Optional override for the Nextflow JAR path.

    Returns:
        Execution result object (currently ``NextflowResult``).

    Example:
        >>> request = ExecutionRequest(script_path=Path("main.nf"), executor="local")
        >>> run_script(request)
        NextflowResult(...)
    """
    return execute_nextflow(request, nextflow_jar_path=nextflow_jar_path)


def run_module(
    module_id: ModuleId,
    request: ExecutionRequest,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    github_token: str | None = None,
    force_download: bool = False,
) -> Any:
    """Ensure a module is cached, then execute it.

    Args:
        module_id: Module identifier.
        request: Execution request describing inputs and options. The
            ``script_path`` value is ignored and replaced with the module's
            ``main.nf`` path.
        cache_dir: Cache directory for module artifacts.
        github_token: Optional GitHub token for authenticated requests.
        force_download: When ``True``, re-download the module.

    Returns:
        Execution result object (currently ``NextflowResult``).

    Example:
        >>> request = ExecutionRequest(script_path=Path("main.nf"), executor="local")
        >>> run_module("nf-core/fastqc", request)
        NextflowResult(...)
    """
    return run_nfcore_module(
        cache_dir,
        module_id,
        github_token,
        request,
        force_download=force_download,
    )


def list_modules(
    cache_dir: Path = DEFAULT_CACHE_DIR, github_token: str | None = None
) -> list[str]:
    """List available modules, using cache when possible.

    Args:
        cache_dir: Cache directory for module metadata.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Sorted list of module identifiers.
    """
    """List available modules, using cache when possible.

    Args:
        cache_dir: Cache directory for module metadata.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Sorted list of module identifiers.

    Example:
        >>> list_modules(Path("/tmp/modules"))
        ['nf-core/fastqc', 'nf-core/samtools']
    """
    return _list_modules(cache_dir, github_token)


def list_submodules(module_id: ModuleId, github_token: str | None = None) -> list[str]:
    """List submodules under a module identifier.

    Args:
        module_id: Module identifier.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Sorted list of submodule identifiers.
    """
    """List submodules under a module identifier.

    Args:
        module_id: Module identifier.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Sorted list of submodule identifiers.

    Example:
        >>> list_submodules("nf-core/samtools")
        ['view', 'sort']
    """
    return _list_submodules(module_id, github_token)


def inspect_module(
    module_id: ModuleId,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    github_token: str | None = None,
) -> dict:
    """Inspect module metadata and previews.

    Args:
        module_id: Module identifier.
        cache_dir: Cache directory for module artifacts.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Dictionary describing the module files and metadata.

    Example:
        >>> inspect_module("nf-core/fastqc")
        {'name': 'nf-core/fastqc', 'meta': {...}, ...}
    """
    return _inspect_module(cache_dir, module_id, github_token)


def get_module_inputs(
    module_id: ModuleId,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    github_token: str | None = None,
) -> list[dict]:
    """Return module input definitions via native introspection.

    Args:
        module_id: Module identifier.
        cache_dir: Cache directory for module artifacts.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        List of input channel definitions.

    Example:
        >>> get_module_inputs("nf-core/fastqc")
        [{'type': 'tuple', 'params': [{'type': 'val', 'name': 'meta'}]}, ...]
    """
    return _get_module_inputs(cache_dir, module_id, github_token)


def get_rate_limit_status(github_token: str | None = None) -> dict:
    """Return GitHub API rate limit status.

    Args:
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Mapping describing GitHub API rate limit state.
    """
    """Return GitHub API rate limit status.

    Args:
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Mapping describing GitHub API rate limit state.

    Example:
        >>> get_rate_limit_status()
        {'limit': 60, 'remaining': 59, 'reset_time': 1700000000}
    """
    return _get_rate_limit_status(github_token)


def read_output_file(path: Path) -> str | None:
    """Read an output file's contents.

    Args:
        path: Path to the output file.

    Returns:
        File contents.

    Raises:
        OSError: If the file cannot be read.

    Example:
        >>> read_output_file(Path("work/output.txt"))
        '...later output...'
    """
    return path.read_text()
