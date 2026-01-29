"""Regression tests for verbose mode.

The functional API supports verbose logging via ExecutionRequest.verbose.
"""

from pathlib import Path

import pytest

from pynf.execution import execute_nextflow
from pynf.types import ExecutionRequest


def nextflow_jar_available() -> bool:
    from pynf.runtime_config import resolve_nextflow_jar_path
    jar = resolve_nextflow_jar_path(None)
    return jar.exists()



@pytest.mark.skipif(not nextflow_jar_available(), reason="Nextflow JAR not present; run python setup_nextflow.py")
def test_verbose_mode_does_not_crash() -> None:
    request = ExecutionRequest(
        script_path=Path("nextflow_scripts/file-output-process.nf"),
        verbose=True,
    )
    result = execute_nextflow(request)
    assert isinstance(result.get_execution_report(), dict)
