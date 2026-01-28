"""Input validation for Nextflow module execution."""

from . import validation


class InputValidator:
    """Backwards-compatible facade over the pure validation module."""

    @staticmethod
    def validate_inputs(inputs, input_channels):
        """Validate inputs using the pure validation helpers."""
        validation.validate_inputs(inputs, input_channels)
