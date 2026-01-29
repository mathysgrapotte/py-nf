"""High-level convenience helpers for nf-core module workflows."""

from pathlib import Path
from typing import Any, Dict, Optional

from . import api
from .nfcore import NFCoreModule, download_module as download_nfcore_module
from .types import DockerConfig, ExecutionRequest


def list_modules(
    cache_dir: Optional[Path] = None, github_token: Optional[str] = None
) -> list[str]:
    """List available nf-core modules.

    Args:
        cache_dir: Directory to cache modules.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Sorted list of module identifiers.

    Example:
        >>> list_modules()
        ['nf-core/fastqc', 'nf-core/samtools']
    """
    return api.list_modules(
        cache_dir=cache_dir or api.DEFAULT_CACHE_DIR, github_token=github_token
    )


def list_submodules(
    module: str,
    cache_dir: Optional[Path] = None,
    github_token: Optional[str] = None,
) -> list[str]:
    """List submodules available in a given module.

    Args:
        module: Parent module identifier (e.g., ``samtools``).
        cache_dir: Optional cache directory override.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Sorted list of submodule identifiers.

    Example:
        >>> list_submodules("nf-core/samtools")
        ['view', 'sort']
    """
    return api.list_submodules(module, github_token=github_token)


def download_module(
    module: str,
    cache_dir: Optional[Path] = None,
    force: bool = False,
    github_token: Optional[str] = None,
) -> NFCoreModule:
    """Download an nf-core module.

    Args:
        module: Module identifier (e.g., ``fastqc`` or ``samtools/view``).
        cache_dir: Optional cache directory override.
        force: Force re-download even if cached.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        ``NFCoreModule`` wrapper describing cached files.

    Example:
        >>> download_module("nf-core/fastqc", cache_dir=Path("/tmp/cache"))
        NFCoreModule(...)
    """
    return download_nfcore_module(
        module,
        cache_dir=cache_dir,
        github_token=github_token,
        force=force,
    )


def inspect_module(
    module: str,
    cache_dir: Optional[Path] = None,
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Inspect a downloaded module and return its metadata.

    Args:
        module: Module identifier.
        cache_dir: Optional cache directory override.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Dictionary containing module metadata and file previews.

    Example:
        >>> inspect_module("nf-core/fastqc")
        {'name': 'nf-core/fastqc', 'meta': {...}, ...}
    """
    cache_dir = cache_dir or api.DEFAULT_CACHE_DIR
    return api.inspect_module(module, cache_dir=cache_dir, github_token=github_token)


def get_module_inputs(
    module: str,
    cache_dir: Optional[Path] = None,
    github_token: Optional[str] = None,
) -> list[Dict[str, Any]]:
    """Extract input parameters from a module's ``main.nf``.

    Args:
        module: Module identifier.
        cache_dir: Optional cache directory override.
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        List of input channel definitions.

    Example:
        >>> get_module_inputs("nf-core/fastqc")
        [{'type': 'tuple', 'params': [{'type': 'val', 'name': 'meta'}]}, ...]
    """
    cache_dir = cache_dir or api.DEFAULT_CACHE_DIR
    return api.get_module_inputs(module, cache_dir=cache_dir, github_token=github_token)


def module_exists_locally(
    module: str,
    cache_dir: Optional[Path] = None,
) -> bool:
    """Check if a module exists in the local cache.

    Args:
        module: Module identifier.
        cache_dir: Optional cache directory override.

    Returns:
        ``True`` when the module appears cached locally.

    Example:
        >>> module_exists_locally("nf-core/fastqc")
        True
    """
    cache_dir = cache_dir or api.DEFAULT_CACHE_DIR
    module_dir = cache_dir / module
    return (module_dir / "main.nf").exists() and (module_dir / "meta.yml").exists()


def get_rate_limit_status(
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Return GitHub API rate limit status.

    Args:
        github_token: Optional GitHub token for authenticated requests.

    Returns:
        Mapping describing GitHub API rate limit state.

    Example:
        >>> get_rate_limit_status()
        {'limit': 60, 'remaining': 59, 'reset_time': 1700000000}
    """
    return api.get_rate_limit_status(github_token)


def run_nfcore_module(
    module: str,
    inputs: Optional[list] = None,
    params: Optional[Dict[str, Any]] = None,
    executor: str = "local",
    docker_enabled: bool = False,
    cache_dir: Optional[Path] = None,
    github_token: Optional[str] = None,
    verbose: bool = False,
):
    """Run an nf-core module with automatic download if needed.

    Args:
        module: Module identifier (e.g., ``fastqc``).
        inputs: List of input group mappings.
        params: Mapping of script parameters.
        executor: Nextflow executor name.
        docker_enabled: Whether to enable Docker execution.
        cache_dir: Optional cache directory override.
        github_token: Optional GitHub token for authenticated requests.
        verbose: Enable verbose debug output.

    Returns:
        Execution result object (currently ``NextflowResult``).

    Example:
        >>> run_nfcore_module("nf-core/fastqc", inputs=[{"reads": "sample.fq"}])
        NextflowResult(...)
    """
    cache_dir = cache_dir or api.DEFAULT_CACHE_DIR
    docker_config = (
        DockerConfig(enabled=True, registry="quay.io") if docker_enabled else None
    )
    request = ExecutionRequest(
        script_path=Path(module),
        executor=executor,
        params=params,
        inputs=inputs,
        docker=docker_config,
        verbose=verbose,
    )
    return api.run_module(
        module, request, cache_dir=cache_dir, github_token=github_token
    )
