"""Input validation for Nextflow module execution."""


class InputValidator:
    """Validates user-provided inputs against expected input channels from .nf script."""

    @staticmethod
    def validate_inputs(inputs, input_channels):
        """
        Validate user inputs against expected input channels.

        Args:
            inputs: List of dicts, each dict contains parameter names and values for one input channel
            input_channels: List of expected input channel structures from .nf script

        Raises:
            ValueError: If validation fails with detailed error message
        """
        if not input_channels:
            if inputs:
                raise ValueError("Module has no inputs, but inputs were provided")
            return

        # Validate input count
        InputValidator._validate_input_count(inputs, input_channels)

        # Validate each input group
        for idx, (user_input, expected_channel) in enumerate(zip(inputs, input_channels)):
            InputValidator._validate_input_group(user_input, expected_channel, idx)

    @staticmethod
    def _validate_input_count(inputs, input_channels):
        """Validate that user provided correct number of input groups."""
        if inputs is None:
            inputs = []

        if len(inputs) != len(input_channels):
            error_msg = InputValidator._format_count_error(inputs, input_channels)
            raise ValueError(error_msg)

    @staticmethod
    def _validate_input_group(user_input, expected_channel, group_idx):
        """Validate a single input group against expected channel structure."""
        channel_type = expected_channel.get('type')
        expected_params = expected_channel.get('params', [])

        # Get expected parameter names
        expected_param_names = {p['name'] for p in expected_params}
        user_param_names = set(user_input.keys())

        # Check for missing required parameters
        missing_params = expected_param_names - user_param_names
        if missing_params:
            error_msg = InputValidator._format_missing_params_error(
                missing_params, expected_params, group_idx, channel_type
            )
            raise ValueError(error_msg)

        # Check for extra parameters
        extra_params = user_param_names - expected_param_names
        if extra_params:
            error_msg = InputValidator._format_extra_params_error(
                extra_params, expected_params, group_idx, channel_type
            )
            raise ValueError(error_msg)

        # Validate tuple structure if it's a tuple input
        if channel_type == 'tuple':
            InputValidator._validate_tuple_structure(user_input, expected_params, group_idx)

    @staticmethod
    def _validate_tuple_structure(user_input, expected_params, group_idx):
        """Validate that tuple input has correct number and types of components."""
        # For now, just check that all components are present (already done above)
        # Future: could validate types (val vs path) if needed
        pass

    @staticmethod
    def _format_count_error(inputs, input_channels):
        """Format error message for incorrect number of input groups."""
        error = f"\n{'='*70}\n"
        error += f"ERROR: Incorrect number of input groups\n"
        error += f"{'='*70}\n\n"
        error += f"Expected {len(input_channels)} input group(s), but got {len(inputs) if inputs else 0}\n\n"
        error += "Expected input structure:\n"
        error += InputValidator._format_expected_structure(input_channels)

        if inputs:
            error += "\nProvided inputs:\n"
            error += InputValidator._format_provided_inputs(inputs)

        error += f"\n{'='*70}\n"
        return error

    @staticmethod
    def _format_missing_params_error(missing_params, expected_params, group_idx, channel_type):
        """Format error message for missing parameters."""
        error = f"\n{'='*70}\n"
        error += f"ERROR: Missing required parameters in input group {group_idx + 1}\n"
        error += f"{'='*70}\n\n"
        error += f"Missing parameters: {', '.join(sorted(missing_params))}\n\n"
        error += f"Input group {group_idx + 1} expects (type: {channel_type}):\n"
        for param in expected_params:
            error += f"  - {param['type']}({param['name']})\n"
        error += f"\n{'='*70}\n"
        return error

    @staticmethod
    def _format_extra_params_error(extra_params, expected_params, group_idx, channel_type):
        """Format error message for extra parameters."""
        error = f"\n{'='*70}\n"
        error += f"ERROR: Unexpected parameters in input group {group_idx + 1}\n"
        error += f"{'='*70}\n\n"
        error += f"Unexpected parameters: {', '.join(sorted(extra_params))}\n\n"
        error += f"Input group {group_idx + 1} expects (type: {channel_type}):\n"
        for param in expected_params:
            error += f"  - {param['type']}({param['name']})\n"
        error += f"\n{'='*70}\n"
        return error

    @staticmethod
    def _format_expected_structure(input_channels):
        """Format expected input structure for error messages."""
        output = "inputs=[\n"
        for idx, channel in enumerate(input_channels):
            channel_type = channel.get('type')
            params = channel.get('params', [])
            output += f"    # Group {idx + 1} (type: {channel_type})\n"
            output += "    {"
            param_strs = [f"'{p['name']}': <value>" for p in params]
            output += ", ".join(param_strs)
            output += "},\n"
        output += "]\n"
        return output

    @staticmethod
    def _format_provided_inputs(inputs):
        """Format provided inputs for error messages."""
        output = "inputs=[\n"
        for idx, inp in enumerate(inputs):
            output += f"    # Group {idx + 1}\n"
            output += f"    {inp},\n"
        output += "]\n"
        return output
