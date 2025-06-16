"""Download assets tool implementation."""

from typing import Dict, Any, List, Optional
from ...services import asset_storage
from ...models import ProjectManager


async def download_assets(
    asset_urls: List[str],
    project_id: str,
    asset_type: Optional[str] = None,
    parallel_downloads: int = 5
) -> Dict[str, Any]:
    """Download generated assets from FAL or other sources."""
    try:
        # Convert parallel_downloads to int if it's passed as string
        if isinstance(parallel_downloads, str):
            parallel_downloads = int(parallel_downloads)
        
        # Validate project exists
        project = ProjectManager.get_project(project_id)
        
        if not asset_urls:
            return {
                "success": False,
                "error": "No asset URLs provided"
            }
        
        # Prepare assets for download
        assets_to_download = []
        for i, url in enumerate(asset_urls):
            asset_info = {
                "url": url,
                "id": f"manual_download_{i}",
                "type": asset_type or "unknown"
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
        return {
            "success": False,
            "error": str(e)
        }