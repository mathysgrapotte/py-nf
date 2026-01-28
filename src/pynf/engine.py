"""Backward-compatible engine wrapper for Nextflow execution."""

from __future__ import annotations

import logging
from pathlib import Path
from collections.abc import Mapping, Sequence
from typing import Any

from dotenv import load_dotenv

from .execution import execute_nextflow
from .jvm_bridge import load_nextflow_classes, start_jvm_if_needed
from .process_introspection import get_process_inputs
from .runtime_config import assert_nextflow_jar_exists, resolve_nextflow_jar_path
from .types import DockerConfig, ExecutionRequest
from .validation import validate_meta_map as _validate_meta_map

load_dotenv()

logger = logging.getLogger(__name__)


def validate_meta_map(
    meta: Mapping[str, Any], required_fields: Sequence[str] | None = None
) -> None:
    """Validate that required meta fields exist.

    Args:
        meta: Metadata mapping to validate.
        required_fields: Optional list of required keys. Defaults to ``["id"]``.

    Raises:
        ValueError: If any required fields are missing.
    """
    _validate_meta_map(meta, required_fields)


class NextflowEngine:
    """Compatibility wrapper around the functional execution API.

    This class retains the previous object-oriented interface while delegating
    actual execution to ``pynf.execution.execute_nextflow``.
    """

    def __init__(self, nextflow_jar_path: str | None = None) -> None:
        jar_path = resolve_nextflow_jar_path(nextflow_jar_path)
        assert_nextflow_jar_exists(jar_path)
        start_jvm_if_needed(jar_path)

        classes = load_nextflow_classes()
        self.ScriptLoaderFactory = classes["ScriptLoaderFactory"]
        self.ScriptMeta = classes["ScriptMeta"]
        self._jar_path = jar_path

    def load_script(self, nf_file_path: str | Path) -> Path:
        """Return a ``Path`` instance for the Nextflow script.

        Args:
            nf_file_path: Script path or path-like object.

        Returns:
            ``Path`` pointing at the script.
        """
        return Path(nf_file_path)

    def execute(
        self,
        script_path: str | Path,
        executor: str = "local",
        params: Mapping[str, Any] | None = None,
        inputs: list[dict] | None = None,
        config: Mapping[str, Any] | None = None,
        docker_config: Mapping[str, Any] | DockerConfig | None = None,
        verbose: bool = False,
    ):
        """Execute a Nextflow script with optional inputs and parameters.

        Args:
            script_path: Path to the Nextflow script.
            executor: Nextflow executor name.
            params: Mapping of script parameters.
            inputs: List of input group mappings.
            config: Reserved for additional Nextflow configuration.
            docker_config: Optional Docker configuration mapping.
            verbose: Enable verbose debug output.

        Returns:
            Execution result object (currently ``NextflowResult``).
        """
        del config
        request = ExecutionRequest(
            script_path=Path(script_path),
            executor=executor,
            params=params,
            inputs=inputs,
            docker=_coerce_docker_config(docker_config),
            verbose=verbose,
        )
        return execute_nextflow(request, nextflow_jar_path=str(self._jar_path))

    def _get_process_inputs(self, loader: Any, script: Any) -> list[dict]:
        """Extract input channel definitions using native Nextflow metadata.

        Args:
            loader: Parsed script loader instance.
            script: Script instance returned by ``loader.getScript()``.

        Returns:
            List of input channel definitions.
        """
        return get_process_inputs(loader, script, self.ScriptMeta)


def _coerce_docker_config(
    docker_config: Mapping[str, Any] | DockerConfig | None,
) -> DockerConfig | None:
    """Normalize docker configuration mappings into ``DockerConfig``.

    Args:
        docker_config: Docker configuration mapping or dataclass.

    Returns:
        ``DockerConfig`` instance or ``None``.
    """
    if docker_config is None:
        return None
    if isinstance(docker_config, DockerConfig):
        return docker_config

    return DockerConfig(
        enabled=bool(docker_config.get("enabled", True)),
        registry=docker_config.get("registry"),
        registry_override=docker_config.get("registryOverride")
        if "registryOverride" in docker_config
        else docker_config.get("registry_override"),
        remove=docker_config.get("remove"),
        run_options=docker_config.get("runOptions")
        if "runOptions" in docker_config
        else docker_config.get("run_options"),
    )
