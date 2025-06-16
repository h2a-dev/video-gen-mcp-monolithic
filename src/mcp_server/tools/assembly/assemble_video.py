"""Assemble video tool implementation."""

from typing import Dict, Any, Optional, List
import os
from pathlib import Path
from ...models import ProjectManager, ProjectStatus
from ...config import settings
from ...services import asset_storage, ffmpeg_wrapper


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
        
        # Collect video paths
        video_paths = []
        
        for scene in scenes:
            # Get video asset
            video_asset = next((a for a in scene.assets if a.type == "video"), None)
            if video_asset and video_asset.local_path:
                video_paths.append(video_asset.local_path)
        
        # Use ffmpeg_wrapper to concatenate videos
        concat_result = await ffmpeg_wrapper.concat_videos(
            video_paths=video_paths,
            output_path=str(output_path),
            quality_preset=quality_preset
        )
        
        if not concat_result["success"]:
            return {
                "success": False,
                "error": f"Failed to assemble video: {concat_result['error']}"
            }
        
        # Check if we have global audio tracks to add
        if project.global_audio_tracks:
            # Add global audio tracks one by one
            current_output = str(output_path)
            for i, audio_track in enumerate(project.global_audio_tracks):
                if audio_track.local_path:
                    temp_output = settings.temp_dir / f"{project_id}_audio_{i}.{output_format}"
                    
                    # Determine track type based on metadata
                    track_type = "background"
                    if audio_track.type == "speech":
                        track_type = "voiceover"
                    elif audio_track.type == "music":
                        track_type = "music"
                    
                    # Add audio track
                    audio_result = await ffmpeg_wrapper.add_audio_track(
                        video_path=current_output,
                        audio_path=audio_track.local_path,
                        output_path=str(temp_output),
                        audio_volume=0.3 if track_type == "background" else 1.0
                    )
                    
                    if audio_result["success"]:
                        # If not the final output, remove intermediate file
                        if current_output != str(output_path):
                            Path(current_output).unlink(missing_ok=True)
                        current_output = str(temp_output)
            
            # Move final output to correct location
            if current_output != str(output_path):
                Path(current_output).rename(output_path)
        
        # Update project status
        project.status = ProjectStatus.COMPLETED
        
        # Calculate final statistics
        total_duration = sum(scene.duration for scene in scenes)
        total_size_estimate = total_duration * 5  # MB estimate
        
        # Get actual file info
        video_info = await ffmpeg_wrapper.get_video_info(str(output_path))
        actual_size_mb = round(os.path.getsize(output_path) / (1024 * 1024), 2)
        
        return {
            "success": True,
            "output": {
                "path": str(output_path),
                "format": output_format,
                "duration": video_info.get("duration", total_duration),
                "scenes_count": len(scenes),
                "size_mb": actual_size_mb,
                "resolution": f"{video_info.get('width', 0)}x{video_info.get('height', 0)}",
                "fps": video_info.get("fps", 0)
            },
            "assembly_details": {
                "quality_preset": quality_preset,
                "aspect_ratio": project.aspect_ratio,
                "platform": project.platform,
                "video_files": len(video_paths),
                "audio_tracks_added": len(project.global_audio_tracks),
                "dynamic_transitions": True,
                "frames_trimmed": concat_result.get("trimmed_frames", 0)
            },
            "next_steps": [
                "Export final video with platform optimizations using export_final_video()",
                "Add additional audio tracks with add_audio_track() if needed",
                "Download the video from the output path"
            ],
            "status": "Video successfully assembled with dynamic transitions!",
            "note": "First 15 frames trimmed from each scene (except the first) for smoother, more dynamic transitions"
        }
        
    except Exception as e:
        # Reset status on error
        if 'project' in locals():
            project.status = ProjectStatus.FAILED
        
        return {
            "success": False,
            "error": str(e)
        }


