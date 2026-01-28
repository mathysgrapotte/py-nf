"""Public entry points for the pynf package."""

from pathlib import Path

from . import api
from .engine import NextflowEngine, _coerce_docker_config, validate_meta_map
from .nfcore import NFCoreModule, NFCoreModuleManager, download_nfcore_module
from .result import NextflowResult
from .types import DockerConfig, ExecutionRequest

__all__ = [
    "NextflowEngine",
    "NextflowResult",
    "run_module",
    "run_script",
    "run_nfcore_module",
    "read_output_file",
    "download_nfcore_module",
    "NFCoreModule",
    "NFCoreModuleManager",
    "DockerConfig",
    "ExecutionRequest",
    "validate_meta_map",
]


def run_module(
    nf_file,
    inputs=None,
    params=None,
    executor="local",
    docker_config=None,
    verbose=False,
):
    """Execute a Nextflow script with a simple one-liner API.

    Args:
        nf_file: Path to the Nextflow script.
        inputs: Optional list of input group mappings.
        params: Optional mapping of script parameters.
        executor: Nextflow executor name.
        docker_config: Optional Docker configuration mapping.
        verbose: Enable verbose debug output.

    Returns:
        Execution result object (currently ``NextflowResult``).
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


def run_script(
    nf_file,
    inputs=None,
    params=None,
    executor="local",
    docker_config=None,
    verbose=False,
):
    """Alias for ``run_module`` when executing raw scripts."""
    return run_module(
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
):
    """Execute an nf-core module via the public API.

    Args:
        module_id: Module identifier.
        request: Execution request describing module inputs.
        cache_dir: Directory for cached module artifacts.
        github_token: Optional GitHub token for authenticated requests.
        force_download: When ``True``, re-download the module.

    Returns:
        Execution result object (currently ``NextflowResult``).
    """
    return api.run_module(
        module_id,
        request,
        cache_dir=cache_dir,
        github_token=github_token,
        force_download=force_download,
    )


def read_output_file(file_path):
    """Read contents of an output file.

    Args:
        file_path: Path to the output file.

    Returns:
        File contents.

    Raises:
        OSError: If the file cannot be read.
    """
    return api.read_output_file(Path(file_path))
