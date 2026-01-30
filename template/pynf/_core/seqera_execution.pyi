"""Seqera Platform execution helpers."""

from __future__ import annotations

from typing import Any

from .result import SeqeraResult
from .types import ExecutionRequest, ModulePaths

def execute_seqera_script(request: ExecutionRequest) -> SeqeraResult:
    """Execute a script remotely on Seqera Platform."""
    ...

def execute_seqera_module(
    request: ExecutionRequest, module_paths: ModulePaths
) -> SeqeraResult:
    """Execute an nf-core module remotely on Seqera Platform."""
    ...

def build_module_wrapper(
    module_paths: ModulePaths, input_groups: list[list[str]]
) -> str:
    """Build a DSL2 wrapper workflow for an nf-core module."""
    ...
