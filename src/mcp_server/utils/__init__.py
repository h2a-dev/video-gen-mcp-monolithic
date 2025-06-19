"""Utility modules for the MCP server."""

from .error_helpers import (
    ErrorType,
    create_error_response,
    validate_duration,
    validate_platform,
    validate_aspect_ratio,
    validate_range,
    validate_enum,
    validate_parameters,
    handle_fal_api_error,
    handle_file_operation_error,
    validate_project_exists
)

from .image_helpers import (
    process_image_input,
    validate_image_input,
    file_to_base64_data_uri
)

__all__ = [
    "ErrorType",
    "create_error_response",
    "validate_duration",
    "validate_platform",
    "validate_aspect_ratio",
    "validate_range",
    "validate_enum",
    "validate_parameters",
    "handle_fal_api_error",
    "handle_file_operation_error",
    "validate_project_exists",
    "process_image_input",
    "validate_image_input",
    "file_to_base64_data_uri"
]