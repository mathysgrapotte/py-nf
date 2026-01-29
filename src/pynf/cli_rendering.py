"""Rich table renderers for CLI output formatting."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from rich.table import Table


def input_group_table(group_idx: int, input_group: Mapping[str, Any]) -> Table:
    """Build a rich table listing a single input channel's parameters.

    Args:
        group_idx: Zero-based index of the input channel.
        input_group: Mapping describing the channel (``type`` and ``params``).

    Returns:
        A ``rich.table.Table`` with parameter names and their declared types.

    Example:
        >>> table = input_group_table(0, {"type": "tuple", "params": [{"name": "meta", "type": "val"}]})
        >>> "Input Channel 1" in str(table)
        True
    """
    channel_type = input_group.get("type", "unknown")
    params = input_group.get("params", [])
    if not isinstance(params, Sequence):
        params = []

    table = Table(
        title=f"Input Channel {group_idx + 1} (type: {channel_type})",
        show_header=True,
        header_style="bold blue",
    )
    table.add_column("Parameter Name", style="cyan")
    table.add_column("Parameter Type", style="yellow")

    for param in params:
        param_name = param.get("name", "unknown")
        param_type = param.get("type", "unknown")
        table.add_row(param_name, param_type)

    return table


def modules_table(modules: Sequence[str], limit: int | None = None) -> Table:
    """Render a rich table that lists available modules and their type.

    Args:
        modules: Ordered list of module identifiers.
        limit: Optional number of modules to display.

    Returns:
        A ``rich.table.Table`` listing module names and their inferred type.

    Example:
        >>> table = modules_table(["nf-core/samtools", "nf-core/fastqc"], limit=1)
        >>> "top-level" in str(table)
        True
    """
    table = Table(
        title="Available nf-core Modules", show_header=True, header_style="bold magenta"
    )
    table.add_column("Module Name", style="cyan")
    table.add_column("Type", style="green")

    display_modules = modules[:limit] if limit else modules
    for module in display_modules:
        module_type = "sub-module" if "/" in module else "top-level"
        table.add_row(module, module_type)

    return table
