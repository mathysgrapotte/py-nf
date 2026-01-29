"""CLI application wiring (thin layer over API + parsing/rendering helpers)."""

from pathlib import Path

class CLIContext:
    """Shared CLI configuration for Click commands exposed by pynf.

    Attributes:
        cache_dir: Optional filesystem cache location for downloaded modules.
        github_token: Optional GitHub token leveraged for authenticated API requests.

    Example:
        >>> CLIContext(cache_dir=Path("~/nf-core-modules"))
        CLIContext(cache_dir=PosixPath('~/nf-core-modules'), github_token=None)

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    pathlib
    """

    cache_dir: Path | None
    github_token: str | None

    def __init__(
        self, cache_dir: Path | None = None, github_token: str | None = None
    ) -> None: ...

def build_cli() -> object:
    """Construct and wire the Click CLI application for module management.

    The builder pulls together parsing/rendering helpers, API operations, and shared
    context so the CLI commands can execute module workflows end-to-end.

    Example:
        >>> cli_group = build_cli()
        >>> isinstance(cli_group, click.core.Group)
        True

    DEPENDS_ON:
    pynf.cli_parsing.parse_params_option
    pynf.cli_parsing.parse_inputs_option
    pynf.cli_rendering.modules_table
    pynf.cli_rendering.input_group_table
    pynf.api.list_modules
    pynf.api.list_submodules
    pynf.api.inspect_module
    pynf.api.get_module_inputs
    pynf.api.run_module
    pynf.api.get_rate_limit_status

    EXTERNAL_DEPENDS_ON:
    click
    rich.console
    """
    ...

def main() -> None:
    """Entry point used by console_scripts to invoke the CLI.

    Example:
        >>> main()
        # Triggers CLI command processing and exits once done

    DEPENDS_ON:
    pynf.cli_app.build_cli

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...
