"""Nextflow process introspection helpers using native APIs."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_process_inputs(
    script_loader: Any, script: Any, script_meta_cls: Any
) -> list[dict]:
    """Extract process inputs using Nextflow's native metadata API.

    Args:
        script_loader: Script loader that has parsed the script.
        script: Script instance returned by ``loader.getScript()``.
        script_meta_cls: Nextflow ``ScriptMeta`` class proxy.

    Returns:
        List of input channel definitions, each containing ``type`` and
        ``params`` keys.

    Raises:
        Exception: If the script cannot be parsed for introspection.
    """
    script_loader.setModule(True)

    script_meta = script_meta_cls.get(script)
    process_names = script_meta.getProcessNames()

    if not process_names:
        was_module = script_meta.isModule()
        script_meta.setModule(True)
        try:
            script_loader.runScript()
        finally:
            script_meta.setModule(was_module)
        process_names = script_meta.getProcessNames()

    if not process_names:
        logger.debug("No processes found in script")
        return []

    all_inputs: list[dict] = []
    for process_name in process_names:
        process_def = script_meta.getProcess(process_name)
        all_inputs.extend(_extract_process_inputs(process_def))

    return all_inputs


def _extract_process_inputs(process_def: Any) -> list[dict]:
    """Extract inputs from a single process definition.

    Args:
        process_def: Nextflow process definition instance.

    Returns:
        List of channel dictionaries with ``type`` and ``params``.
    """
    process_config = process_def.getProcessConfig()
    inputs = process_config.getInputs()
    return [_build_channel_info(inp) for inp in inputs]


def _build_channel_info(input_def: Any) -> dict:
    """Build a channel dictionary from a Nextflow input definition.

    Args:
        input_def: Nextflow input definition instance.

    Returns:
        Dictionary describing the channel and its parameters.
    """
    channel_info = {"type": str(input_def.getTypeName()), "params": []}

    if hasattr(input_def, "getInner") and input_def.getInner() is not None:
        channel_info["params"] = _extract_tuple_components(input_def)
    else:
        channel_info["params"].append(_extract_simple_param(input_def))

    return channel_info


def _extract_tuple_components(input_def: Any) -> list[dict[str, str]]:
    """Extract tuple components from a tuple input definition.

    Args:
        input_def: Nextflow tuple input definition.

    Returns:
        List of dictionaries containing ``type`` and ``name``.
    """
    inner = input_def.getInner()
    return [
        {"type": str(component.getTypeName()), "name": str(component.getName())}
        for component in inner
    ]


def _extract_simple_param(input_def: Any) -> dict[str, str]:
    """Extract a simple input parameter definition.

    Args:
        input_def: Nextflow input definition.

    Returns:
        Dictionary containing ``type`` and ``name``.
    """
    return {"type": str(input_def.getTypeName()), "name": str(input_def.getName())}
