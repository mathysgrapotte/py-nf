"""Public entry points for the pynf package (stubs).

This file mirrors ``src/pynf/__init__.py``.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pynf._core.result import NextflowResult
from pynf._core.types import DockerConfig, ExecutionRequest
from pynf._core.validation import validate_meta_map

__all__: list[str]


def run_script(
    nf_file: str | Path,
    inputs: Any = ...,
    params: Any = ...,
    executor: str = ...,
    docker_config: Mapping[str, Any] | DockerConfig | None = ...,
    verbose: bool = ...,
) -> NextflowResult: ...


def run_module(
    nf_file: str | Path,
    inputs: Any = ...,
    params: Any = ...,
    executor: str = ...,
    docker_config: Mapping[str, Any] | DockerConfig | None = ...,
    verbose: bool = ...,
) -> NextflowResult: ...


def run_nfcore_module(
    module_id: str,
    request: ExecutionRequest,
    cache_dir: Path = ...,
    github_token: str | None = ...,
    force_download: bool = ...,
) -> NextflowResult: ...


def read_output_file(file_path: str | Path) -> str: ...
