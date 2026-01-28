"""Validation tests for multi-input nf-core modules.

These tests focus on input validation performed by the functional execution
pipeline.

They rely on the presence of the samtools/view test cache under
`test_nfcore_cache/`.
"""

from pathlib import Path

import pytest

from pynf.execution import execute_nextflow
from pynf.types import DockerConfig, ExecutionRequest


def nextflow_jar_available() -> bool:
    from pynf.runtime_config import resolve_nextflow_jar_path
    jar = resolve_nextflow_jar_path(None)
    return jar.exists()



MODULE_PATH = Path("test_nfcore_cache/samtools/view/main.nf")


def _docker_quay() -> DockerConfig:
    return DockerConfig(enabled=True, registry="quay.io", remove=True)


@pytest.mark.skipif(not nextflow_jar_available(), reason="Nextflow JAR not present; run python setup_nextflow.py")
def test_multi_input_validation_rejects_missing_meta_id() -> None:
    request = ExecutionRequest(
        script_path=MODULE_PATH,
        inputs=[{"meta": {}, "input": ["test.bam"], "index": []}],
        docker=_docker_quay(),
    )
    with pytest.raises(ValueError):
        execute_nextflow(request)


@pytest.mark.skipif(not nextflow_jar_available(), reason="Nextflow JAR not present; run python setup_nextflow.py")
def test_multi_input_validation_accepts_meta_id() -> None:
    request = ExecutionRequest(
        script_path=MODULE_PATH,
        inputs=[{"meta": {"id": "sample1"}, "input": ["test.bam"], "index": []}],
        docker=_docker_quay(),
    )
    # This may still fail later if test inputs are missing; the key assertion here
    # is that validation passes and we reach execution.
    try:
        execute_nextflow(request)
    except Exception as exc:
        # If runtime fails due to missing files/containers, that's acceptable for
        # this unit focusing on validation.
        assert not isinstance(exc, ValueError)
