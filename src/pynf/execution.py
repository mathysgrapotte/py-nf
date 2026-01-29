"""Execution orchestration that composes runtime, introspection, and outputs."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

import jpype

from .jvm_bridge import load_nextflow_classes, start_jvm_if_needed
from .observer_events import WorkflowOutputCollector
from .process_introspection import get_process_inputs
from .session_lifecycle import managed_session, registered_trace_observer
from .jvm_values import to_java
from .runtime_config import (
    assert_nextflow_jar_exists,
    configure_logging,
    resolve_nextflow_jar_path,
)
from ._core.types import DockerConfig, ExecutionRequest
from ._core.validation import validate_inputs

logger = logging.getLogger(__name__)


def execute_nextflow(
    request: ExecutionRequest, nextflow_jar_path: str | None = None
) -> Any:
    """Execute a Nextflow script and capture structured runtime outputs.

    This function drives the full lifecycle: validating the request, ensuring the
    JVM is bootstrapped, configuring logging, injecting parameters input groups,
    wiring observers, and finally returning the wrapped ``NextflowResult``.

    Args:
        request: Immutable request describing the script execution.
        nextflow_jar_path: Optional override for the Nextflow JAR path.

    Returns:
        Execution result object (currently ``NextflowResult``).

    Example:
        >>> request = ExecutionRequest(script_path=Path("main.nf"))
        >>> result = execute_nextflow(request)
        >>> result.workflow_event_names()
        ['workflowFinished']
    """
    jar_path = resolve_nextflow_jar_path(nextflow_jar_path)
    assert_nextflow_jar_exists(jar_path)
    start_jvm_if_needed(jar_path)
    configure_logging(request.verbose)

    classes = load_nextflow_classes()
    ScriptLoaderFactory = classes["ScriptLoaderFactory"]
    Session = classes["Session"]
    TraceObserverV2 = classes["TraceObserverV2"]
    ScriptMeta = classes["ScriptMeta"]

    from .result import NextflowResult

    with managed_session(Session, str(request.script_path)) as session:
        if request.docker:
            _configure_docker(session, request.docker)

        if request.params:
            for key, value in request.params.items():
                session.getBinding().setVariable(key, value)

        loader = ScriptLoaderFactory.create(session)
        java_path = jpype.java.nio.file.Paths.get(str(request.script_path))
        loader.parse(java_path)
        script = loader.getScript()

        input_channels = get_process_inputs(loader, script, ScriptMeta)
        logger.debug("Discovered input channels: %s", input_channels)

        if request.inputs:
            validate_inputs(request.inputs, input_channels)
            _set_params_from_inputs(session, input_channels, request.inputs)

        collector = WorkflowOutputCollector()
        observer_proxy = jpype.JProxy(TraceObserverV2, inst=collector)

        with registered_trace_observer(session, observer_proxy):
            loader.runScript()
            session.fireDataflowNetwork(False)
            session.await_()

        # Snapshot values *before* session teardown.
        work_dir = str(session.getWorkDir())
        stats = session.getStatsObserver().getStats()
        report = {
            "completed_tasks": stats.getSucceededCount(),
            "failed_tasks": stats.getFailedCount(),
            "work_dir": work_dir,
        }

    # Session destroyed here.
    return NextflowResult(
        workflow_events=collector.workflow_events(),
        file_events=collector.file_events(),
        task_workdirs=collector.task_workdirs(),
        execution_report=report,
        work_dir=work_dir,
    )


def _configure_docker(session: Any, docker_config: DockerConfig) -> None:
    """Apply Docker configuration to the Nextflow session config.

    Args:
        session: Nextflow session object.
        docker_config: Docker configuration values.

    Example:
        >>> config = DockerConfig(enabled=True, registry="quay.io")
        >>> _configure_docker(session, config)
    """
    HashMap = jpype.JClass("java.util.HashMap")
    config = session.getConfig()

    if not config.containsKey("docker"):
        docker_map = HashMap()
        config.put("docker", docker_map)
    else:
        docker_map = config.get("docker")

    docker_map.put("enabled", docker_config.enabled)

    if docker_config.registry is not None:
        docker_map.put("registry", docker_config.registry)
    if docker_config.registry_override is not None:
        docker_map.put("registryOverride", docker_config.registry_override)
    if docker_config.run_options is not None:
        docker_map.put("runOptions", docker_config.run_options)
    if docker_config.remove is not None:
        docker_map.put("remove", docker_config.remove)


def _set_params_from_inputs(
    session: Any,
    input_channels: Sequence[dict],
    inputs: Sequence[Mapping[str, Any]],
) -> None:
    """Map user inputs onto the Nextflow session parameters.

    Matches each input group to the channel definitions discovered via introspection
    and coerces Python values into Nextflow-friendly types before inserting them
    into the session binding.

    Args:
        session: Nextflow session instance.
        input_channels: Expected channel structures from the script.
        inputs: User-provided input groups.

    Example:
        >>> _set_params_from_inputs(session, input_channels, [{"reads": "sample.fa"}])
    """
    params_obj = session.getParams()

    if not input_channels or not inputs:
        return

    for input_dict, channel_info in zip(inputs, input_channels):
        channel_params = channel_info.get("params", [])
        for param_info in channel_params:
            param_name = param_info["name"]
            param_type = param_info["type"]

            if param_name not in input_dict:
                continue

            param_value = input_dict[param_name]
            params_obj.put(param_name, to_java(param_value, param_type=param_type))


