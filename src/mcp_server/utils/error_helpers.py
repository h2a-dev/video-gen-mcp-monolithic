"""Standardized error handling utilities for agent-friendly error messages."""

from typing import Dict, Any, List, Optional, Union, Callable
from functools import wraps
import asyncio


class ErrorType:
    """Standard error types for categorization."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    API_ERROR = "API_ERROR"
    STATE_ERROR = "STATE_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"


def create_error_response(
    error_type: str,
    error_message: str,
    details: Optional[Dict[str, Any]] = None,
    valid_options: Optional[Dict[str, Any]] = None,
    suggestion: Optional[str] = None,
    example: Optional[str] = None
) -> Dict[str, Any]:
    """Create a standardized error response that helps agents understand and recover."""
    response = {
        "success": False,
        "error_type": error_type,
        "error": error_message
    }
    
    if details:
        response["details"] = details
    
    if valid_options:
        response["valid_options"] = valid_options
    
    if suggestion:
        response["suggestion"] = suggestion
    
    if example:
        response["example"] = example
    
    return response


# Common validation functions

def validate_duration(value: Union[int, str], valid_durations: List[int] = [5, 10]) -> Dict[str, Any]:
    """Validate video duration parameter."""
    try:
        duration = int(value) if isinstance(value, str) else value
    except (ValueError, TypeError):
        return {
            "valid": False,
            "error_response": create_error_response(
                ErrorType.VALIDATION_ERROR,
                f"Duration must be a number, got: {type(value).__name__}",
                details={"parameter": "duration", "provided": value},
                suggestion="Provide duration as an integer in seconds",
                example="duration=10"
            )
        }
    
    if duration not in valid_durations:
        return {
            "valid": False,
            "error_response": create_error_response(
                ErrorType.VALIDATION_ERROR,
                f"Invalid duration: {duration} seconds",
                details={
                    "parameter": "duration",
                    "provided": duration,
                    "valid_values": valid_durations
                },
                suggestion=f"Use {' or '.join(map(str, valid_durations))} seconds",
                example=f"generate_video_from_image(image_url='...', duration={valid_durations[0]})"
            )
        }
    
    return {"valid": True, "value": duration}


def validate_platform(platform: str, valid_platforms: Dict[str, str]) -> Dict[str, Any]:
    """Validate platform parameter."""
    if platform not in valid_platforms:
        return {
            "valid": False,
            "error_response": create_error_response(
                ErrorType.VALIDATION_ERROR,
                f"Unknown platform: '{platform}'",
                details={"parameter": "platform", "provided": platform},
                valid_options=valid_platforms,
                suggestion="Choose a platform based on your target audience",
                example="create_project(title='My Video', platform='youtube')"
            )
        }
    
    return {"valid": True}


def validate_aspect_ratio(aspect_ratio: str, valid_ratios: Dict[str, str]) -> Dict[str, Any]:
    """Validate aspect ratio parameter."""
    if aspect_ratio not in valid_ratios:
        return {
            "valid": False,
            "error_response": create_error_response(
                ErrorType.VALIDATION_ERROR,
                f"Invalid aspect ratio: '{aspect_ratio}'",
                details={"parameter": "aspect_ratio", "provided": aspect_ratio},
                valid_options=valid_ratios,
                suggestion="Use 16:9 for YouTube, 9:16 for TikTok/Reels, or 1:1 for Instagram",
                example="aspect_ratio='16:9'"
            )
        }
    
    return {"valid": True}


def validate_range(
    value: Union[float, str],
    param_name: str,
    min_value: float,
    max_value: float,
    param_description: str = "value"
) -> Dict[str, Any]:
    """Validate numeric parameter is within range."""
    try:
        numeric_value = float(value) if isinstance(value, str) else value
    except (ValueError, TypeError):
        return {
            "valid": False,
            "error_response": create_error_response(
                ErrorType.VALIDATION_ERROR,
                f"{param_description} must be a number, got: {type(value).__name__}",
                details={"parameter": param_name, "provided": value},
                suggestion=f"Provide {param_name} as a number between {min_value} and {max_value}",
                example=f"{param_name}={min_value}"
            )
        }
    
    if not min_value <= numeric_value <= max_value:
        return {
            "valid": False,
            "error_response": create_error_response(
                ErrorType.VALIDATION_ERROR,
                f"{param_description} must be between {min_value} and {max_value}, got: {numeric_value}",
                details={
                    "parameter": param_name,
                    "provided": numeric_value,
                    "min": min_value,
                    "max": max_value
                },
                suggestion=f"Use a value between {min_value} and {max_value}",
                example=f"{param_name}={(min_value + max_value) / 2}"
            )
        }
    
    return {"valid": True, "value": numeric_value}


def validate_enum(
    value: str,
    param_name: str,
    valid_values: List[str],
    param_description: str = "value"
) -> Dict[str, Any]:
    """Validate parameter is one of allowed values."""
    if value not in valid_values:
        return {
            "valid": False,
            "error_response": create_error_response(
                ErrorType.VALIDATION_ERROR,
                f"Invalid {param_description}: '{value}'",
                details={
                    "parameter": param_name,
                    "provided": value,
                    "valid_values": valid_values
                },
                suggestion=f"Choose one of: {', '.join(valid_values)}",
                example=f"{param_name}='{valid_values[0]}'"
            )
        }
    
    return {"valid": True}


# Decorator for parameter validation
def validate_parameters(**validations: Dict[str, Callable]) -> Callable:
    """Decorator to validate parameters before executing tool."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(**kwargs):
            # Run all validations
            for param_name, validator in validations.items():
                if param_name in kwargs and kwargs[param_name] is not None:
                    result = validator(kwargs[param_name])
                    if not result["valid"]:
                        return result["error_response"]
                    # Update with validated/converted value if provided
                    if "value" in result:
                        kwargs[param_name] = result["value"]
            
            # Call the original function
            return await func(**kwargs)
        
        return wrapper
    return decorator


