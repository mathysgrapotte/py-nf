"""Rendering helpers for CLI output."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from rich.table import Table


def input_group_table(group_idx: int, input_group: Mapping[str, object]) -> Table:
    """Create a table for an input channel from native API format."""
    channel_type = input_group.get("type", "unknown")
    params = input_group.get("params", [])

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
    """Create a modules table with optional truncation."""
    table = Table(title="Available nf-core Modules", show_header=True, header_style="bold magenta")
    table.add_column("Module Name", style="cyan")
    table.add_column("Type", style="green")

    display_modules = modules[:limit] if limit else modules
    for module in display_modules:
        module_type = "sub-module" if "/" in module else "top-level"
        table.add_row(module, module_type)

    return table
