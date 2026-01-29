"""Utilities for managing the JPype/JVM boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import jpype


def start_jvm_if_needed(jar_path: Path) -> None:
    """Start the JVM with the Nextflow JAR on the classpath.

    This helper ensures the JVM is bootstrapped exactly once so that later
    components can obtain Nextflow class proxies.

    Args:
        jar_path: Path to the Nextflow fat JAR.

    Example:
        >>> start_jvm_if_needed(Path("/tmp/nextflow.jar"))
    """
    if not jpype.isJVMStarted():
        jpype.startJVM(classpath=[str(jar_path)])


def load_nextflow_classes() -> dict[str, Any]:
    """Load the Nextflow Java classes required by the runtime.

    Returns:
        Mapping of class names to JPype class proxies.

    Example:
        >>> classes = load_nextflow_classes()
        >>> 'ScriptLoaderFactory' in classes
        True
    """
    return {
        "ScriptLoaderFactory": jpype.JClass("nextflow.script.ScriptLoaderFactory"),
        "Session": jpype.JClass("nextflow.Session"),
        "Channel": jpype.JClass("nextflow.Channel"),
        "TraceObserverV2": jpype.JClass("nextflow.trace.TraceObserverV2"),
        "ScriptMeta": jpype.JClass("nextflow.script.ScriptMeta"),
    }
