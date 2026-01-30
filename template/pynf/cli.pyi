"""Click CLI for managing nf-core modules and Nextflow scripts."""

from __future__ import annotations

from typing import Any

class CLIContext:
    """Shared CLI configuration for Click commands.

Attributes:
    cache_dir: Optional directory for cached module artifacts.
    github_token: Optional GitHub token for authenticated requests.

Example:
    >>> CLIContext(cache_dir=Path("~/.cache/nf-core-modules"))
    CLIContext(cache_dir=PosixPath('~/.cache/nf-core-modules'), github_token=None)"""
    ...

def parse_params_option(raw: str | None) -> dict[str, Any]:
    """Parse the CLI ``--params`` option into a typed dictionary.

The option accepts either a JSON object string or a comma-separated list of
``key=value`` pairs. When JSON parsing succeeds, rich objects like booleans,
numbers, lists, and nested dictionaries are preserved. The ``key=value``
fallback keeps values as strings when they cannot be parsed as JSON.

Args:
    raw: Raw CLI parameter string or ``None``.

Returns:
    Parsed parameters. Returns an empty dictionary when ``raw`` is empty.

Raises:
    json.JSONDecodeError: If JSON parsing fails for a JSON object string.
    ValueError: If a ``key=value`` pair is missing the separator.

Example:
    >>> parse_params_option('threads=4,debug=true')
    {'threads': 4, 'debug': True}
    >>> parse_params_option('{"threads": 4, "debug": true}')
    {'threads': 4, 'debug': True}"""
    ...

def parse_inputs_option(raw: str | None) -> list[dict[str, Any]] | None:
    """Parse the CLI ``--inputs`` option into a list of dictionaries.

The CLI accepts JSON representing a list of input group mappings, where each
mapping contains parameter names and values to feed into the Nextflow module.

Args:
    raw: Raw CLI inputs JSON string or ``None``.

Returns:
    List of input group mappings, or ``None`` when ``raw`` is empty.

Raises:
    json.JSONDecodeError: If the inputs string is not valid JSON.
    ValueError: If the parsed JSON is not a list.

Example:
    >>> parse_inputs_option('[{"reads": ["a.fastq"]}]')
    [{'reads': ['a.fastq']}]"""
    ...

def input_group_table(group_idx: int, input_group: dict[str, Any]) -> Table:
    """Build a rich table listing a single input channel's parameters.

Args:
    group_idx: Zero-based index of the input channel.
    input_group: Mapping describing the channel (``type`` and ``params``).

Returns:
    A ``rich.table.Table`` with parameter names and their declared types.

Example:
    >>> table = input_group_table(0, {"type": "tuple", "params": [{"name": "meta", "type": "val"}]})
    >>> "Input Channel 1" in str(table)
    True"""
    ...

def modules_table(modules: list[str], limit: int | None = None) -> Table:
    """Render a rich table that lists available modules and their type.

Args:
    modules: Ordered list of module identifiers.
    limit: Optional number of modules to display.

Returns:
    A ``rich.table.Table`` listing module names and their inferred type.

Example:
    >>> table = modules_table(["samtools", "fastqc"], limit=1)
    >>> "top-level" in str(table)
    True"""
    ...

def cli(ctx, cache_dir: Optional[str], github_token: Optional[str]):
    """Entry point for the pynf CLI commands.

Args:
    ctx: Click context populated by the command group.
    cache_dir: Optional cache directory override.
    github_token: Optional GitHub token for authenticated requests."""
    ...

def list_modules_cmd(ctx: CLIContext, limit: Optional[int], rate_limit: bool):
    """List available nf-core modules.

Args:
    ctx: Click context containing CLI configuration.
    limit: Optional number of modules to display.
    rate_limit: When ``True``, display GitHub API rate limit info."""
    ...

def list_submodules(ctx: CLIContext, module: str):
    """List submodules available in a module.

Args:
    ctx: Click context containing CLI configuration.
    module: Parent module identifier."""
    ...

def download(ctx: CLIContext, module: str, force: bool):
    """Download an nf-core module into the local cache.

Args:
    ctx: Click context containing CLI configuration.
    module: Module identifier to download.
    force: When ``True``, re-download even if cached."""
    ...

def list_inputs(ctx: CLIContext, module: str, output_json: bool):
    """List input parameters from a module's ``main.nf``.

Args:
    ctx: Click context containing CLI configuration.
    module: Module identifier.
    output_json: When ``True``, emit JSON output."""
    ...

def inspect(ctx: CLIContext, module: str, output_json: bool):
    """Inspect a downloaded nf-core module.

Args:
    ctx: Click context containing CLI configuration.
    module: Module identifier.
    output_json: When ``True``, emit JSON output."""
    ...

def run(
    ctx: CLIContext,
    module: str,
    inputs: Optional[str],
    params: Optional[str],
    docker: bool,
    executor: str,
    verbose: bool,
):
    """Run an nf-core module via the Nextflow runtime.

Args:
    ctx: Click context containing CLI configuration.
    module: Module identifier.
    inputs: JSON string describing input groups.
    params: JSON string or key=value list of parameters.
    docker: Whether to enable Docker execution.
    executor: Nextflow executor name.
    verbose: Enable verbose debug output."""
    ...

def main():
    """Main entry point for the CLI.

Returns:
    ``None``. The CLI handles execution and exits the process."""
    ...

