"""Public entry points for the pynf package.

This package is intentionally **functional-first**: most users should only need
``pynf`` (or ``pynf.api``) functions plus a couple of dataclasses.

Design principle:
- Keep the public surface small and easy to discover.
- Hide implementation details behind ``pynf.api``.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple

from . import api
from ._core.result import NextflowResult
from ._core.types import DockerConfig, ExecutionRequest
from ._core.validation import validate_meta_map


class ModuleResult(NamedTuple):
    output_files: list[str]
    workflow_outputs: list[dict[str, Any]]
    report: dict[str, Any]
    raw: NextflowResult


def run_script(
    nf_file: str | Path,
    inputs=None,
    params=None,
    executor: str = "local",
    docker_config: Mapping[str, Any] | DockerConfig | None = None,
    verbose: bool = False,
) -> NextflowResult:
    """Execute an arbitrary Nextflow script."""
    ...


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
    """Run an nf-core module using a keyword-argument (pythonic) calling style."""
    ...


def run_nfcore_module(
    module_id: str,
    request: ExecutionRequest,
    cache_dir: Path = api.DEFAULT_CACHE_DIR,
    github_token: str | None = None,
    force_download: bool = False,
) -> NextflowResult:
    """Download (if needed) and run an nf-core module."""
    ...


def read_output_file(file_path: str | Path) -> str:
    """Read contents of an output file."""
    ...
