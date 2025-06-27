"""Generate music tool implementation."""

from typing import Dict, Any, Optional
from ...services import fal_service, asset_storage
from ...models import ProjectManager, Asset, AssetType, AssetSource
from ...config import calculate_music_cost
from ...utils import handle_fal_api_error


async def generate_music(
    prompt: str,
    duration: int = 95,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """Generate background music from a text description."""
    try:
        # Convert duration to int if it's passed as string
        if isinstance(duration, str):
            duration = int(duration)
        
        # Lyria2 generates ~95 seconds of music
        actual_duration = 95
        
        # Generate the music
        result = await fal_service.generate_music(
            prompt=prompt,
            duration=actual_duration
        )
        
        if not result["success"]:
            # If it's an API error, provide helpful context
            if "error" in result:
                return handle_fal_api_error(Exception(result["error"]), "music generation")
            return result
        
        # Calculate cost
        cost = calculate_music_cost(actual_duration)
        
        # Create asset record
        asset = Asset(
            type=AssetType.MUSIC,
            source=AssetSource.GENERATED,
            url=result["url"],
            cost=cost,
            metadata={
                "model": "lyria2",
                "prompt": prompt,
                "duration": actual_duration
            },
            generation_params={
                "prompt": prompt,
                "model": "lyria2"
            }
        )
        
        # If associated with a project, add as global audio track
        if project_id:
            project = ProjectManager.get_project(project_id)
            project.global_audio_tracks.append(asset)
            project.total_cost = project.calculate_cost()
            project.updated_at = asset.created_at
            
            # Download the asset
            download_result = await asset_storage.download_asset(
                url=result["url"],
                project_id=project_id,
                asset_id=asset.id,
                asset_type="music"
            )
            if download_result["success"]:
                asset.local_path = download_result["local_path"]
        
        return {
            "success": True,
            "asset": {
                "id": asset.id,
                "url": asset.url,
                "type": asset.type,
                "cost": asset.cost,
                "duration": actual_duration,
                "local_path": asset.local_path
            },
            "generation_details": {
                "model": "lyria2",
                "prompt": prompt,
                "duration": actual_duration
            },
            "project_association": {
                "project_id": project_id
            } if project_id else None,
            "notes": [
                f"Generated {actual_duration} seconds of music",
                "Music will be looped or trimmed during video assembly",
                "For custom duration, the audio will be adjusted in post-processing"
            ],
            "next_steps": [
                "Add voiceover: generate_speech() if you need narration",
                "Continue generating visual content for your scenes",
                "IMPORTANT: assemble_video() automatically mixes ALL audio - no need to use add_audio_track()",
                "For multiple music tracks: Just generate them all before assembly"
            ]
        }
        
    except Exception as e:
        # Check if it's an API error
        if "fal" in str(e).lower() or "api" in str(e).lower() or "downstream" in str(e).lower():
            return handle_fal_api_error(e, "music generation")
        
        # Generic error
        return {
            "success": False,
            "error": str(e),
            "model": "lyria2"
        }