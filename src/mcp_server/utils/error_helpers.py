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
    RATE_LIMIT = "RATE_LIMIT"
    TIMEOUT = "TIMEOUT"
    AUTHENTICATION = "AUTHENTICATION"
    CONTENT_POLICY = "CONTENT_POLICY"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"


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
    """Convert FAL API errors to user-friendly messages with enhanced context."""
    error_str = str(error).lower()
    
    # Rate limiting errors
    if any(term in error_str for term in ["rate limit", "too many requests", "429"]):
        return create_error_response(
            ErrorType.API_ERROR,
            "Rate limit exceeded - too many requests",
            details={"operation": operation, "service": "FAL AI", "error": str(error)},
            suggestion="Wait a few minutes before trying again. Consider batching your requests or adding delays between calls.",
            example="# Add delay between requests:\nimport time\ntime.sleep(5)  # Wait 5 seconds"
        )
    
    # Authentication errors  
    if any(term in error_str for term in ["api key", "unauthorized", "401"]):
        return create_error_response(
            ErrorType.API_ERROR,
            "API authentication failed",
            details={"operation": operation, "service": "FAL AI"},
            suggestion="Check that FALAI_API_KEY environment variable is set correctly",
            example="# Set your API key:\nexport FALAI_API_KEY='your-api-key-here'"
        )
    
    # Timeout errors
    if any(term in error_str for term in ["timeout", "timed out", "took too long"]):
        return create_error_response(
            ErrorType.API_ERROR,
            f"{operation} timed out - this can happen with complex generations",
            details={"operation": operation, "service": "FAL AI"},
            suggestion="Try again with simpler parameters or shorter duration. Complex requests may take longer.",
            example="# For video generation, try:\nduration=5  # Instead of 10"
        )
    
    # Invalid URL/resource errors
    if any(term in error_str for term in ["invalid url", "url", "not found", "404", "cannot access"]):
        return create_error_response(
            ErrorType.VALIDATION_ERROR,
            "The provided resource URL is not accessible",
            details={"operation": operation, "error": str(error)},
            suggestion="Ensure the URL is publicly accessible. For local files, use absolute paths starting with '/'",
            example="# Web URL: https://example.com/image.jpg\n# Local file: /home/user/images/photo.png"
        )
    
    # Server errors
    if any(term in error_str for term in ["500", "502", "503", "504", "server error"]):
        return create_error_response(
            ErrorType.API_ERROR,
            f"Server error during {operation}",
            details={"operation": operation, "service": "FAL AI", "error": str(error)},
            suggestion="The service is temporarily unavailable. Please try again in a few moments.",
            example="# Wait and retry"
        )
    
    # Downstream service errors (common with music generation)
    if any(term in error_str for term in ["downstream", "downstream_service_error", "service_error"]):
        return create_error_response(
            ErrorType.API_ERROR,
            f"The AI service is temporarily having issues with {operation}",
            details={"operation": operation, "service": "FAL AI", "error": str(error)},
            suggestion="This is a temporary issue with the AI model. Try a simpler prompt or wait a few moments before retrying.",
            example="# Try a simpler prompt:\n# 'ambient background music' instead of complex descriptions"
        )
    
    # Model-specific duration errors
    if "kling" in error_str and "duration" in error_str:
        return create_error_response(
            ErrorType.VALIDATION_ERROR,
            "Invalid duration for Kling model",
            details={"operation": operation, "model": "kling_2.1"},
            suggestion="Kling model only supports durations of 5 or 10 seconds",
            example="duration=5  # or duration=10"
        )
    
    if "hailuo" in error_str and "duration" in error_str:
        return create_error_response(
            ErrorType.VALIDATION_ERROR,
            "Invalid duration for Hailuo model",
            details={"operation": operation, "model": "hailuo_02"},
            suggestion="Hailuo model only supports durations of 6 or 10 seconds",
            example="duration=6  # or duration=10"
        )
    
    # Content safety errors
    if any(term in error_str for term in ["safety", "content policy", "inappropriate", "blocked"]):
        return create_error_response(
            ErrorType.API_ERROR,
            "Content violates safety guidelines",
            details={"operation": operation, "error": str(error)},
            suggestion="Modify your prompt to be more appropriate. Avoid sensitive or inappropriate content.",
            example="# Use professional, neutral language in prompts"
        )
    
    # Resource exhaustion
    if any(term in error_str for term in ["out of memory", "resource", "capacity"]):
        return create_error_response(
            ErrorType.API_ERROR,
            "Insufficient resources available",
            details={"operation": operation, "error": str(error)},
            suggestion="The service is at capacity. Try with smaller parameters or wait a few minutes.",
            example="# Try lower resolution or shorter duration"
        )
    
    # Generic API error with more context
    return create_error_response(
        ErrorType.API_ERROR,
        f"API error during {operation}",
        details={"operation": operation, "error": str(error), "error_type": type(error).__name__},
        suggestion="Check your parameters and try again. If the error persists, the service may be experiencing issues.",
        example=f"# Verify all parameters are correct for {operation}"
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