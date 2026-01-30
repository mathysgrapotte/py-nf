"""Embedded Nextflow execution (JPype).

This module is the core runtime engine:
- resolve/validate Nextflow JAR
- start a JVM once
- load Nextflow classes
- execute a script
- validate/convert inputs
- collect workflow outputs via a TraceObserver proxy

Public entry point:
- :func:`execute_nextflow`"""

from __future__ import annotations

from typing import Any

def resolve_nextflow_jar_path(explicit_path: str | None) -> Path:
    """Resolve the Nextflow fat JAR path."""
    ...

def assert_nextflow_jar_exists(jar_path: Path) -> None:
    """Validate that the Nextflow JAR exists on disk."""
    ...

def configure_logging(verbose: bool) -> None:
    """Configure Python and Java logging verbosity (best-effort)."""
    ...

def start_jvm_if_needed(jar_path: Path) -> None:
    """Start the JVM with the Nextflow JAR on the classpath."""
    ...

def load_nextflow_classes() -> dict[str, Any]:
    """Load the Nextflow Java classes required by the runtime."""
    ...

def to_java(value: Any, *, param_type: str | None = None) -> Any:
    """Convert Python values into Java-friendly values for Nextflow."""
    ...

class WorkflowOutputCollector:
    """Collect workflow outputs, file publish events, and task workdirs."""
    ...

def get_process_inputs(script_loader: Any, script: Any, script_meta_cls: Any) -> list[dict]:
    """Extract process inputs using Nextflow's native metadata API."""
    ...

def managed_session(Session: Any, script_path: str) -> Iterator[Any]:
    """Create, initialize, start, and always destroy a Nextflow session."""
    ...

def registered_trace_observer(session: Any, observer_proxy: Any) -> Iterator[None]:
    """Register a TraceObserverV2 instance on a session (best-effort removal)."""
    ...

def execute_nextflow(request: ExecutionRequest, nextflow_jar_path: str | None = None) -> NextflowResult:
    """Execute a Nextflow script and capture structured runtime outputs."""
    ...

