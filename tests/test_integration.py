#!/usr/bin/env python3

"""Integration tests for the py-nf package.

These tests validate that we can run a simple Nextflow script from Python and
capture outputs.

NOTE: This repo intentionally uses the functional API (ExecutionRequest →
execute_nextflow). The old NextflowEngine wrapper has been removed.
"""

from pathlib import Path

import pytest

from pynf import run_module
from pynf.execution import execute_nextflow
from pynf.types import ExecutionRequest


def nextflow_jar_available() -> bool:
    from pynf.runtime_config import resolve_nextflow_jar_path
    jar = resolve_nextflow_jar_path(None)
    return jar.exists()



@pytest.mark.skipif(not nextflow_jar_available(), reason="Nextflow JAR not present; run python setup_nextflow.py")
def test_basic_execute_nextflow() -> None:
    """Execute a basic Nextflow script via the functional API."""

    request = ExecutionRequest(script_path=Path("nextflow/tests/hello.nf"))
    result = execute_nextflow(request)

    report = result.get_execution_report()
    outputs = result.get_output_files()

    assert isinstance(report, dict)
    assert isinstance(outputs, list)


@pytest.mark.skipif(not nextflow_jar_available(), reason="Nextflow JAR not present; run python setup_nextflow.py")
def test_convenience_function() -> None:
    """The convenience run_module wrapper should still work."""

    result = run_module("nextflow/tests/hello.nf")
    assert isinstance(result.get_execution_report(), dict)


@pytest.mark.skipif(not nextflow_jar_available(), reason="Nextflow JAR not present; run python setup_nextflow.py")
def test_file_output_process_outputs_output_txt() -> None:
    """Ensure file-output-process.nf publishes output.txt."""

    request = ExecutionRequest(script_path=Path("nextflow_scripts/file-output-process.nf"))
    result = execute_nextflow(request)

    outputs = result.get_output_files()
    assert any(Path(path).name == "output.txt" for path in outputs), outputs


if __name__ == "__main__":
    raise SystemExit("Run with pytest")
