"""Upload image file tool implementation."""

from typing import Dict, Any
from pathlib import Path
from ...services import fal_service
from ...utils import create_error_response, ErrorType
from ...utils.image_helpers import is_image_file


async def upload_image_file(file_path: str) -> Dict[str, Any]:
    """
    Upload a local image file to FAL and get a URL.
    
    Args:
        file_path: Path to the local image file
        
    Returns:
        Dict with upload results including the URL
    """
    try:
        # Validate file path
        if not file_path or not file_path.strip():
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "File path cannot be empty",
                details={"parameter": "file_path"},
                suggestion="Provide a path to an image file",
                example="upload_image_file('/path/to/image.jpg')"
            )
        
        # Check if it's a valid image file
        if not is_image_file(file_path):
            path = Path(file_path)
            if not path.exists():
                return create_error_response(
                    ErrorType.RESOURCE_NOT_FOUND,
                    f"File not found: {file_path}",
                    details={"file_path": file_path},
                    suggestion="Check that the file path is correct and the file exists",
                    example="upload_image_file('/existing/path/to/image.png')"
                )
            elif not path.is_file():
                return create_error_response(
                    ErrorType.VALIDATION_ERROR,
                    f"Path is not a file: {file_path}",
                    details={"file_path": file_path},
                    suggestion="Provide a path to a file, not a directory",
                    example="upload_image_file('/path/to/specific/image.jpg')"
                )
            else:
                return create_error_response(
                    ErrorType.VALIDATION_ERROR,
                    f"File does not appear to be an image: {file_path}",
                    details={"file_path": file_path},
                    suggestion="Provide a path to a valid image file (jpg, png, gif, webp, etc.)",
                    example="upload_image_file('/path/to/image.png')"
                )
        
        # Upload the file
        result = await fal_service.upload_file(file_path)
        
        if not result["success"]:
            return create_error_response(
                ErrorType.SYSTEM_ERROR,
                f"Failed to upload file: {result.get('error', 'Unknown error')}",
                details={"file_path": file_path, "error": result.get('error')},
                suggestion="Check that the file is accessible and try again",
                example="Ensure the file exists and you have read permissions"
            )
        
        # Get file info
        path = Path(file_path)
        file_size = path.stat().st_size
        
        return {
            "success": True,
            "url": result["url"],
            "file_info": {
                "original_path": file_path,
                "file_name": path.name,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2)
            },
            "usage": {
                "description": "Use this URL in image or video generation tools",
                "examples": [
                    f"generate_video_from_image('{result['url']}', 'camera slowly zooms in')",
                    f"generate_image_from_image('{result['url']}', 'make it more colorful')"
                ]
            }
        }
        
    except Exception as e:
        return create_error_response(
            ErrorType.SYSTEM_ERROR,
            f"Unexpected error uploading file: {str(e)}",
            details={"file_path": file_path, "error": str(e)},
            suggestion="Check the file path and try again",
            example="upload_image_file('/valid/path/to/image.jpg')"
        )