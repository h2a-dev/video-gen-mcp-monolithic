"""Download assets tool implementation."""

from typing import Dict, Any, List, Optional
from ...services import asset_storage
from ...models import ProjectManager
from ...utils import (
    create_error_response,
    ErrorType,
    validate_range,
    validate_project_exists,
    handle_file_operation_error
)


async def download_assets(
    asset_urls: List[str],
    project_id: str,
    asset_type: Optional[str] = None,
    parallel_downloads: int = 5
) -> Dict[str, Any]:
    """Download generated assets from FAL or other sources.
    
    Args:
        asset_urls: List of URLs to download
        project_id: Project to associate downloads with
        asset_type: Optional type ('image', 'video', 'audio') - leave empty for auto-detection
        parallel_downloads: Number of concurrent downloads (1-10)
    
    Note: For mixed asset types (e.g., videos AND audio), leave asset_type as None.
    The tool will auto-detect types from file extensions.
    """
    try:
        # Validate asset_urls
        if not asset_urls:
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "No asset URLs provided",
                details={"parameter": "asset_urls"},
                suggestion="Provide a list of asset URLs to download",
                example="download_assets(asset_urls=['https://...', 'https://...'], project_id='...')"
            )
        
        if not isinstance(asset_urls, list):
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Asset URLs must be provided as a list",
                details={"parameter": "asset_urls", "type_provided": type(asset_urls).__name__},
                suggestion="Wrap your URLs in a list, even for a single URL",
                example="download_assets(asset_urls=['https://example.com/asset.mp4'], project_id='...')"
            )
        
        # Validate each URL is a string
        invalid_urls = []
        for i, url in enumerate(asset_urls):
            if not isinstance(url, str) or not url.strip():
                invalid_urls.append(i)
        
        if invalid_urls:
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                f"Invalid URLs at positions: {invalid_urls}",
                details={"invalid_positions": invalid_urls, "total_urls": len(asset_urls)},
                suggestion="Ensure all URLs are non-empty strings",
                example="Each URL should be a valid string like 'https://example.com/asset.mp4'"
            )
        
        # Validate project exists
        project_validation = validate_project_exists(project_id, ProjectManager)
        if not project_validation["valid"]:
            return project_validation["error_response"]
        
        # Validate parallel_downloads
        downloads_validation = validate_range(
            parallel_downloads, "parallel_downloads", 1, 10, "Parallel downloads"
        )
        if not downloads_validation["valid"]:
            return downloads_validation["error_response"]
        parallel_downloads = int(downloads_validation["value"])
        
        # Validate asset_type if provided
        valid_asset_types = ["image", "video", "audio", "unknown"]
        if asset_type and asset_type not in valid_asset_types:
            # Check if user is trying to download mixed assets
            if asset_type in ["mixed", "all", "various"]:
                return create_error_response(
                    ErrorType.VALIDATION_ERROR,
                    "Cannot specify 'mixed' asset type. Leave asset_type empty for mixed downloads.",
                    details={"parameter": "asset_type", "provided": asset_type},
                    valid_options={
                        "asset_types": valid_asset_types,
                        "for_mixed_assets": "Leave asset_type parameter unspecified (None)"
                    },
                    suggestion="For mixed asset types, omit the asset_type parameter entirely",
                    example="download_assets(asset_urls=[...], project_id='...') # No asset_type"
                )
            else:
                return create_error_response(
                    ErrorType.VALIDATION_ERROR,
                    f"Invalid asset type: '{asset_type}'",
                    details={"parameter": "asset_type", "provided": asset_type},
                    valid_options={"asset_types": valid_asset_types},
                    suggestion="Use 'image', 'video', 'audio', or leave unspecified for auto-detection",
                    example="asset_type='video' # or omit for auto-detection"
                )
        
        # Prepare assets for download with auto-detection
        assets_to_download = []
        for i, url in enumerate(asset_urls):
            # Auto-detect type from URL if not specified
            detected_type = asset_type
            if not detected_type:
                url_lower = url.lower()
                if any(ext in url_lower for ext in ['.mp4', '.mov', '.avi', '.webm']):
                    detected_type = "video"
                elif any(ext in url_lower for ext in ['.mp3', '.wav', '.aac', '.m4a']):
                    detected_type = "audio"
                elif any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    detected_type = "image"
                else:
                    detected_type = "unknown"
            
            asset_info = {
                "url": url,
                "id": f"manual_download_{i}",
                "type": detected_type
            }
            assets_to_download.append(asset_info)
        
        # Download assets
        results = await asset_storage.download_multiple_assets(
            assets=assets_to_download,
            project_id=project_id,
            max_concurrent=min(parallel_downloads, 10)  # Cap at 10
        )
        
        # Process results
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]
        
        # Calculate total size
        total_size = sum(r.get("size", 0) for r in successful)
        
        return {
            "success": True,
            "summary": {
                "total_requested": len(asset_urls),
                "successful_downloads": len(successful),
                "failed_downloads": len(failed),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            },
            "downloads": {
                "successful": [
                    {
                        "url": r["metadata"]["url"],
                        "local_path": r["local_path"],
                        "size_mb": round(r["size"] / (1024 * 1024), 2)
                    }
                    for r in successful
                ],
                "failed": [
                    {
                        "url": r["url"],
                        "error": r["error"]
                    }
                    for r in failed
                ]
            },
            "storage_info": asset_storage.calculate_project_storage(project_id),
            "next_steps": [
                "Use downloaded assets in your video assembly",
                "Check failed downloads and retry if needed",
                "Clean up temporary files when done"
            ]
        }
        
    except Exception as e:
        # Check for specific error patterns
        error_str = str(e).lower()
        if "not found" in error_str:
            return create_error_response(
                ErrorType.RESOURCE_NOT_FOUND,
                f"Project not found: {project_id}",
                details={"project_id": project_id},
                suggestion="Use list_projects() to see available projects",
                example="First check projects: list_projects()"
            )
        
        if "connection" in error_str or "timeout" in error_str:
            return create_error_response(
                ErrorType.API_ERROR,
                "Network error while downloading assets",
                details={"error": str(e)},
                suggestion="Check your internet connection and try again",
                example="Consider downloading fewer assets at once or increasing timeout"
            )
        
        # Generic error
        return create_error_response(
            ErrorType.SYSTEM_ERROR,
            f"Failed to download assets: {str(e)}",
            details={"error": str(e)},
            suggestion="Check the asset URLs are valid and accessible",
            example="Ensure all URLs point to valid, downloadable files"
        )