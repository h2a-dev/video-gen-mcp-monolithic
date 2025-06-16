"""Generate speech tool implementation."""

from typing import Dict, Any, Optional
import sys
from ...services import fal_service, asset_storage
from ...models import ProjectManager, Asset, AssetType, AssetSource
from ...config import calculate_speech_cost


# Define valid voices at module level for reuse
VALID_VOICES = {
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

# Common voice mistakes/variations mapping
VOICE_ALIASES = {
    # Common variations
    "wise_woman": "Wise_Woman",
    "wise woman": "Wise_Woman",
    "female": "Wise_Woman",
    "woman": "Wise_Woman",
    "professional": "Wise_Woman",
    "friendly_person": "Friendly_Person",
    "friendly person": "Friendly_Person",
    "friendly": "Friendly_Person",
    "male": "Deep_Voice_Man",
    "man": "Deep_Voice_Man",
    "deep voice": "Deep_Voice_Man",
    "deep_voice_man": "Deep_Voice_Man",
    "calm_woman": "Calm_Woman",
    "calm woman": "Calm_Woman",
    "calm": "Calm_Woman",
    "casual_guy": "Casual_Guy",
    "casual guy": "Casual_Guy",
    "casual": "Casual_Guy",
    "inspirational_girl": "Inspirational_girl",
    "inspirational girl": "Inspirational_girl",
    "inspirational": "Inspirational_girl",
    # Common AI confusions
    "narrator": "Friendly_Person",
    "voiceover": "Friendly_Person",
    "default": "Wise_Woman",
    "neutral": "Friendly_Person"
}


async def generate_speech(
    text: str,
    voice: str = "Wise_Woman",
    speed: float = 1.0,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None
) -> Dict[str, Any]:
    """Generate speech/voiceover from text.
    
    Args:
        text: The text to convert to speech (max 5000 characters)
        voice: Voice ID - must be one of: Wise_Woman, Friendly_Person, Deep_Voice_Man, Calm_Woman, etc.
        speed: Speech speed (0.5-2.0, default 1.0)
        project_id: Optional project to associate the speech with
        scene_id: Optional scene within the project
    """
    try:
        # Convert speed to float if it's passed as string
        if isinstance(speed, str):
            speed = float(speed)
        
        # Validate and normalize voice parameter
        original_voice = voice
        
        # First check if it's already a valid voice
        if voice not in VALID_VOICES:
            # Try to find it in aliases (case-insensitive)
            voice_lower = voice.lower()
            if voice_lower in VOICE_ALIASES:
                voice = VOICE_ALIASES[voice_lower]
                print(f"[GenerateSpeech] Mapped voice '{original_voice}' to '{voice}'", file=sys.stderr)
            else:
                # Return error with helpful information
                return {
                    "success": False,
                    "error": f"Invalid voice: '{original_voice}'. Please use one of these exact voice IDs:",
                    "valid_voices": {
                        "female_voices": {
                            "Wise_Woman": "Professional, authoritative female",
                            "Calm_Woman": "Soothing, peaceful female", 
                            "Inspirational_girl": "Energetic, motivating female",
                            "Lively_Girl": "Cheerful, animated female",
                            "Lovely_Girl": "Sweet, gentle female",
                            "Sweet_Girl_2": "Soft, pleasant female",
                            "Exuberant_Girl": "Enthusiastic, vibrant female",
                            "Abbess": "Mature, wise female"
                        },
                        "male_voices": {
                            "Deep_Voice_Man": "Deep, commanding male",
                            "Casual_Guy": "Relaxed, conversational male",
                            "Patient_Man": "Understanding, gentle male",
                            "Young_Knight": "Heroic, youthful male",
                            "Determined_Man": "Strong, confident male",
                            "Decent_Boy": "Young, friendly male",
                            "Imposing_Manner": "Authoritative, powerful male",
                            "Elegant_Man": "Refined, sophisticated male"
                        },
                        "neutral_voices": {
                            "Friendly_Person": "Warm, approachable narrator"
                        }
                    },
                    "quick_suggestions": [
                        "For professional narration: use 'Wise_Woman' or 'Deep_Voice_Man'",
                        "For friendly content: use 'Friendly_Person' or 'Casual_Guy'",
                        "For motivational content: use 'Inspirational_girl' or 'Determined_Man'"
                    ],
                    "correct_usage": "generate_speech(text='Your text', voice='Wise_Woman')"
                }
        
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
        
        # Use the module-level voice options
        voice_options = VALID_VOICES
        
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
                "voice_used": voice,
                "original_voice_request": original_voice if original_voice != voice else None,
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