"""Pure validation helpers for inputs and parameters."""

from typing import Mapping, Sequence

from pynf.types import ChannelInfo, InputGroups

def validate_meta_map(
    meta: Mapping[str, object], required_fields: Sequence[str] | None = None
) -> None:
    """Validate that required meta fields are present.

    Example:
        >>> validate_meta_map({'id': 'sample1'})

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    typing
    """
    ...

def normalize_inputs(inputs: InputGroups | None) -> list[dict]:
    """Normalize optional inputs into a list of dict-like groups.

    Example:
        >>> normalize_inputs(None)
        []

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...

def validate_inputs(
    inputs: InputGroups | None, input_channels: Sequence[ChannelInfo | dict]
) -> None:
    """Validate user inputs against discovered input channels.

    Example:
        >>> validate_inputs([{'reads': 'sample.fq'}], [{'type': 'tuple', 'params': [{'name': 'reads', 'type': 'path'}]}])

    DEPENDS_ON:
    pynf.validation.normalize_inputs
    pynf.validation._validate_input_count
    pynf.validation._validate_input_group

    EXTERNAL_DEPENDS_ON:
    typing
    """
    ...

def _validate_input_count(
    inputs: Sequence[dict], input_channels: Sequence[ChannelInfo | dict]
) -> None:
    """Validate that the number of input groups matches expectations.

    Example:
        >>> _validate_input_count([{}], [{'type': 'tuple', 'params': []}])

    DEPENDS_ON:
    pynf.validation._format_count_error

    EXTERNAL_DEPENDS_ON:
    typing
    """
    ...

def _validate_input_group(
    user_input: Mapping[str, object],
    expected_channel: ChannelInfo | dict,
    group_idx: int,
) -> None:
    """Validate a single input group against expected parameters.

    Example:
        >>> _validate_input_group({'reads': 'a.fq'}, expected_channel, 0)

    DEPENDS_ON:
    pynf.validation._format_missing_params_error
    pynf.validation._format_extra_params_error

    EXTERNAL_DEPENDS_ON:
    typing
    """
    ...

def _format_count_error(
    inputs: Sequence[dict], input_channels: Sequence[ChannelInfo | dict]
) -> str:
    """Format a detailed input-count error message.

    Example:
        >>> _format_count_error([], [{'type': 'tuple', 'params': []}])

    DEPENDS_ON:
    pynf.validation._format_expected_structure
    pynf.validation._format_provided_inputs

    EXTERNAL_DEPENDS_ON:
    typing
    """
    ...

def _format_missing_params_error(
    missing_params: set[str],
    expected_params: Sequence[dict],
    group_idx: int,
    channel_type: str | None,
) -> str:
    """Format a detailed missing-parameter error message.

    Example:
        >>> _format_missing_params_error({'reads'}, expected_params, 0, 'tuple')

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    typing
    """
    ...

def _format_extra_params_error(
    extra_params: set[str],
    expected_params: Sequence[dict],
    group_idx: int,
    channel_type: str | None,
) -> str:
    """Format a detailed extra-parameter error message.

    Example:
        >>> _format_extra_params_error({'foo'}, expected_params, 0, 'tuple')

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    typing
    """
    ...

def _format_expected_structure(input_channels: Sequence[ChannelInfo | dict]) -> str:
    """Render the expected input structure for error messages.

    Example:
        >>> _format_expected_structure([{'type': 'tuple', 'params': [{'name': 'reads', 'type': 'path'}]}])

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    typing
    """
    ...

def _format_provided_inputs(inputs: Sequence[dict]) -> str:
    """Render the provided inputs for error messages.

    Example:
        >>> _format_provided_inputs([{'reads': 'sample.fq'}])

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    typing
    """
    ...
