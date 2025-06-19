"""Image handling utilities for the MCP server."""

import re
import base64
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, Union
from .error_helpers import create_error_response, ErrorType


def is_base64_image(data: str) -> bool:
    """Check if a string is a base64 encoded image data URI."""
    # Check for data URI pattern: data:image/[format];base64,[data]
    pattern = r'^data:image/[a-zA-Z]+;base64,[A-Za-z0-9+/]+=*$'
    return bool(re.match(pattern, data))


def is_url(data: str) -> bool:
    """Check if a string is a valid URL."""
    # Simple URL pattern check
    url_pattern = r'^https?://[^\s]+$'
    return bool(re.match(url_pattern, data))


def get_image_mime_type(file_path: str) -> Optional[str]:
    """Get MIME type for an image file."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and mime_type.startswith('image/'):
        return mime_type
    
    # Fallback for common image extensions
    ext = Path(file_path).suffix.lower()
    mime_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.bmp': 'image/bmp'
    }
    return mime_map.get(ext)


def file_to_base64_data_uri(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Convert an image file to a base64 data URI.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Dict with:
        - success: bool
        - data_uri: The base64 data URI string (if success)
        - error: Error message (if failed)
    """
    try:
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        # Check if it's a file (not directory)
        if not path.is_file():
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}"
            }
        
        # Get MIME type
        mime_type = get_image_mime_type(str(path))
        if not mime_type:
            return {
                "success": False,
                "error": f"File does not appear to be an image: {file_path}"
            }
        
        # Read file and encode to base64
        with open(path, 'rb') as f:
            image_data = f.read()
            base64_encoded = base64.b64encode(image_data).decode('utf-8')
            data_uri = f"data:{mime_type};base64,{base64_encoded}"
            
        return {
            "success": True,
            "data_uri": data_uri,
            "mime_type": mime_type,
            "file_size": len(image_data)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read image file: {str(e)}"
        }


def process_image_input(image_input: str) -> Dict[str, Any]:
    """
    Process image input which can be a URL, base64 data URI, or file path.
    
    Args:
        image_input: URL, base64 data URI, or file path
        
    Returns:
        Dict with:
        - valid: bool
        - type: "url", "base64", or "file"
        - data: Processed data (URL or base64 data URI)
        - error_response: Error response if invalid
    """
    if not image_input or not image_input.strip():
        return {
            "valid": False,
            "error_response": create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Image input cannot be empty",
                details={"parameter": "image_url"},
                suggestion="Provide an image URL, base64 data URI, or file path",
                example="image_url='https://example.com/image.jpg' or image_url='/path/to/image.png'"
            )
        }
    
    image_input = image_input.strip()
    
    # Check if it's a base64 data URI
    if image_input.startswith("data:image/"):
        if is_base64_image(image_input):
            return {
                "valid": True,
                "type": "base64",
                "data": image_input
            }
        else:
            return {
                "valid": False,
                "error_response": create_error_response(
                    ErrorType.VALIDATION_ERROR,
                    "Invalid base64 image data URI format",
                    details={"parameter": "image_url"},
                    suggestion="Ensure the base64 data URI follows the format: data:image/[format];base64,[data]",
                    example="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                )
            }
    
    # Check if it's a URL
    elif is_url(image_input):
        return {
            "valid": True,
            "type": "url",
            "data": image_input
        }
    
    # Check if it's a file path
    else:
        # Try to convert file to base64
        result = file_to_base64_data_uri(image_input)
        
        if result["success"]:
            return {
                "valid": True,
                "type": "file",
                "data": result["data_uri"],
                "metadata": {
                    "original_path": image_input,
                    "mime_type": result["mime_type"],
                    "file_size": result["file_size"]
                }
            }
        else:
            return {
                "valid": False,
                "error_response": create_error_response(
                    ErrorType.VALIDATION_ERROR,
                    f"Invalid image input: {result['error']}",
                    details={"parameter": "image_url", "provided": image_input},
                    suggestion="Provide a valid image URL, base64 data URI, or existing image file path",
                    example="image_url='https://example.com/image.jpg' or image_url='/path/to/image.png'"
                )
            }


def validate_image_input(image_data: str) -> Dict[str, Any]:
    """
    Validate and process image input (backwards compatible wrapper).
    
    Args:
        image_data: Either a URL string, base64 data URI, or file path
        
    Returns:
        Dict with validation result
    """
    return process_image_input(image_data)