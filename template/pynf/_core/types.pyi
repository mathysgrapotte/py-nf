"""Core datatypes (stubs)."""

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
    type: ParamType
    name: ParamName


@dataclass(frozen=True)
class ChannelInfo:
    type: ParamType
    params: Sequence[ChannelParam]


@dataclass(frozen=True)
class ModulePaths:
    module_id: ModuleId
    module_dir: Path
    main_nf: Path
    meta_yml: Path


@dataclass(frozen=True)
class DockerConfig:
    enabled: bool = ...
    registry: str | None = ...
    registry_override: bool | None = ...
    remove: bool | None = ...
    run_options: str | None = ...


@dataclass(frozen=True)
class ExecutionRequest:
    script_path: Path
    executor: str = ...
    params: ParamsMap | None = ...
    inputs: InputGroups | None = ...
    docker: DockerConfig | None = ...
    verbose: bool = ...
