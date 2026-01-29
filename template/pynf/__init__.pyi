"""Public entry points for the pynf package.

This package is intentionally **functional-first**: most users should only need
``pynf`` (or ``pynf.api``) functions plus a couple of dataclasses.

Design principle:
- Keep the public surface small and easy to discover.
- Hide implementation details behind ``pynf.api``."""

from __future__ import annotations

from typing import Any

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
    ``NextflowResult``."""
    ...

def run_module(
    nf_file: str | Path,
    inputs=None,
    params=None,
    executor: str = "local",
    docker_config: Mapping[str, Any] | DockerConfig | None = None,
    verbose: bool = False,
) -> NextflowResult:
    """Alias for :func:`run_script`.

Kept for users who prefer the "run a module" naming even for raw scripts."""
    ...

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
    ``NextflowResult``."""
    ...

def read_output_file(file_path: str | Path) -> str:
    """Read contents of an output file."""
    ...

