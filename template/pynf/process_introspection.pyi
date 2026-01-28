"""Nextflow process introspection using native APIs."""

from typing import Any

def get_process_inputs(
    script_loader: Any, script: Any, script_meta_cls: Any
) -> list[dict]:
    """Extract process inputs via Nextflow ScriptMeta.

    DEPENDS_ON:
    pynf.process_introspection._extract_process_inputs

    EXTERNAL_DEPENDS_ON:
    logging
    """
    ...

def _extract_process_inputs(process_def: Any) -> list[dict]:
    """Extract all inputs from a single process definition.

    DEPENDS_ON:
    pynf.process_introspection._build_channel_info

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...

def _build_channel_info(input_def: Any) -> dict:
    """Build channel metadata from an input definition.

    DEPENDS_ON:
    pynf.process_introspection._extract_tuple_components
    pynf.process_introspection._extract_simple_param

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...

def _extract_tuple_components(input_def: Any) -> list[dict[str, str]]:
    """Extract tuple components from an input definition.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...

def _extract_simple_param(input_def: Any) -> dict[str, str]:
    """Extract a simple parameter from an input definition.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...
