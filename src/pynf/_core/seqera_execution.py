"""Seqera Platform execution helpers."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import yaml

from .result import SeqeraResult
from .seqera_client import SeqeraClient
from .types import ExecutionRequest, ModulePaths, SeqeraConfig
from .validation import validate_inputs

TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "CANCELLED"}


def execute_seqera_script(request: ExecutionRequest) -> SeqeraResult:
    seqera = resolve_seqera_config(request)
    outdir = require_outdir(request)
    params_text = build_params_text(request)
    main_script = request.script_path.read_text()
    return _submit_seqera_launch(
        seqera,
        main_script=main_script,
        params_text=params_text,
        outdir=outdir,
    )


def execute_seqera_module(
    request: ExecutionRequest, module_paths: ModulePaths
) -> SeqeraResult:
    seqera = resolve_seqera_config(request)
    outdir = require_outdir(request)
    input_groups = _extract_input_groups(module_paths.meta_yml)
    _validate_inputs_from_meta(request.inputs, input_groups)
    params_text = build_params_text(request)
    wrapper = build_module_wrapper(module_paths, input_groups)
    return _submit_seqera_launch(
        seqera,
        main_script=wrapper,
        params_text=params_text,
        outdir=outdir,
    )


def build_module_wrapper(
    module_paths: ModulePaths, input_groups: list[list[str]]
) -> str:
    module_source = module_paths.main_nf.read_text()
    process_name = _extract_process_name(module_source)
    if not process_name:
        raise ValueError("Unable to determine module process name")

    header = "\n".join(
        [
            "nextflow.enable.dsl=2",
            "",
            "def moduleDir = workflow.projectDir",
            "",
            "process {",
            "  publishDir = [path: params.outdir, mode: 'copy', overwrite: true]",
            "}",
            "",
        ]
    )
    workflow_block = _render_workflow_block(process_name, input_groups)
    return f"{header}{module_source}\n\n{workflow_block}\n"


def resolve_seqera_config(request: ExecutionRequest) -> SeqeraConfig:
    base = request.seqera or SeqeraConfig()
    access_token = base.access_token or os.getenv("TOWER_ACCESS_TOKEN")
    default_endpoint = "https://api.cloud.seqera.io"
    api_endpoint = base.api_endpoint or default_endpoint
    env_endpoint = os.getenv("TOWER_API_ENDPOINT")
    if env_endpoint and (
        request.seqera is None or base.api_endpoint == default_endpoint
    ):
        api_endpoint = env_endpoint
    workspace_id = _coerce_int(base.workspace_id or os.getenv("TOWER_WORKSPACE_ID"))
    compute_env_id = base.compute_env_id or os.getenv("TOWER_COMPUTE_ENV_ID")

    if not access_token:
        raise ValueError(
            "Seqera access token missing; set TOWER_ACCESS_TOKEN or SeqeraConfig.access_token"
        )
    if workspace_id is None:
        raise ValueError(
            "Seqera workspace id missing; set TOWER_WORKSPACE_ID or SeqeraConfig.workspace_id"
        )
    if not compute_env_id:
        raise ValueError(
            "Seqera compute env id missing; set TOWER_COMPUTE_ENV_ID or SeqeraConfig.compute_env_id"
        )

    return SeqeraConfig(
        access_token=access_token,
        api_endpoint=api_endpoint,
        workspace_id=workspace_id,
        compute_env_id=compute_env_id,
        work_dir=base.work_dir,
        run_name=base.run_name,
    )


def require_outdir(request: ExecutionRequest) -> str:
    params = request.params or {}
    if "outdir" not in params:
        raise ValueError("Seqera execution requires params['outdir'] to be set")
    outdir = params["outdir"]
    if isinstance(outdir, Path):
        outdir = str(outdir)
    if not isinstance(outdir, str) or not outdir:
        raise ValueError(
            "Seqera execution requires params['outdir'] to be a non-empty string"
        )
    return outdir


def build_params_text(request: ExecutionRequest) -> str:
    params = _normalize_params(dict(request.params or {}))
    if request.inputs is not None:
        params["inputs"] = _normalize_params(list(request.inputs))
    return json.dumps(params, indent=2)


def _submit_seqera_launch(
    seqera: SeqeraConfig,
    *,
    main_script: str,
    params_text: str,
    outdir: str,
) -> SeqeraResult:
    launch: dict[str, Any] = {
        "computeEnvId": seqera.compute_env_id,
        "mainScript": main_script,
        "paramsText": params_text,
    }
    if seqera.work_dir:
        launch["workDir"] = seqera.work_dir
    if seqera.run_name:
        launch["runName"] = seqera.run_name

    if not seqera.access_token or seqera.workspace_id is None:
        raise ValueError("Seqera configuration missing access token or workspace id")
    client = SeqeraClient(seqera.api_endpoint, seqera.access_token)
    workflow_id = client.create_workflow_launch(
        launch, workspace_id=seqera.workspace_id
    )
    payload = client.wait_for_workflow(
        workflow_id,
        workspace_id=seqera.workspace_id,
        terminal_states=TERMINAL_STATUSES,
    )
    status = _extract_status(payload) or "UNKNOWN"
    url = f"{seqera.api_endpoint.rstrip('/')}/workflow/{workflow_id}"
    report = {
        "workflow_id": workflow_id,
        "status": status,
        "work_dir": seqera.work_dir,
        "run_name": seqera.run_name,
    }
    return SeqeraResult(
        workflow_id=workflow_id,
        status=status,
        execution_report=report,
        outdir=outdir,
        url=url,
    )


def _extract_process_name(module_source: str) -> str | None:
    match = re.search(r"^process\s+(\w+)", module_source, flags=re.MULTILINE)
    if not match:
        return None
    return match.group(1)


def _extract_input_groups(meta_path: Path) -> list[list[str]]:
    meta = _read_yaml(meta_path)
    inputs = meta.get("input") if isinstance(meta, dict) else None
    if not isinstance(inputs, list):
        return []
    groups: list[list[str]] = []
    for group in inputs:
        if not isinstance(group, list):
            continue
        names: list[str] = []
        for item in group:
            if not isinstance(item, dict):
                continue
            for key in item.keys():
                names.append(str(key))
        if names:
            groups.append(names)
    return groups


def _validate_inputs_from_meta(inputs: Any, input_groups: list[list[str]]) -> None:
    channels = []
    for group in input_groups:
        params = [{"name": name, "type": "val"} for name in group]
        channel_type = "tuple" if len(params) > 1 else "val"
        channels.append({"type": channel_type, "params": params})
    validate_inputs(inputs, channels)


def _render_workflow_block(process_name: str, input_groups: list[list[str]]) -> str:
    lines = ["workflow {"]
    if input_groups:
        lines.append("  if( params.inputs == null ) error 'params.inputs is required'")
        lines.append(
            f"  if( params.inputs.size() != {len(input_groups)} ) "
            f"error 'Expected {len(input_groups)} input group(s) in params.inputs'"
        )
    for idx, group in enumerate(input_groups):
        lines.append(f"  def input{idx} = params.inputs[{idx}]")
        if len(group) == 1:
            lines.append(f"  def ch{idx} = Channel.of({_input_ref(idx, group[0])})")
        else:
            tuple_items = ", ".join(_input_ref(idx, name) for name in group)
            lines.append(f"  def ch{idx} = Channel.of(tuple({tuple_items}))")
    call_args = ", ".join(f"ch{idx}" for idx in range(len(input_groups)))
    lines.append(f"  {process_name}({call_args})")
    lines.append("}")
    return "\n".join(lines)


def _input_ref(index: int, name: str) -> str:
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
        return f"input{index}.{name}"
    return f"input{index}[{json.dumps(name)}]"


def _read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _extract_status(payload: dict[str, Any]) -> str | None:
    workflow = payload.get("workflow") if isinstance(payload, dict) else None
    if isinstance(workflow, dict):
        return workflow.get("status")
    return None


def _normalize_params(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _normalize_params(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_normalize_params(item) for item in value]
    return value


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
