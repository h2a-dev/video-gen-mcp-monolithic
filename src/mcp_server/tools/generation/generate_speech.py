"""Generate speech tool implementation."""

from typing import Dict, Any, Optional
from ...services import fal_service, asset_storage
from ...models import ProjectManager, Asset, AssetType, AssetSource
from ...config import calculate_speech_cost


async def generate_speech(
    text: str,
    voice: str = "en-US-1",
    speed: float = 1.0,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None
) -> Dict[str, Any]:
    """Generate speech/voiceover from text."""
    try:
        # Convert speed to float if it's passed as string
        if isinstance(speed, str):
            speed = float(speed)
        
        # Validate text length
        if len(text) > 5000:
            return {
                "success": False,
                "error": "Text exceeds 5000 character limit"
            }
        
        # Generate the speech
        result = await fal_service.generate_speech(
            text=text,
            voice=voice,
            speed=speed
        )
        
        if not result["success"]:
            return result
        
        # Calculate cost
        cost = calculate_speech_cost(text)
        
        # Create asset record
        asset = Asset(
            type=AssetType.SPEECH,
            source=AssetSource.GENERATED,
            url=result["url"],
            cost=cost,
            metadata={
                "model": "minimax_speech",
                "text": text,
                "voice": voice,
                "speed": speed,
                "character_count": len(text)
            },
            generation_params={
                "text": text,
                "voice": voice,
                "speed": speed
            }
        )
        
        # If associated with a project/scene, add to it
        if project_id:
            project = ProjectManager.get_project(project_id)
            
            if scene_id:
                # Add to specific scene
                scene = next((s for s in project.scenes if s.id == scene_id), None)
                if scene:
                    scene.audio_tracks.append(asset.id)
            else:
                # Add as global audio track
                project.global_audio_tracks.append(asset)
            
            project.total_cost = project.calculate_cost()
            project.updated_at = asset.created_at
            
            # Download the asset
            download_result = await asset_storage.download_asset(
                url=result["url"],
                project_id=project_id,
                asset_id=asset.id,
                asset_type="speech"
            )
            if download_result["success"]:
                asset.local_path = download_result["local_path"]
        
        # Available voices info
        voice_options = {
            "en-US-1": "American English (Male)",
            "en-US-2": "American English (Female)",
            "en-GB-1": "British English (Male)",
            "en-GB-2": "British English (Female)",
            "es-ES-1": "Spanish (Male)",
            "es-ES-2": "Spanish (Female)",
            "fr-FR-1": "French (Male)",
            "fr-FR-2": "French (Female)",
            "de-DE-1": "German (Male)",
            "de-DE-2": "German (Female)"
        }
        
        return {
            "success": True,
            "asset": {
                "id": asset.id,
                "url": asset.url,
                "type": asset.type,
                "cost": asset.cost,
                "local_path": asset.local_path
            },
            "generation_details": {
                "model": "minimax_speech",
                "voice": voice,
                "voice_description": voice_options.get(voice, "Custom voice"),
                "speed": speed,
                "character_count": len(text)
            },
            "project_association": {
                "project_id": project_id,
                "scene_id": scene_id
            } if project_id else None,
            "available_voices": voice_options,
            "next_steps": [
                "Generate visuals for your narration",
                "Add background music with generate_music()",
                "Assemble everything with assemble_video()"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": "minimax_speech"
        }