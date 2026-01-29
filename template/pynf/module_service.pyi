"""High-level module workflows that orchestrate catalog, download, and execution."""

from pathlib import Path
from typing import Any

from pynf.types import ExecutionRequest, ModuleId, ModulePaths

def ensure_module(
    cache_dir: Path,
    module_id: ModuleId,
    github_token: str | None,
    force: bool = False,
) -> ModulePaths:
    """Ensure a module is available locally.

    DEPENDS_ON:
    pynf.module_downloader.download_module

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def inspect_module(
    cache_dir: Path, module_id: ModuleId, github_token: str | None
) -> dict[str, Any]:
    """Inspect a module's metadata and script preview.

    DEPENDS_ON:
    pynf.module_service.ensure_module
    pynf.module_service._read_yaml
    pynf.module_service._preview_lines

    EXTERNAL_DEPENDS_ON:
    yaml
    pathlib
    """
    ...

def get_module_inputs(
    cache_dir: Path, module_id: ModuleId, github_token: str | None
) -> list[dict]:
    """Get module inputs via Nextflow native introspection.

    DEPENDS_ON:
    pynf.module_service.ensure_module
    pynf.execution.execute_nextflow
    pynf.module_service._introspect_only_request

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...

def run_nfcore_module(
    cache_dir: Path,
    module_id: ModuleId,
    github_token: str | None,
    request: ExecutionRequest,
    force_download: bool = False,
) -> Any:
    """Download (if needed) and execute an nf-core module.

    DEPENDS_ON:
    pynf.module_service.ensure_module
    pynf.execution.execute_nextflow

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...

def _read_yaml(path: Path) -> dict:
    """Read YAML into a dictionary.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    yaml
    pathlib
    """
    ...

def _preview_lines(path: Path, limit: int = 20) -> list[str]:
    """Read a file and return the first N lines.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def _introspect_only_request(script_path: Path) -> ExecutionRequest:
    """Build a request used only for introspection.

    DEPENDS_ON:
    pynf.types.ExecutionRequest

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...
