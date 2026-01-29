"""Public API composition layer."""

from pathlib import Path
from typing import Any

from pynf.types import ExecutionRequest, ModuleId

DEFAULT_CACHE_DIR: Path

def run_script(request: ExecutionRequest, nextflow_jar_path: str | None = None) -> Any:
    """Execute an arbitrary Nextflow script using the provided request.

    Args:
        request: Execution request describing the script to run.
        nextflow_jar_path: Optional override for the Nextflow JAR path.

    Example:
        >>> request = ExecutionRequest(script_path=Path("main.nf"), executor="local")
        >>> run_script(request)
        NextflowResult(...)

    DEPENDS_ON:
    pynf.execution.execute_nextflow

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...

def run_module(
    module_id: ModuleId,
    request: ExecutionRequest,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    github_token: str | None = None,
    force_download: bool = False,
) -> Any:
    """Ensure a module is downloaded and then execute it.

    Args:
        module_id: Module identifier.
        request: Execution request describing execution inputs and options.
        cache_dir: Cache directory for module artifacts.
        github_token: Optional GitHub token for authenticated requests.
        force_download: When ``True``, re-download the module even if cached.

    Example:
        >>> request = ExecutionRequest(script_path=Path("main.nf"), executor="local")
        >>> run_module("nf-core/fastqc", request)
        NextflowResult(...)

    DEPENDS_ON:
    pynf.module_service.run_nfcore_module

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def list_modules(
    cache_dir: Path = DEFAULT_CACHE_DIR, github_token: str | None = None
) -> list[str]:
    """List available modules using the cached catalog.

    Args:
        cache_dir: Cache directory for module metadata.
        github_token: Optional GitHub token for authenticated requests.

    Example:
        >>> list_modules(Path("/tmp/modules"))
        ['nf-core/fastqc', 'nf-core/samtools']

    DEPENDS_ON:
    pynf.module_catalog.list_modules

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def list_submodules(module_id: ModuleId, github_token: str | None = None) -> list[str]:
    """List submodules for a module identifier.

    Args:
        module_id: Module identifier.
        github_token: Optional GitHub token for authenticated requests.

    Example:
        >>> list_submodules("nf-core/samtools")
        ['view', 'sort']

    DEPENDS_ON:
    pynf.module_catalog.list_submodules

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...

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

    Example:
        >>> inspect_module("nf-core/fastqc")
        {'name': 'nf-core/fastqc', 'meta': {...}, ...}

    DEPENDS_ON:
    pynf.module_service.inspect_module

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def get_module_inputs(
    module_id: ModuleId,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    github_token: str | None = None,
) -> list[dict]:
    """Return module inputs via native introspection.

    Args:
        module_id: Module identifier.
        cache_dir: Cache directory for module artifacts.
        github_token: Optional GitHub token for authenticated requests.

    Example:
        >>> get_module_inputs("nf-core/fastqc")
        [{'type': 'tuple', 'params': [{'type': 'val', 'name': 'meta'}]}, ...]

    DEPENDS_ON:
    pynf.module_service.get_module_inputs

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def get_rate_limit_status(github_token: str | None = None) -> dict:
    """Return GitHub API rate limit status.

    Args:
        github_token: Optional GitHub token for authenticated requests.

    Example:
        >>> get_rate_limit_status()
        {'limit': 60, 'remaining': 59, 'reset_time': 1700000000}

    DEPENDS_ON:
    pynf.module_catalog.get_rate_limit_status

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...

def read_output_file(path: Path) -> str | None:
    """Read an output file's contents.

    Args:
        path: Path to the output file.

    Example:
        >>> read_output_file(Path("work/output.txt"))
        '...later output...'

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...
