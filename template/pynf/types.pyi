"""Core types and data models for the pynf architecture."""

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
    """Describes a single input parameter in a Nextflow channel.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    dataclasses
    """

    type: ParamType
    name: ParamName

@dataclass(frozen=True)
class ChannelInfo:
    """Describes an input channel and its parameters.

    DEPENDS_ON:
    pynf.types.ChannelParam

    EXTERNAL_DEPENDS_ON:
    dataclasses
    """

    type: ParamType
    params: Sequence[ChannelParam]

@dataclass(frozen=True)
class ModulePaths:
    """Local filesystem paths for a cached nf-core module.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    dataclasses
    pathlib
    """

    module_id: ModuleId
    module_dir: Path
    main_nf: Path
    meta_yml: Path

@dataclass(frozen=True)
class DockerConfig:
    """Docker configuration for Nextflow execution.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    dataclasses
    """

    enabled: bool = True
    registry: str | None = None
    registry_override: bool | None = None
    remove: bool | None = None
    run_options: str | None = None

@dataclass(frozen=True)
class ExecutionRequest:
    """Immutable request describing a Nextflow execution.

    DEPENDS_ON:
    pynf.types.DockerConfig

    EXTERNAL_DEPENDS_ON:
    dataclasses
    pathlib
    """

    script_path: Path
    executor: str = "local"
    params: ParamsMap | None = None
    inputs: InputGroups | None = None
    docker: DockerConfig | None = None
    verbose: bool = False
