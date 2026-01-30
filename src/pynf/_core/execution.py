"""Embedded Nextflow execution (JPype).

This module is the core runtime engine:
- resolve/validate Nextflow JAR
- start a JVM once
- load Nextflow classes
- execute a script
- validate/convert inputs
- collect workflow outputs via a TraceObserver proxy

Public entry point:
- :func:`execute_nextflow`
"""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import jpype

from .types import DockerConfig, ExecutionRequest
from .seqera_execution import execute_seqera_script
from .validation import validate_inputs
from .result import NextflowResult

logger = logging.getLogger(__name__)

DEFAULT_NEXTFLOW_JAR_PATH = "nextflow/build/releases/nextflow-25.10.0-one.jar"


def resolve_nextflow_jar_path(explicit_path: str | None) -> Path:
    """Resolve the Nextflow fat JAR path."""
    if explicit_path:
        return Path(explicit_path)
    return Path(os.getenv("NEXTFLOW_JAR_PATH", DEFAULT_NEXTFLOW_JAR_PATH))


def assert_nextflow_jar_exists(jar_path: Path) -> None:
    """Validate that the Nextflow JAR exists on disk."""
    if jar_path.exists():
        return

    jar_path_str = str(jar_path)
    error_msg = (
        f"\n{'=' * 70}\n"
        f"ERROR: Nextflow JAR not found at: {jar_path_str}\n"
        f"{'=' * 70}\n\n"
        "This project requires a Nextflow fat JAR to run.\n\n"
        "To set up Nextflow automatically, run:\n"
        "    python setup_nextflow.py\n\n"
        "Alternatively, set NEXTFLOW_JAR_PATH to a built JAR.\n"
        f"{'=' * 70}\n"
    )
    raise FileNotFoundError(error_msg)


def configure_logging(verbose: bool) -> None:
    """Configure Python and Java logging verbosity (best-effort)."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s", force=True)

    if verbose:
        return

    if not jpype.isJVMStarted():  # type: ignore[attr-defined]
        return

    try:
        logger_factory = jpype.JClass("org.slf4j.LoggerFactory")
        level_cls = jpype.JClass("ch.qos.logback.classic.Level")
        context = logger_factory.getILoggerFactory()
        root_logger = context.getLogger("ROOT")
        root_logger.setLevel(level_cls.WARN)
    except Exception:
        return


def start_jvm_if_needed(jar_path: Path) -> None:
    """Start the JVM with the Nextflow JAR on the classpath."""
    if not jpype.isJVMStarted():
        jpype.startJVM(classpath=[str(jar_path)])


def load_nextflow_classes() -> dict[str, Any]:
    """Load the Nextflow Java classes required by the runtime."""
    return {
        "ScriptLoaderFactory": jpype.JClass("nextflow.script.ScriptLoaderFactory"),
        "Session": jpype.JClass("nextflow.Session"),
        "TraceObserverV2": jpype.JClass("nextflow.trace.TraceObserverV2"),
        "ScriptMeta": jpype.JClass("nextflow.script.ScriptMeta"),
    }


def to_java(value: Any, *, param_type: str | None = None) -> Any:
    """Convert Python values into Java-friendly values for Nextflow."""
    if value is None:
        return None

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Mapping):
        HashMap = jpype.JClass("java.util.HashMap")
        m = HashMap()
        for k, v in value.items():
            m.put(str(k), to_java(v))
        return m

    if isinstance(value, (list, tuple, set)):
        ArrayList = jpype.JClass("java.util.ArrayList")
        arr = ArrayList()
        for item in value:
            arr.add(to_java(item, param_type=param_type))
        return arr

    return value


class WorkflowOutputCollector:
    """Collect workflow outputs, file publish events, and task workdirs."""

    def __init__(self) -> None:
        self._workflow_events: list[dict] = []
        self._file_events: list[dict] = []
        self._task_workdirs: list[str] = []

    def onTaskComplete(self, event: Any) -> None:  # noqa: N802
        self._record_task_workdir(event)

    def onTaskCached(self, event: Any) -> None:  # noqa: N802
        self._record_task_workdir(event)

    def onWorkflowOutput(self, event: Any) -> None:  # noqa: N802
        self._workflow_events.append(
            {
                "name": event.getName(),
                "value": event.getValue(),
                "index": event.getIndex(),
            }
        )

    def onFilePublish(self, event: Any) -> None:  # noqa: N802
        self._file_events.append(
            {
                "target": event.getTarget(),
                "source": event.getSource(),
                "labels": event.getLabels(),
            }
        )

    def __getattr__(self, name: str):
        # Nextflow TraceObserverV2 has many callback methods; we only care about a few.
        if name.startswith("on"):

            def _noop(*args: Any, **kwargs: Any) -> None:
                return None

            return _noop
        raise AttributeError(name)

    def workflow_events(self) -> list[dict]:
        return list(self._workflow_events)

    def file_events(self) -> list[dict]:
        return list(self._file_events)

    def task_workdirs(self) -> list[str]:
        return list(self._task_workdirs)

    def _record_task_workdir(self, event: Any) -> None:
        try:
            handler = event.getHandler()
            task = handler.getTask()
            self._task_workdirs.append(str(task.getWorkDir()))
        except Exception:
            return


def get_process_inputs(
    script_loader: Any, script: Any, script_meta_cls: Any
) -> list[dict]:
    """Extract process inputs using Nextflow's native metadata API."""
    script_loader.setModule(True)

    script_meta = script_meta_cls.get(script)
    process_names = script_meta.getProcessNames()

    if not process_names:
        was_module = script_meta.isModule()
        script_meta.setModule(True)
        try:
            script_loader.runScript()
        finally:
            script_meta.setModule(was_module)
        process_names = script_meta.getProcessNames()

    if not process_names:
        return []

    all_inputs: list[dict] = []
    for process_name in process_names:
        process_def = script_meta.getProcess(process_name)
        all_inputs.extend(_extract_process_inputs(process_def))

    return all_inputs


