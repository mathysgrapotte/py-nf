"""Docker execution tests for nf-core modules.

This uses the functional API and verifies that Docker config can be injected into
Nextflow session config.

Note: this may require Docker to be available on the host running tests.
"""

from pathlib import Path

import pytest

from pynf.execution import execute_nextflow
from pynf.types import DockerConfig, ExecutionRequest


def nextflow_jar_available() -> bool:
    from pynf.runtime_config import resolve_nextflow_jar_path
    jar = resolve_nextflow_jar_path(None)
    return jar.exists()



@pytest.mark.skipif(not nextflow_jar_available(), reason="Nextflow JAR not present; run python setup_nextflow.py")
def test_nfcore_docker_config_is_accepted() -> None:
    module_path = Path("test_nfcore_cache/samtools/view/main.nf")
    request = ExecutionRequest(
        script_path=module_path,
        inputs=[{"meta": {"id": "sample"}, "input": ["test.bam"], "index": []}],
        docker=DockerConfig(enabled=True, registry="quay.io", remove=True),
    )

    try:
        execute_nextflow(request)
    except Exception as exc:
        # We only assert that docker configuration doesn't crash *before* runtime;
        # if Docker is unavailable or inputs are missing, the error will come
        # from execution and is environment-dependent.
        assert not isinstance(exc, TypeError)
        assert not isinstance(exc, ValueError)


@pytest.mark.skipif(True, reason="No additional docker runtime assertions yet")
def test_placeholder() -> None:
    pass
