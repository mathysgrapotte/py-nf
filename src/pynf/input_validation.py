"""Compatibility helpers for input validation."""

from . import validation


class InputValidator:
    """Backwards-compatible facade over pure validation helpers."""

    @staticmethod
    def validate_inputs(inputs, input_channels):
        """Validate user inputs against discovered input channels.

        Args:
            inputs: List of input group mappings supplied by the user.
            input_channels: Expected channel structures extracted from a script.

        Raises:
            ValueError: If the inputs do not match the expected structure.
        """
        validation.validate_inputs(inputs, input_channels)
