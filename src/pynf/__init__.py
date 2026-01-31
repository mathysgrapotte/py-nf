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
from typing import Any, NamedTuple

from . import api
from ._core.result import NextflowResult
from ._core.types import DockerConfig, ExecutionRequest
from ._core.validation import validate_meta_map

__all__ = [
    "NextflowResult",
    "DockerConfig",
    "ExecutionRequest",
    "validate_meta_map",
    # Public functional API
    "run_script",
    "run_module",
    "run_nfcore_module",
    "read_output_file",
    "ModuleResult",
]


def run_script(
    nf_file: str | Path,
    inputs=None,
    params=None,
    executor: str = "local",
    docker_config: Mapping[str, Any] | DockerConfig | None = None,
    verbose: bool = False,
) -> NextflowResult:
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
        ``NextflowResult``.
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


class ModuleResult(NamedTuple):
    """Pythonic tuple-like result for a module run.

    This is a convenience wrapper around :class:`~pynf._core.result.NextflowResult`.

    Attributes:
        output_files: Output file paths discovered from Nextflow events/workdirs.
        workflow_outputs: Workflow outputs converted to JSON-ish Python values.
        report: Execution statistics snapshot.
        raw: The underlying `NextflowResult`.

    Example:
        >>> result = run_module("fastqc", reads=["R1.fq"], meta={"id": "s1"})
        >>> output_files, workflow_outputs, report, raw = result
    """

    output_files: list[str]
    workflow_outputs: list[dict[str, Any]]
    report: dict[str, Any]
    raw: NextflowResult


def run_module(
    module_id: str,
    *,
    executor: str = "local",
    docker: bool = False,
    cache_dir: Path = api.DEFAULT_CACHE_DIR,
    github_token: str | None = None,
    params: dict[str, Any] | None = None,
    verbose: bool = False,
    force_download: bool = False,
    **inputs: Any,
) -> ModuleResult:
    """Run an nf-core module using a keyword-argument (pythonic) calling style.

    This function introspects the module's Nextflow input channels and attempts
    to map ``**inputs`` onto those channels.

    Rules:
    - Unknown keyword names are an error.
    - If a keyword could map to multiple channels, we raise an error instead of guessing.

    Args:
        module_id: Module identifier (canonical: without the ``nf-core/`` prefix).
        executor: Nextflow executor name.
        docker: When ``True``, enables Docker with a default registry.
        cache_dir: Directory for cached module artifacts.
        github_token: Optional GitHub token.
        params: Nextflow params mapping.
        verbose: Enable verbose debug output.
        force_download: Re-download the module if already cached.
        **inputs: Module input values (keyword args).

    Returns:
        A tuple-like :class:`ModuleResult`.
    """
    from ._core.pythonic_api import auto_group_inputs

    input_channels = api.get_module_inputs(
        module_id, cache_dir=cache_dir, github_token=github_token
    )
    grouped_inputs = auto_group_inputs(input_channels=input_channels, kwargs=dict(inputs))

    docker_config = DockerConfig(enabled=True, registry="quay.io") if docker else None

    request = ExecutionRequest(
        script_path=Path("."),
        executor=executor,
        params=params,
        inputs=grouped_inputs,
        docker=docker_config,
        verbose=verbose,
    )

    raw = run_nfcore_module(
        module_id,
        request,
        cache_dir=cache_dir,
        github_token=github_token,
        force_download=force_download,
    )

    return ModuleResult(
        output_files=raw.get_output_files(),
        workflow_outputs=raw.get_workflow_outputs(),
        report=raw.get_execution_report(),
        raw=raw,
    )


def run_nfcore_module(
    module_id: str,
    request: ExecutionRequest,
    cache_dir: Path = api.DEFAULT_CACHE_DIR,
    github_token: str | None = None,
    force_download: bool = False,
) -> NextflowResult:
    """Download (if needed) and run an nf-core module.

    Args:
        module_id: Module id (canonical form is without the ``nf-core/`` prefix).
        request: Execution request describing inputs and execution options.
        cache_dir: Directory for cached module artifacts.
        github_token: Optional GitHub token for authenticated requests.
        force_download: When ``True``, re-download the module.

    Returns:
        ``NextflowResult``.
    """
    return api.run_module(
        module_id,
        request,
        cache_dir=cache_dir,
        github_token=github_token,
        force_download=force_download,
    )


def read_output_file(file_path: str | Path) -> str:
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
