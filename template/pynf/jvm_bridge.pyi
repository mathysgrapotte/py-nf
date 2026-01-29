"""JPype/JVM boundary utilities."""

from pathlib import Path
from typing import Any

def start_jvm_if_needed(jar_path: Path) -> None:
    """Start the JVM with the provided JAR on the classpath.

    Example:
        >>> start_jvm_if_needed(Path("/tmp/nextflow.jar"))

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    jpype
    pathlib
    """
    ...

def load_nextflow_classes() -> dict[str, Any]:
    """Load and return the Nextflow Java classes used by the engine.

    Example:
        >>> classes = load_nextflow_classes()
        >>> 'ScriptLoaderFactory' in classes

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    jpype
    """
    ...
