"""Public entry points for the pynf package.

This package is intentionally **functional-first**: most users should only need
``pynf`` (or ``pynf.api``) functions plus a couple of dataclasses.

Design principle:
- Keep the public surface small and easy to discover.
- Hide implementation details behind ``pynf.api``.
"""

from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping
from typing import Any

from . import api
from ._core.result import NextflowResult, SeqeraResult
from ._core.types import DockerConfig, ExecutionRequest, SeqeraConfig
from ._core.validation import validate_meta_map

__all__ = [
    "NextflowResult",
    "SeqeraResult",
    "DockerConfig",
    "ExecutionRequest",
    "SeqeraConfig",
    "validate_meta_map",
    # Public functional API
    "run_script",
    "run_module",
    "run_nfcore_module",
    "read_output_file",
]


def run_script(
    nf_file: str | Path,
    inputs=None,
    params=None,
    executor: str = "local",
    docker_config: Mapping[str, Any] | DockerConfig | None = None,
    verbose: bool = False,
) -> NextflowResult | SeqeraResult:
    """Execute an arbitrary Nextflow script.

    This is a convenience wrapper around :func:`pynf.api.run_script`.

    Args:
        nf_file: Path to a Nextflow script.
        inputs: Optional list of input-group mappings.
        params: Optional mapping of script parameters.
        executor: Nextflow executor name.
        docker_config: Optional Docker configuration mapping or dataclass.
        verbose: Enable verbose debug output.

    Returns:
        ``NextflowResult`` or ``SeqeraResult``.
    """
    request = ExecutionRequest(
        script_path=Path(nf_file),
        executor=executor,
        params=params,
        inputs=inputs,
        docker=_coerce_docker_config(docker_config),
        verbose=verbose,
    )
    return api.run_script(request)


def run_module(
    nf_file: str | Path,
    inputs=None,
    params=None,
    executor: str = "local",
    docker_config: Mapping[str, Any] | DockerConfig | None = None,
    verbose: bool = False,
) -> NextflowResult | SeqeraResult:
    """Alias for :func:`run_script`.

    Kept for users who prefer the "run a module" naming even for raw scripts.
    """
    return run_script(
        nf_file,
        inputs=inputs,
        params=params,
        executor=executor,
        docker_config=docker_config,
        verbose=verbose,
    )


def run_nfcore_module(
    module_id: str,
    request: ExecutionRequest,
    cache_dir: Path = api.DEFAULT_CACHE_DIR,
    github_token: str | None = None,
    force_download: bool = False,
) -> NextflowResult | SeqeraResult:
    """Download (if needed) and run an nf-core module.

    Args:
        module_id: Module id (canonical form is without the ``nf-core/`` prefix).
        request: Execution request describing inputs and execution options.
        cache_dir: Directory for cached module artifacts.
        github_token: Optional GitHub token for authenticated requests.
        force_download: When ``True``, re-download the module.

    Returns:
        ``NextflowResult`` or ``SeqeraResult``.
    """
    return api.run_module(
        module_id,
        request,
        cache_dir=cache_dir,
        github_token=github_token,
        force_download=force_download,
    )


def read_output_file(file_path: str | Path) -> str | None:
    """Read contents of an output file."""
    return api.read_output_file(Path(file_path))


def _coerce_docker_config(
    docker_config: Mapping[str, Any] | DockerConfig | None,
) -> DockerConfig | None:
    """Normalize docker configuration mappings into ``DockerConfig``."""
    if docker_config is None:
        return None
    if isinstance(docker_config, DockerConfig):
        return docker_config

    return DockerConfig(
        enabled=bool(docker_config.get("enabled", True)),
        registry=docker_config.get("registry"),
        registry_override=docker_config.get("registryOverride")
        if "registryOverride" in docker_config
        else docker_config.get("registry_override"),
        remove=docker_config.get("remove"),
        run_options=docker_config.get("runOptions")
        if "runOptions" in docker_config
        else docker_config.get("run_options"),
    )
