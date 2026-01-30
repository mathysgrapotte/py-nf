"""Core data types for the pynf runtime and module workflows."""

from __future__ import annotations

from typing import Any, Literal, Mapping, Sequence

ExecutionBackend = Literal["local", "seqera"]
ModuleId = str
ParamName = str
ParamType = str
ParamValue = Any
ParamsMap = Mapping[str, Any]
InputGroup = Mapping[ParamName, ParamValue]
InputGroups = Sequence[InputGroup]

class ChannelParam:
    """Describe a single parameter within a Nextflow input channel.

    Attributes:
        type: The Nextflow parameter type (e.g., ``val`` or ``path``) extracted from the
            process definition.
        name: The parameter name as declared in the module; used to map user inputs.

    Example:
        >>> ChannelParam(type="val", name="reads")
        ChannelParam(type='val', name='reads')"""

    ...

class ChannelInfo:
    """Describe a Nextflow input channel and its constituent parameters.

    Attributes:
        type: The channel type as exposed by Nextflow (e.g., ``tuple``,
            ``val``), which determines how inputs should be structured.
        params: Ordered parameter definitions within the channel; preserved order
            reflects the declaration order in the module process.

    Example:
        >>> ChannelInfo(type="tuple", params=[ChannelParam("val", "meta")])
        ChannelInfo(type='tuple', params=[ChannelParam(type='val', name='meta')])"""

    ...

class ModulePaths:
    """Resolve and store local paths for a cached nf-core module.

    Attributes:
        module_id: The nf-core module identifier (e.g., ``samtools/view``).
        module_dir: Directory containing the cached module files.
        main_nf: Path to the module ``main.nf`` workflow definition.
        meta_yml: Path to the module ``meta.yml`` inputs configuration.

    Example:
        >>> ModulePaths(
        ...     module_id="samtools/view",
        ...     module_dir=Path("/tmp/nf-core-modules/samtools/view"),
        ...     main_nf=Path("/tmp/nf-core-modules/samtools/view/main.nf"),
        ...     meta_yml=Path("/tmp/nf-core-modules/samtools/view/meta.yml"),
        ... )
        ModulePaths(module_dir=PosixPath('/tmp/...'), main_nf=PosixPath('/tmp/...'), ...)"""

    ...

class DockerConfig:
    """Docker configuration values for Nextflow execution.

    Attributes:
        enabled: Whether Docker is enabled in the Nextflow session.
        registry: Optional Docker registry override (e.g., ``quay.io``).
        registry_override: Whether to override registry values in fully qualified images.
        remove: Whether to auto-remove containers once execution finishes.
        run_options: Extra CLI options appended to the Docker command.

    Example:
        >>> DockerConfig(enabled=True, registry="quay.io", run_options="--rm")
        DockerConfig(enabled=True, registry='quay.io', registry_override=None, remove=None, run_options='--rm')"""

    ...

class SeqeraConfig:
    """Seqera Platform configuration for remote execution.

    Attributes:
        access_token: Seqera Platform access token. If omitted, read ``TOWER_ACCESS_TOKEN``.
        api_endpoint: Base API endpoint (defaults to ``https://api.cloud.seqera.io``).
        workspace_id: Workspace numeric identifier.
        compute_env_id: Compute environment identifier.
        work_dir: Optional work directory for the run (e.g. ``s3://bucket/work``).
        run_name: Optional run name for the workflow.

    Example:
        >>> SeqeraConfig(workspace_id=1, compute_env_id="abc123")
        SeqeraConfig(workspace_id=1, compute_env_id='abc123')"""

    ...

class ExecutionRequest:
    """Immutable request describing a Nextflow execution.

    Attributes:
        script_path: Path to the Nextflow script to execute.
        executor: Executor identifier (e.g., ``local``) passed to Nextflow.
        params: Script parameters to set on the Nextflow binding before script load.
        inputs: Optional list of input group mappings that are validated against the script metadata.
        docker: Docker execution configuration, when enabled.
        verbose: Whether to enable verbose logging and diagnostic output.
        backend: Execution backend identifier (``local`` or ``seqera``).
        seqera: Seqera Platform configuration when ``backend='seqera'``.

    Example:
        >>> ExecutionRequest(
        ...     script_path=Path("main.nf"),
        ...     executor="local",
        ...     params={"threads": 4},
        ...     inputs=[{"reads": "sample.fastq"}],
        ... )
        ExecutionRequest(script_path=PosixPath('main.nf'), executor='local', ...)"""

    ...
