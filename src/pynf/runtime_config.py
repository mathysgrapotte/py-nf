"""Runtime configuration and logging setup for Nextflow execution."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import jpype

DEFAULT_NEXTFLOW_JAR_PATH = "nextflow/build/releases/nextflow-25.10.0-one.jar"


def resolve_nextflow_jar_path(explicit_path: str | None) -> Path:
    """Resolve the Nextflow fat JAR path from arg, env var, or default."""
    if explicit_path:
        return Path(explicit_path)
    return Path(os.getenv("NEXTFLOW_JAR_PATH", DEFAULT_NEXTFLOW_JAR_PATH))


def assert_nextflow_jar_exists(jar_path: Path) -> None:
    """Raise an actionable error when the JAR is missing."""
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
        "This will clone and build Nextflow for you.\n\n"
        "Alternatively, you can set up manually:\n"
        "1. Clone: git clone https://github.com/nextflow-io/nextflow.git\n"
        "2. Build: cd nextflow && make pack\n"
        "3. Update .env with the JAR path\n"
        f"{'=' * 70}\n"
    )
    raise FileNotFoundError(error_msg)


def configure_logging(verbose: bool) -> None:
    """Configure Python logging and best-effort Java logging."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        force=True,
    )

    if verbose:
        return

    try:
        logger_factory = jpype.JClass("org.slf4j.LoggerFactory")
        level_cls = jpype.JClass("ch.qos.logback.classic.Level")
        context = logger_factory.getILoggerFactory()
        root_logger = context.getLogger("ROOT")
        root_logger.setLevel(level_cls.WARN)
    except Exception:
        # If Java logging configuration fails, continue quietly.
        pass
