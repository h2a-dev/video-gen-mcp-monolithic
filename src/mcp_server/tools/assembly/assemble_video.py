"""Assemble video tool implementation."""

from typing import Dict, Any, Optional, List
import os
from pathlib import Path
from ...models import ProjectManager, ProjectStatus
from ...config import settings
from ...services import asset_storage


async def assemble_video(
    project_id: str,
    scene_ids: Optional[List[str]] = None,
    output_format: str = "mp4",
    quality_preset: str = "high"
) -> Dict[str, Any]:
    """Assemble scenes into a complete video using ffmpeg."""
    try:
        project = ProjectManager.get_project(project_id)
        
        # Update project status
        project.status = ProjectStatus.RENDERING
        
        # Get scenes to assemble
        if scene_ids:
            scenes = [s for s in project.scenes if s.id in scene_ids]
        else:
            scenes = sorted(project.scenes, key=lambda s: s.order)
        
        if not scenes:
            return {
                "success": False,
                "error": "No scenes to assemble"
            }
        
        # Check if all scenes have video assets
        missing_videos = []
        for scene in scenes:
            if not any(asset.type == "video" for asset in scene.assets):
                missing_videos.append(f"Scene {scene.order + 1}: {scene.description[:30]}...")
        
        if missing_videos:
            return {
                "success": False,
                "error": "Some scenes are missing video assets",
                "missing_videos": missing_videos,
                "suggestion": "Generate videos for these scenes first with generate_video_from_image()"
            }
        
        # Prepare output path
        output_filename = f"{project.title.replace(' ', '_')}_{project.platform}.{output_format}"
        output_path = settings.get_project_dir(project_id) / output_filename
        
        # Create concat file for ffmpeg
        concat_file = settings.temp_dir / f"{project_id}_concat.txt"
        video_paths = []
        
        with open(concat_file, 'w') as f:
            for scene in scenes:
                # Get video asset
                video_asset = next((a for a in scene.assets if a.type == "video"), None)
                if video_asset and video_asset.local_path:
                    f.write(f"file '{video_asset.local_path}'\n")
                    video_paths.append(video_asset.local_path)
        
        # Build ffmpeg command
        ffmpeg_cmd = _build_ffmpeg_command(
            concat_file,
            output_path,
            quality_preset,
            project.aspect_ratio
        )
        
        # For MVP, we'll return the command to be executed
        # In production, this would execute the command
        
        # Update project status
        project.status = ProjectStatus.COMPLETED
        
        # Calculate final statistics
        total_duration = sum(scene.duration for scene in scenes)
        total_size_estimate = total_duration * 5  # MB estimate
        
        return {
            "success": True,
            "output": {
                "path": str(output_path),
                "format": output_format,
                "duration": total_duration,
                "scenes_count": len(scenes),
                "estimated_size_mb": total_size_estimate
            },
            "assembly_details": {
                "quality_preset": quality_preset,
                "aspect_ratio": project.aspect_ratio,
                "platform": project.platform,
                "video_files": len(video_paths)
            },
            "ffmpeg_command": ffmpeg_cmd,
            "next_steps": [
                "Add audio tracks with add_audio_track() if needed",
                "Export final video with platform optimizations using export_final_video()",
                "Download the video from the output path"
            ],
            "note": "In production, this would execute ffmpeg. For MVP, use the provided command."
        }
        
    except Exception as e:
        # Reset status on error
        if 'project' in locals():
            project.status = ProjectStatus.FAILED
        
        return {
            "success": False,
            "error": str(e)
        }


def _build_ffmpeg_command(
    concat_file: Path,
    output_path: Path,
    quality_preset: str,
    aspect_ratio: str
) -> str:
    """Build ffmpeg command for video assembly."""
    
    # Quality presets
    quality_settings = {
        "low": {
            "crf": 28,
            "preset": "faster",
            "bitrate": "1M"
        },
        "medium": {
            "crf": 23,
            "preset": "medium",
            "bitrate": "2M"
        },
        "high": {
            "crf": 18,
            "preset": "slow",
            "bitrate": "5M"
        }
    }
    
    q = quality_settings.get(quality_preset, quality_settings["high"])
    
    # Build command
    cmd_parts = [
        settings.ffmpeg_path,
        "-f", "concat",
        "-safe", "0",
        "-i", f'"{concat_file}"',
        "-c:v", "libx264",
        "-preset", q["preset"],
        "-crf", str(q["crf"]),
        "-b:v", q["bitrate"],
        "-pix_fmt", "yuv420p",  # Compatibility
        "-movflags", "+faststart",  # Web optimization
    ]
    
    # Add audio settings (copy if exists)
    cmd_parts.extend(["-c:a", "aac", "-b:a", "192k"])
    
    # Output file
    cmd_parts.append(f'"{output_path}"')
    
    return " ".join(cmd_parts)