def _extract_process_inputs(process_def: Any) -> list[dict]:
    process_config = process_def.getProcessConfig()
    inputs = process_config.getInputs()
    return [_build_channel_info(inp) for inp in inputs]


def _build_channel_info(input_def: Any) -> dict:
    channel_info = {"type": str(input_def.getTypeName()), "params": []}

    if hasattr(input_def, "getInner") and input_def.getInner() is not None:
        inner = input_def.getInner()
        channel_info["params"] = [
            {"type": str(component.getTypeName()), "name": str(component.getName())}
            for component in inner
        ]
    else:
        channel_info["params"].append(
            {"type": str(input_def.getTypeName()), "name": str(input_def.getName())}
        )

    return channel_info


@contextmanager
def managed_session(Session: Any, script_path: str) -> Iterator[Any]:
    """Create, initialize, start, and always destroy a Nextflow session."""
    session = Session()

    ArrayList = jpype.JClass("java.util.ArrayList")
    ScriptFile = jpype.JClass("nextflow.script.ScriptFile")
    script_file = ScriptFile(jpype.java.nio.file.Paths.get(script_path))

    session.init(script_file, ArrayList(), None, None)
    session.start()

    try:
        yield session
    finally:
        try:
            session.destroy()
        except Exception:
            pass


@contextmanager
def registered_trace_observer(session: Any, observer_proxy: Any) -> Iterator[None]:
    """Register a TraceObserverV2 instance on a session (best-effort removal)."""
    observers = None
    try:
        field = session.getClass().getDeclaredField("observersV2")
        field.setAccessible(True)
        observers = field.get(session)
        observers.add(observer_proxy)
        yield
    finally:
        if observers is None:
            return
        try:
            observers.remove(observer_proxy)
        except Exception:
            pass


def execute_nextflow(
    request: ExecutionRequest, nextflow_jar_path: str | None = None
) -> NextflowResult:
    """Execute a Nextflow script and capture structured runtime outputs."""
    jar_path = resolve_nextflow_jar_path(nextflow_jar_path)
    assert_nextflow_jar_exists(jar_path)
    start_jvm_if_needed(jar_path)
    configure_logging(request.verbose)

    classes = load_nextflow_classes()
    ScriptLoaderFactory = classes["ScriptLoaderFactory"]
    Session = classes["Session"]
    TraceObserverV2 = classes["TraceObserverV2"]
    ScriptMeta = classes["ScriptMeta"]

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

        # Snapshot values before session teardown.
        work_dir = str(session.getWorkDir())
        stats = session.getStatsObserver().getStats()
        report = {
            "completed_tasks": stats.getSucceededCount(),
            "failed_tasks": stats.getFailedCount(),
            "work_dir": work_dir,
        }

    return NextflowResult(
        workflow_events=collector.workflow_events(),
        file_events=collector.file_events(),
        task_workdirs=collector.task_workdirs(),
        execution_report=report,
        work_dir=work_dir,
    )


def execute_request(
    request: ExecutionRequest, nextflow_jar_path: str | None = None
) -> Any:
    """Dispatch execution to local or remote backend."""
    if request.backend == "seqera":
        return execute_seqera_script(request)
    return execute_nextflow(request, nextflow_jar_path=nextflow_jar_path)


def _configure_docker(session: Any, docker_config: DockerConfig) -> None:
    """Apply Docker configuration to the Nextflow session config."""
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
