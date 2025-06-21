"""Image handling utilities for the MCP server."""

import re
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, Union
from .error_helpers import create_error_response, ErrorType


def is_url(data: str) -> bool:
    """Check if a string is a valid URL."""
    # Simple URL pattern check
    url_pattern = r'^https?://[^\s]+$'
    return bool(re.match(url_pattern, data))


def is_image_file(file_path: str) -> bool:
    """Check if a file path points to an image file."""
    try:
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return False
        
        # Check by MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type and mime_type.startswith('image/'):
            return True
        
        # Check by extension
        ext = path.suffix.lower()
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.svg'}
        return ext in image_extensions
        
    except Exception:
        return False


async def process_image_input(image_input: str, fal_service=None) -> Dict[str, Any]:
    """
    Process image input which can be a URL or file path.
    For file paths, automatically upload to FAL.
    
    Args:
        image_input: URL or file path
        fal_service: FAL service instance for uploading files
        
    Returns:
        Dict with:
        - valid: bool
        - type: "url" or "file"
        - data: Processed URL (original or uploaded)
        - error_response: Error response if invalid
    """
    if not image_input or not image_input.strip():
        return {
            "valid": False,
            "error_response": create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Image input cannot be empty",
                details={"parameter": "image_url"},
                suggestion="Provide an image URL or file path",
                example="image_url='https://example.com/image.jpg' or image_url='/path/to/image.png'"
            )
        }
    
    image_input = image_input.strip()
    
    # Check if it's a URL
    if is_url(image_input):
        return {
            "valid": True,
            "type": "url",
            "data": image_input
        }
    
    # Check if it's a file path
    else:
        if not is_image_file(image_input):
            return {
                "valid": False,
                "error_response": create_error_response(
                    ErrorType.VALIDATION_ERROR,
                    f"Invalid image file: {image_input}",
                    details={"parameter": "image_url", "provided": image_input},
                    suggestion="Provide a valid image URL or existing image file path",
                    example="image_url='https://example.com/image.jpg' or image_url='/path/to/image.png'"
                )
            }
        
        # If we have a FAL service, upload the file
        if fal_service:
            upload_result = await fal_service.upload_file(image_input)
            if upload_result["success"]:
                return {
                    "valid": True,
                    "type": "file",
                    "data": upload_result["url"],
                    "metadata": {
                        "original_path": image_input,
                        "uploaded_url": upload_result["url"]
                    }
                }
            else:
                return {
                    "valid": False,
                    "error_response": create_error_response(
                        ErrorType.SYSTEM_ERROR,
                        f"Failed to upload image: {upload_result['error']}",
                        details={"parameter": "image_url", "file_path": image_input},
                        suggestion="Check that the file exists and is accessible",
                        example="image_url='/path/to/existing/image.png'"
                    )
                }
        else:
            # No FAL service provided, just validate the file exists
            return {
                "valid": True,
                "type": "file",
                "data": image_input,
                "metadata": {
                    "original_path": image_input,
                    "needs_upload": True
                }
            }


