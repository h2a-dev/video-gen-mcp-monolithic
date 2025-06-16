"""Asset storage and management service."""

import os
import asyncio
import aiofiles
import httpx
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from ..config import settings


class AssetStorage:
    """Manages local storage of generated and uploaded assets."""
    
    def __init__(self):
        self.storage_dir = settings.storage_dir
        self.temp_dir = settings.temp_dir
        
    def get_asset_path(self, project_id: str, asset_id: str, extension: str) -> Path:
        """Get the local path for an asset."""
        project_dir = settings.get_project_dir(project_id)
        assets_dir = project_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        return assets_dir / f"{asset_id}.{extension}"
    
    async def download_asset(
        self,
        url: str,
        project_id: str,
        asset_id: str,
        asset_type: str
    ) -> Dict[str, Any]:
        """Download an asset from URL and store locally."""
        try:
            # Determine file extension based on asset type
            ext_map = {
                "image": "png",
                "video": "mp4",
                "audio": "mp3",
                "music": "mp3",
                "speech": "mp3"
            }
            extension = ext_map.get(asset_type, "bin")
            
            # Get local path
            local_path = self.get_asset_path(project_id, asset_id, extension)
            
            # Download the file
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=settings.download_timeout)
                response.raise_for_status()
                
                # Save to local storage
                async with aiofiles.open(local_path, 'wb') as f:
                    await f.write(response.content)
            
            # Save metadata
            metadata_path = local_path.with_suffix('.json')
            metadata = {
                "asset_id": asset_id,
                "url": url,
                "local_path": str(local_path),
                "asset_type": asset_type,
                "size": os.path.getsize(local_path),
                "downloaded_at": datetime.now().isoformat()
            }
            
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(metadata, indent=2))
            
            return {
                "success": True,
                "local_path": str(local_path),
                "size": metadata["size"],
                "metadata": metadata
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    async def download_multiple_assets(
        self,
        assets: List[Dict[str, str]],
        project_id: str,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """Download multiple assets concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_semaphore(asset):
            async with semaphore:
                return await self.download_asset(
                    url=asset["url"],
                    project_id=project_id,
                    asset_id=asset["id"],
                    asset_type=asset["type"]
                )
        
        tasks = [download_with_semaphore(asset) for asset in assets]
        results = await asyncio.gather(*tasks)
        return results
    
    def get_project_assets(self, project_id: str) -> List[Dict[str, Any]]:
        """List all assets for a project."""
        project_dir = settings.get_project_dir(project_id)
        assets_dir = project_dir / "assets"
        
        if not assets_dir.exists():
            return []
        
        assets = []
        for metadata_file in assets_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    assets.append(metadata)
            except Exception:
                continue
        
        return assets
    
    async def cleanup_temp_files(self, older_than_hours: int = 24):
        """Clean up temporary files older than specified hours."""
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (older_than_hours * 3600)
        
        cleaned = 0
        for temp_file in self.temp_dir.iterdir():
            if temp_file.is_file():
                file_time = os.path.getmtime(temp_file)
                if file_time < cutoff_time:
                    temp_file.unlink()
                    cleaned += 1
        
        return {"cleaned_files": cleaned}
    
    def get_asset_info(self, project_id: str, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific asset."""
        # Try different extensions
        for ext in ['json']:
            metadata_path = self.get_asset_path(project_id, asset_id, ext)
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    return json.load(f)
        return None
    
    def calculate_project_storage(self, project_id: str) -> Dict[str, Any]:
        """Calculate total storage used by a project."""
        project_dir = settings.get_project_dir(project_id)
        
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
        
        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count
        }


# Singleton instance
asset_storage = AssetStorage()