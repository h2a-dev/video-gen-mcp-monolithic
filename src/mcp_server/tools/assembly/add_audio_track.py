"""Add audio track tool implementation."""

from typing import Dict, Any
from pathlib import Path
from ...services import ffmpeg_wrapper
from ...config import settings
from ...utils import (
    create_error_response,
    ErrorType,
    validate_enum,
    validate_range,
    handle_file_operation_error
)


async def add_audio_track(
    video_path: str,
    audio_path: str,
    track_type: str = "background",
    volume_adjustment: float = 1.0,
    fade_in: float = 0.0,
    fade_out: float = 0.0
) -> Dict[str, Any]:
    """Add audio track to video without re-encoding video stream.
    
    WARNING: If you used assemble_video(), audio tracks are already mixed!
    This tool is only needed for manual audio addition to videos created outside the normal workflow.
    """
    try:
        # Check if this looks like an assembled video
        video_file = Path(video_path)
        if "_with_audio" in video_file.name or (video_file.parent.name and "project" in str(video_file.parent)):
            return create_error_response(
                ErrorType.STATE_ERROR,
                "This video was created by assemble_video and already has all audio tracks mixed!",
                details={"video_path": video_path},
                suggestion="Do NOT add audio tracks to assembled videos. The audio is already included.",
                example="If you need different audio, regenerate with assemble_video()"
            )
        # Validate file paths
        if not video_path or not video_path.strip():
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Video path cannot be empty",
                details={"parameter": "video_path"},
                suggestion="Provide the path to the video file",
                example="add_audio_track(video_path='/path/to/video.mp4', audio_path='/path/to/audio.mp3')"
            )
        
        if not audio_path or not audio_path.strip():
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Audio path cannot be empty",
                details={"parameter": "audio_path"},
                suggestion="Provide the path to the audio file",
                example="add_audio_track(video_path='/path/to/video.mp4', audio_path='/path/to/audio.mp3')"
            )
        
        # Check files exist
        video_file = Path(video_path)
        audio_file = Path(audio_path)
        
        if not video_file.exists():
            return handle_file_operation_error(
                FileNotFoundError(f"Video file not found: {video_path}"),
                video_path,
                "reading video file"
            )
        
        if not audio_file.exists():
            return handle_file_operation_error(
                FileNotFoundError(f"Audio file not found: {audio_path}"),
                audio_path,
                "reading audio file"
            )
        
        # Validate track type
        valid_types = ["background", "voiceover", "sfx", "music"]
        type_validation = validate_enum(track_type, "track_type", valid_types, "audio track type")
        if not type_validation["valid"]:
            type_validation["error_response"]["valid_options"] = {
                "background": "Background music (auto-lowered to 30% volume)",
                "voiceover": "Voice narration (full volume)",
                "sfx": "Sound effects (70% volume)",
                "music": "Music track (full volume)"
            }
            return type_validation["error_response"]
        
        # Validate numeric parameters
        volume_validation = validate_range(
            volume_adjustment, "volume_adjustment", 0.0, 2.0, "Volume adjustment"
        )
        if not volume_validation["valid"]:
            volume_validation["error_response"]["suggestion"] = "Use 0.0 for mute, 1.0 for normal, 2.0 for double volume"
            return volume_validation["error_response"]
        volume_adjustment = volume_validation["value"]
        
        fade_in_validation = validate_range(
            fade_in, "fade_in", 0.0, 10.0, "Fade in duration"
        )
        if not fade_in_validation["valid"]:
            return fade_in_validation["error_response"]
        fade_in = fade_in_validation["value"]
        
        fade_out_validation = validate_range(
            fade_out, "fade_out", 0.0, 10.0, "Fade out duration"
        )
        if not fade_out_validation["valid"]:
            return fade_out_validation["error_response"]
        fade_out = fade_out_validation["value"]
        
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
        # Check for specific error patterns
        error_str = str(e).lower()
        if "codec" in error_str or "format" in error_str:
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Unsupported audio/video format",
                details={"error": str(e)},
                suggestion="Ensure video is MP4 and audio is MP3/AAC/WAV",
                example="Convert files to supported formats first"
            )
        
        if "permission" in error_str:
            return handle_file_operation_error(e, str(output_path), "writing output file")
        
        # Generic error
        return create_error_response(
            ErrorType.SYSTEM_ERROR,
            f"Failed to add audio track: {str(e)}",
            details={"error": str(e)},
            suggestion="Check file paths and formats are correct",
            example="Ensure both files are accessible and in supported formats"
        )