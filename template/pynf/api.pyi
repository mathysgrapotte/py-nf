"""Public API composition layer."""

from pathlib import Path
from typing import Any

from pynf.types import ExecutionRequest, ModuleId

DEFAULT_CACHE_DIR: Path

def run_script(request: ExecutionRequest, nextflow_jar_path: str | None = None) -> Any:
    """Execute an arbitrary Nextflow script.

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
    """Ensure a module is downloaded, then execute it.

    DEPENDS_ON:
    pynf.module_service.run_nfcore_module

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def list_modules(
    cache_dir: Path = DEFAULT_CACHE_DIR, github_token: str | None = None
) -> list[str]:
    """List available modules (with local caching).

    DEPENDS_ON:
    pynf.module_catalog.list_modules

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def list_submodules(module_id: ModuleId, github_token: str | None = None) -> list[str]:
    """List submodules for a module.

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

    DEPENDS_ON:
    pynf.module_service.get_module_inputs

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def get_rate_limit_status(github_token: str | None = None) -> dict:
    """Return GitHub API rate limit status.

    DEPENDS_ON:
    pynf.module_catalog.get_rate_limit_status

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...

def read_output_file(path: Path) -> str | None:
    """Read an output file's contents.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...
