"""Pure CLI parsing helpers."""

from typing import Any

def parse_params_option(raw: str | None) -> dict[str, Any]:
    """Parse the CLI params option into a dictionary.

    Accepts either a JSON object string or a comma-separated list of ``key=value``
    pairs, mirroring the behavior of the runtime so callers can evaluate before
    handing values to Nextflow.

    Example:
        >>> parse_params_option('threads=4,debug=true')
        {'threads': 4, 'debug': True}

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    json
    """
    ...

def parse_inputs_option(raw: str | None) -> list[dict[str, Any]] | None:
    """Parse the CLI inputs option as a list of dictionaries.

    The CLI expects a JSON array where each element is an input group mapping, so
    this function validates the list structure and mirrors the runtime contract.

    Example:
        >>> parse_inputs_option('[{"reads": ["a.fastq"]}]')
        [{'reads': ['a.fastq']}]

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    json
    """
    ...
