"""JPype/JVM boundary utilities."""

from pathlib import Path
from typing import Any

def start_jvm_if_needed(jar_path: Path) -> None:
    """Start the JVM with the provided JAR on the classpath.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    jpype
    pathlib
    """
    ...

def load_nextflow_classes() -> dict[str, Any]:
    """Load and return the Nextflow Java classes used by the engine.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    jpype
    """
    ...
