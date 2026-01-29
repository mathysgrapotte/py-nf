"""Embedded Nextflow execution runtime (stubs)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pynf._core.result import NextflowResult
from pynf._core.types import ExecutionRequest

DEFAULT_NEXTFLOW_JAR_PATH: str

def resolve_nextflow_jar_path(explicit_path: str | None) -> Path: ...

def assert_nextflow_jar_exists(jar_path: Path) -> None: ...

def configure_logging(verbose: bool) -> None: ...

def start_jvm_if_needed(jar_path: Path) -> None: ...

def load_nextflow_classes() -> dict[str, Any]: ...

def to_java(value: Any, *, param_type: str | None = ...) -> Any: ...

def execute_nextflow(request: ExecutionRequest, nextflow_jar_path: str | None = ...) -> NextflowResult: ...
