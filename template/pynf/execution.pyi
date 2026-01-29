"""Execution orchestration that composes runtime, introspection, and outputs."""

from typing import Any

from pynf.types import ExecutionRequest

def execute_nextflow(
    request: ExecutionRequest, nextflow_jar_path: str | None = None
) -> Any:
    """Execute a Nextflow script and return a structured result.

    DEPENDS_ON:
    pynf.runtime_config.resolve_nextflow_jar_path
    pynf.runtime_config.assert_nextflow_jar_exists
    pynf.runtime_config.configure_logging
    pynf.jvm_bridge.start_jvm_if_needed
    pynf.jvm_bridge.load_nextflow_classes
    pynf.process_introspection.get_process_inputs
    pynf.validation.validate_inputs
    pynf.observer_events.WorkflowOutputCollector
    pynf.execution._set_params_from_inputs
    pynf.execution._configure_docker
    pynf.outputs.collect_paths_from_events
    pynf.outputs.collect_paths_from_workdirs

    EXTERNAL_DEPENDS_ON:
    jpype
    logging

    CHECKS:
    request.script_path must exist
    """
    ...

def _configure_docker(session: Any, docker_config: dict[str, Any]) -> None:
    """Apply docker configuration to the Nextflow session config.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    jpype
    """
    ...

def _set_params_from_inputs(
    session: Any, input_channels: list[dict], inputs: list[dict]
) -> None:
    """Map user inputs onto session params.

    DEPENDS_ON:
    pynf.execution._convert_to_java_type

    EXTERNAL_DEPENDS_ON:
    jpype
    """
    ...

def _convert_to_java_type(value: Any, param_type: str) -> Any:
    """Convert Python values into Java-compatible representations.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    jpype
    """
    ...