# Common error handlers for external services

def handle_fal_api_error(error: Exception, operation: str) -> Dict[str, Any]:
    """Convert FAL API errors to user-friendly messages."""
    error_str = str(error).lower()
    
    if "rate limit" in error_str or "too many requests" in error_str:
        return create_error_response(
            ErrorType.API_ERROR,
            "Rate limit exceeded - too many requests",
            details={"operation": operation, "service": "FAL AI"},
            suggestion="Wait a few minutes before trying again",
            example="Consider batching your requests or adding delays"
        )
    
    if "api key" in error_str or "unauthorized" in error_str:
        return create_error_response(
            ErrorType.API_ERROR,
            "API authentication failed",
            details={"operation": operation, "service": "FAL AI"},
            suggestion="Check that FALAI_API_KEY environment variable is set correctly"
        )
    
    if "timeout" in error_str:
        return create_error_response(
            ErrorType.API_ERROR,
            f"{operation} timed out - this can happen with complex generations",
            details={"operation": operation, "service": "FAL AI"},
            suggestion="Try again with simpler parameters or wait a moment",
            example="Consider reducing complexity or using a different model"
        )
    
    # Generic API error
    return create_error_response(
        ErrorType.API_ERROR,
        f"API error during {operation}",
        details={"operation": operation, "error": str(error)},
        suggestion="Check your parameters and try again"
    )


def handle_file_operation_error(error: Exception, file_path: str, operation: str) -> Dict[str, Any]:
    """Convert file operation errors to user-friendly messages."""
    error_str = str(error).lower()
    
    if "not found" in error_str or "no such file" in error_str:
        return create_error_response(
            ErrorType.RESOURCE_NOT_FOUND,
            f"File not found: {file_path}",
            details={"file_path": file_path, "operation": operation},
            suggestion="Check the file path and ensure the file exists",
            example="Use an absolute path or verify the file was created successfully"
        )
    
    if "permission" in error_str:
        return create_error_response(
            ErrorType.SYSTEM_ERROR,
            f"Permission denied accessing: {file_path}",
            details={"file_path": file_path, "operation": operation},
            suggestion="Check file permissions or run with appropriate access rights"
        )
    
    if "space" in error_str:
        return create_error_response(
            ErrorType.SYSTEM_ERROR,
            "Insufficient disk space",
            details={"file_path": file_path, "operation": operation},
            suggestion="Free up disk space and try again"
        )
    
    return create_error_response(
        ErrorType.SYSTEM_ERROR,
        f"File operation failed: {operation}",
        details={"file_path": file_path, "error": str(error)},
        suggestion="Check file path and system permissions"
    )


# Project validation helper
def validate_project_exists(project_id: str, project_manager) -> Dict[str, Any]:
    """Check if project exists and return helpful error if not."""
    try:
        project = project_manager.get_project(project_id)
        return {"valid": True, "project": project}
    except:
        return {
            "valid": False,
            "error_response": create_error_response(
                ErrorType.RESOURCE_NOT_FOUND,
                f"Project not found: {project_id}",
                details={"project_id": project_id},
                suggestion="Use list_projects() to see available projects",
                example="First create a project: create_project(title='My Video', platform='youtube')"
            )
        }