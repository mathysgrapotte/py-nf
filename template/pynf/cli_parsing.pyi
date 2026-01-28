"""Pure CLI parsing helpers."""

from typing import Any

def parse_params_option(raw: str | None) -> dict[str, Any]:
    """Parse params as JSON or key=value pairs.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    json
    """
    ...

def parse_inputs_option(raw: str | None) -> list[dict[str, Any]] | None:
    """Parse inputs as a JSON list of dicts.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    json
    """
    ...
