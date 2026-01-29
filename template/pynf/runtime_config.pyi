"""Runtime configuration and environment resolution."""

from pathlib import Path

DEFAULT_NEXTFLOW_JAR_PATH: str

def resolve_nextflow_jar_path(explicit_path: str | None) -> Path:
    """Resolve the Nextflow fat JAR path from arg, env var, or default.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    os
    pathlib
    """
    ...

def assert_nextflow_jar_exists(jar_path: Path) -> None:
    """Raise an actionable error when the jar path is missing.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    pathlib

    CHECKS:
    jar_path must exist and be a file
    """
    ...

def configure_logging(verbose: bool) -> None:
    """Configure Python logging and best-effort Java logging.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    logging
    jpype
    """
    ...
