"""Execution orchestration that composes runtime, introspection, and outputs."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

import jpype

from .jvm_bridge import load_nextflow_classes, start_jvm_if_needed
from .observer_events import WorkflowOutputCollector
from .process_introspection import get_process_inputs
from .runtime_config import (
    assert_nextflow_jar_exists,
    configure_logging,
    resolve_nextflow_jar_path,
)
from .types import DockerConfig, ExecutionRequest
from .validation import validate_inputs

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

    session = Session()
    if request.docker:
        _configure_docker(session, request.docker)

    ArrayList = jpype.JClass("java.util.ArrayList")
    ScriptFile = jpype.JClass("nextflow.script.ScriptFile")
    script_file = ScriptFile(jpype.java.nio.file.Paths.get(str(request.script_path)))
    session.init(script_file, ArrayList(), None, None)
    session.start()

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
    observer_registered = _register_output_observer(session, observer_proxy)

    try:
        loader.runScript()
        session.fireDataflowNetwork(False)
        session.await_()
    finally:
        if observer_registered:
            _unregister_output_observer(session, observer_proxy)
        session.destroy()

    from .result import NextflowResult

    return NextflowResult(
        script,
        session,
        loader,
        workflow_events=collector.workflow_events(),
        file_events=collector.file_events(),
        task_workdirs=collector.task_workdirs(),
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
            params_obj.put(param_name, _convert_to_java_type(param_value, param_type))


def _convert_to_java_type(value: Any, param_type: str) -> Any:
    """Convert Python values to Java-compatible representations.

    Args:
        value: Python value to convert.
        param_type: Nextflow parameter type (e.g., ``path``).

    Returns:
        Java-compatible value suitable for Nextflow.

    Example:
        >>> _convert_to_java_type(Path("sample.fastq"), "path")
        'sample.fastq'
    """
    HashMap = jpype.JClass("java.util.HashMap")

    if value is None:
        return None
    if isinstance(value, dict):
        meta_map = HashMap()
        for key, val in value.items():
            meta_map.put(key, val)
        return meta_map
    if isinstance(value, list):
        return ",".join(str(v) for v in value)
    if param_type == "path":
        return str(value)
    return value


def _register_output_observer(session: Any, observer: Any) -> bool:
    """Register an output observer with the Nextflow session.

    Args:
        session: Nextflow session instance.
        observer: JPype proxy implementing TraceObserverV2.

    Returns:
        ``True`` if the observer was registered successfully.
    """
    return _mutate_observers(session, observer, add=True)


def _unregister_output_observer(session: Any, observer: Any) -> None:
    """Unregister an output observer from the Nextflow session.

    Args:
        session: Nextflow session instance.
        observer: JPype proxy implementing TraceObserverV2.
    """
    _mutate_observers(session, observer, add=False)


def _mutate_observers(session: Any, observer: Any, add: bool) -> bool:
    """Add or remove a TraceObserverV2 instance from the session.

    Args:
        session: Nextflow session instance.
        observer: JPype proxy instance implementing TraceObserverV2.
        add: When ``True``, add the observer; otherwise remove it.

    Returns:
        ``True`` if the mutation succeeded.
    """
    session_class = session.getClass()
    field = session_class.getDeclaredField("observersV2")
    field.setAccessible(True)
    observers = field.get(session)
    if add:
        observers.add(observer)
    else:
        observers.remove(observer)
    field.set(session, observers)
    return True
