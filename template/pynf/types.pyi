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
    """Describe a single parameter within a Nextflow input channel.

    This dataclass captures the parameter name and declared type so downstream
    validation and session wiring can look up values by name and enforce expected
    semantics.

    Attributes:
        type: The Nextflow type declared for the parameter (e.g., ``val`` or ``path``).
        name: The parameter name as declared in the process block.

    Example:
        >>> ChannelParam(type="val", name="meta")
        ChannelParam(type='val', name='meta')

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    dataclasses
    """

    type: ParamType
    name: ParamName

@dataclass(frozen=True)
class ChannelInfo:
    """Describe a Nextflow input channel and the ordered parameters it exposes.

    The ``type`` field reflects the channel category (``tuple``, ``val``, etc.) while
    ``params`` enumerates the contained parameters so the CLI/runtime can bind values.

    Attributes:
        type: The channel type name emitted by Nextflow.
        params: Sequence of ``ChannelParam`` instances ordered by declaration.

    Example:
        >>> ChannelInfo(type="tuple", params=[ChannelParam(type="val", name="meta")])
        ChannelInfo(type='tuple', params=[ChannelParam(type='val', name='meta')])

    DEPENDS_ON:
    pynf.types.ChannelParam

    EXTERNAL_DEPENDS_ON:
    dataclasses
    """

    type: ParamType
    params: Sequence[ChannelParam]

@dataclass(frozen=True)
class ModulePaths:
    """Resolve and store local paths for a cached nf-core module.

    Each cached module exposes its workspace directory, nextflow script, and meta
    configuration so the CLI can display or execute the workflow.

    Attributes:
        module_id: The nf-core module identifier (e.g., ``samtools/view``).
        module_dir: Directory containing the module files.
        main_nf: Path to the ``main.nf`` Nextflow script.
        meta_yml: Path to the ``meta.yml`` inputs metadata.

    Example:
        >>> ModulePaths(
        ...     module_id="samtools/view",
        ...     module_dir=Path("/tmp/nf-core-modules/samtools/view"),
        ...     main_nf=Path("/tmp/nf-core-modules/samtools/view/main.nf"),
        ...     meta_yml=Path("/tmp/nf-core-modules/samtools/view/meta.yml"),
        )
        ModulePaths(module_dir=PosixPath('/tmp/...'), main_nf=PosixPath('/tmp/...'), ...)

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
    """Docker configuration values for Nextflow execution.

    This dataclass gathers flags and overrides that are translated into the JVM
    session config, allowing the Nextflow runtime to reach into Docker/OCI engines.

    Attributes:
        enabled: Whether Docker should be used for execution.
        registry: Registry override string (e.g., ``quay.io``).
        registry_override: Force a registry override even when absolute image names are used.
        remove: Whether Docker should auto-remove containers on exit.
        run_options: Extra CLI options forwarded to Docker.

    Example:
        >>> DockerConfig(enabled=True, registry="quay.io", run_options="--rm")
        DockerConfig(enabled=True, registry='quay.io', registry_override=None, remove=None, run_options='--rm')

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

    The execution request bundles script path, executor selection, parameter mappings,
    and optional Docker configuration into a single value object consumed by the runtime.

    Attributes:
        script_path: Path to the Nextflow script to execute.
        executor: Executor identifier (e.g., ``local``).
        params: Mapping of script parameters to pre-set values.
        inputs: Optional list of input groups that map into Nextflow channels.
        docker: Optional Docker configuration.
        verbose: Enable verbose logging output.

    Example:
        >>> ExecutionRequest(
        ...     script_path=Path("main.nf"),
        ...     executor="local",
        ...     params={"threads": 4},
        ...     inputs=[{"reads": "sample.fastq"}],
        ... )
        ExecutionRequest(script_path=PosixPath('main.nf'), executor='local', ...)

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
