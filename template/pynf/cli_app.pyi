"""CLI application wiring (thin layer over API + parsing/rendering helpers)."""

from pathlib import Path

class CLIContext:
    """Shared CLI configuration.

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
    """Construct and return the Click CLI application.

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
    """CLI entry point.

    DEPENDS_ON:
    pynf.cli_app.build_cli

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...
