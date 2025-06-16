"""Add audio track tool implementation."""

from typing import Dict, Any
from pathlib import Path
from ...services import ffmpeg_wrapper
from ...config import settings


async def add_audio_track(
    video_path: str,
    audio_path: str,
    track_type: str = "background",
    volume_adjustment: float = 1.0,
    fade_in: float = 0.0,
    fade_out: float = 0.0
) -> Dict[str, Any]:
    """Add audio track to video without re-encoding video stream."""
    try:
        # Validate inputs
        video_file = Path(video_path)
        audio_file = Path(audio_path)
        
        if not video_file.exists():
            return {
                "success": False,
                "error": f"Video file not found: {video_path}"
            }
        
        if not audio_file.exists():
            return {
                "success": False,
                "error": f"Audio file not found: {audio_path}"
            }
        
        # Validate track type
        valid_types = ["background", "voiceover", "sfx", "music"]
        if track_type not in valid_types:
            return {
                "success": False,
                "error": f"Invalid track type. Must be one of: {', '.join(valid_types)}"
            }
        
        # Adjust volume based on track type
        if track_type == "background" and volume_adjustment == 1.0:
            volume_adjustment = 0.3  # Lower background music by default
        elif track_type == "sfx" and volume_adjustment == 1.0:
            volume_adjustment = 0.7  # Moderate SFX volume
        
        # Create output path
        output_filename = video_file.stem + f"_with_{track_type}" + video_file.suffix
        output_path = video_file.parent / output_filename
        
        # Add audio track
        result = await ffmpeg_wrapper.add_audio_track(
            video_path=video_path,
            audio_path=audio_path,
            output_path=str(output_path),
            audio_volume=volume_adjustment,
            fade_in=fade_in,
            fade_out=fade_out
        )
        
        if not result["success"]:
            return result
        
        # Get output info
        output_info = await ffmpeg_wrapper.get_video_info(str(output_path))
        
        return {
            "success": True,
            "output": {
                "path": str(output_path),
                "size_mb": round(result["size"] / (1024 * 1024), 2),
                "duration": output_info.get("duration", 0)
            },
            "audio_settings": {
                "track_type": track_type,
                "volume": volume_adjustment,
                "fade_in": fade_in,
                "fade_out": fade_out,
                "filters_applied": result.get("audio_filters", [])
            },
            "technical_details": {
                "video_stream": "copied (no re-encoding)",
                "audio_stream": "aac 192k",
                "processing": "fast (stream copy)"
            },
            "next_steps": [
                "Add more audio tracks if needed",
                "Export final video with export_final_video()",
                "Preview the audio mix"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }