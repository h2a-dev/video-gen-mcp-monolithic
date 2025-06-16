"""Generate speech tool implementation."""

from typing import Dict, Any, Optional
from ...services import fal_service, asset_storage
from ...models import ProjectManager, Asset, AssetType, AssetSource
from ...config import calculate_speech_cost


async def generate_speech(
    text: str,
    voice: str = "Wise_Woman",
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
        
        # Get audio duration
        audio_duration = result.get("duration_seconds", 0)
        
        # If project is specified, check against expected duration
        duration_warning = None
        if project_id:
            project = ProjectManager.get_project(project_id)
            if project.target_duration:
                # Calculate effective duration after frame trimming
                scene_count = len(project.scenes) if project.scenes else 3  # Default estimate
                trimmed_duration = 0.5 * (scene_count - 1)
                effective_duration = project.target_duration - trimmed_duration
                
                if audio_duration > effective_duration:
                    duration_warning = (
                        f"⚠️ Audio is {audio_duration - effective_duration:.1f}s too long! "
                        f"Target: {effective_duration:.1f}s (after {trimmed_duration:.1f}s transitions), "
                        f"Actual: {audio_duration:.1f}s. Consider trimming the script or increasing speed."
                    )
        
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
            "Wise_Woman": "Wise Woman (Female)",
            "Friendly_Person": "Friendly Person",
            "Inspirational_girl": "Inspirational Girl",
            "Deep_Voice_Man": "Deep Voice Man",
            "Calm_Woman": "Calm Woman",
            "Casual_Guy": "Casual Guy",
            "Lively_Girl": "Lively Girl",
            "Patient_Man": "Patient Man",
            "Young_Knight": "Young Knight",
            "Determined_Man": "Determined Man",
            "Lovely_Girl": "Lovely Girl",
            "Decent_Boy": "Decent Boy",
            "Imposing_Manner": "Imposing Manner",
            "Elegant_Man": "Elegant Man",
            "Abbess": "Abbess",
            "Sweet_Girl_2": "Sweet Girl 2",
            "Exuberant_Girl": "Exuberant Girl"
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
                "character_count": len(text),
                "duration_seconds": audio_duration
            },
            "project_association": {
                "project_id": project_id,
                "scene_id": scene_id
            } if project_id else None,
            "available_voices": voice_options,
            "duration_warning": duration_warning,
            "next_steps": [
                "Generate visuals for your narration",
                "Add background music with generate_music()",
                "Assemble everything with assemble_video()"
            ] if not duration_warning else [
                "Consider regenerating with shorter text or faster speed",
                "Or extend your video duration to match the audio"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": "minimax_speech"
        }