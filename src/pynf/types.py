"""Core data types for the pynf runtime and module workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

ModuleId = str
ParamName = str
ParamType = str

ParamValue = Any
ParamsMap = Mapping[str, Any]

InputGroup = Mapping[ParamName, ParamValue]
InputGroups = Sequence[InputGroup]


@dataclass(frozen=True)
class ChannelParam:
    """Describe a single parameter within a Nextflow input channel.

    Attributes:
        type: The Nextflow parameter type (e.g., ``val`` or ``path``).
        name: The parameter name as declared in the module.
    """

    type: ParamType
    name: ParamName


@dataclass(frozen=True)
class ChannelInfo:
    """Describe a Nextflow input channel and its parameters.

    Attributes:
        type: The channel type (e.g., ``tuple``).
        params: Ordered parameter definitions within the channel.
    """

    type: ParamType
    params: Sequence[ChannelParam]


@dataclass(frozen=True)
class ModulePaths:
    """Resolve and store local paths for a cached nf-core module.

    Attributes:
        module_id: The nf-core module identifier (e.g., ``samtools/view``).
        module_dir: Directory containing the module files.
        main_nf: Path to the module ``main.nf``.
        meta_yml: Path to the module ``meta.yml``.
    """

    module_id: ModuleId
    module_dir: Path
    main_nf: Path
    meta_yml: Path


@dataclass(frozen=True)
class DockerConfig:
    """Docker configuration values for Nextflow execution.

    Attributes:
        enabled: Whether Docker is enabled in the Nextflow session.
        registry: Optional Docker registry override (e.g., ``quay.io``).
        registry_override: Whether to override registry values in image names.
        remove: Whether to auto-remove containers after execution.
        run_options: Extra options to pass to Docker at runtime.
    """

    enabled: bool = True
    registry: str | None = None
    registry_override: bool | None = None
    remove: bool | None = None
    run_options: str | None = None


@dataclass(frozen=True)
class ExecutionRequest:
    """Immutable request describing a Nextflow execution.

    Attributes:
        script_path: Path to the Nextflow script to execute.
        executor: Executor identifier (e.g., ``local``).
        params: Script parameters to set on the Nextflow binding.
        inputs: Optional input group mappings to map into ``session.params``.
        docker: Docker execution configuration, when enabled.
        verbose: Whether to enable verbose logging.
    """

    script_path: Path
    executor: str = "local"
    params: ParamsMap | None = None
    inputs: InputGroups | None = None
    docker: DockerConfig | None = None
    verbose: bool = False
