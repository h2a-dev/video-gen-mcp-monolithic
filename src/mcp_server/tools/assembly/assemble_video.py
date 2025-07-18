"""Assemble video tool implementation."""

from typing import Dict, Any, Optional, List
import os
import sys
from pathlib import Path
from ...models import ProjectManager, ProjectStatus
from ...config import settings
from ...services import asset_storage, ffmpeg_wrapper


async def assemble_video(
    project_id: str,
    scene_ids: Optional[List[str]] = None,
    output_format: str = "mp4",
    quality_preset: str = "high",
    add_logo: bool = False,
    logo_position: str = "bottom_right",
    logo_padding: int = 10,
    add_end_video: bool = False
) -> Dict[str, Any]:
    """Assemble scenes into a complete video using ffmpeg.
    
    Args:
        project_id: ID of the project to assemble
        scene_ids: Optional list of scene IDs to include (uses all if None)
        output_format: Video format (default: mp4)
        quality_preset: Quality level - high, medium, low (default: high)
        add_logo: Whether to add logo overlay (default: False)
        logo_position: Corner position - bottom_right, bottom_left, top_right, top_left (default: bottom_right)
        logo_padding: Padding from edges in pixels (default: 10)
        add_end_video: Whether to append h2a_end.mp4 to the end of the video (default: False)
    
    Returns:
        Dict with assembly results including output path and metadata
    """
    
    try:
        print(f"[AssembleVideo] Starting assembly for project {project_id}", file=sys.stderr)
        project = ProjectManager.get_project(project_id)
        
        # Check if video has already been assembled
        project_dir = settings.get_project_dir(project_id)
        existing_videos = list(project_dir.glob(f"{project.title.replace(' ', '_')}_{project.platform}.{output_format}"))
        if existing_videos:
            # Check if the existing video has audio
            existing_video = existing_videos[0]
            video_info = await ffmpeg_wrapper.get_video_info(str(existing_video))
            if video_info.get('has_audio', False):
                print(f"[AssembleVideo] Video already assembled with audio: {existing_video.name}", file=sys.stderr)
                return {
                    "success": True,
                    "output": {
                        "path": str(existing_video),
                        "format": output_format,
                        "duration": video_info.get("duration", 0),
                        "size_mb": round(existing_video.stat().st_size / (1024 * 1024), 2),
                        "already_assembled": True
                    },
                    "message": "Video was already assembled with audio tracks. No need to call add_audio_track!",
                    "next_steps": [
                        "Video is COMPLETE! Do not add audio tracks.",
                        "Download the video from the output path",
                        "Share your creation!"
                    ]
                }
        
        # Track files to clean up
        temp_files_created = []
        
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
                print(f"[AssembleVideo] Added video: {video_asset.local_path}", file=sys.stderr)
        
        # Add end video if requested
        if add_end_video:
            end_video_path = settings.logos_dir / "h2a_end.mp4"
            if end_video_path.exists():
                # Check end video compatibility first
                end_video_info = await ffmpeg_wrapper.get_video_info(str(end_video_path))
                print(f"[AssembleVideo] End video info: {end_video_info}", file=sys.stderr)
                
                if end_video_info.get("error"):
                    print(f"[AssembleVideo] ERROR: Cannot read end video: {end_video_info['error']}", file=sys.stderr)
                    print(f"[AssembleVideo] Continuing without end video", file=sys.stderr)
                else:
                    video_paths.append(str(end_video_path))
                    print(f"[AssembleVideo] Added end video: {end_video_path}", file=sys.stderr)
                    print(f"[AssembleVideo] End video duration: {end_video_info.get('duration', 0):.2f}s", file=sys.stderr)
                    print(f"[AssembleVideo] End video resolution: {end_video_info.get('width', 0)}x{end_video_info.get('height', 0)}", file=sys.stderr)
            else:
                print(f"[AssembleVideo] WARNING: End video not found at {end_video_path}", file=sys.stderr)
                print(f"[AssembleVideo] Continuing without end video", file=sys.stderr)
        
        # Use ffmpeg_wrapper to concatenate videos
        print(f"[AssembleVideo] Concatenating {len(video_paths)} videos...", file=sys.stderr)
        concat_result = await ffmpeg_wrapper.concat_videos(
            video_paths=video_paths,
            output_path=str(output_path),
            quality_preset=quality_preset
        )
        print(f"[AssembleVideo] Concatenation complete", file=sys.stderr)
        
        # Check if concatenated video has audio
        concat_info = await ffmpeg_wrapper.get_video_info(str(output_path))
        print(f"[AssembleVideo] Concatenated video has audio: {concat_info.get('has_audio', False)}", file=sys.stderr)
        
        if not concat_result["success"]:
            return {
                "success": False,
                "error": f"Failed to assemble video: {concat_result['error']}"
            }
        
        # Check if we have global audio tracks to add
        if project.global_audio_tracks:
            print(f"[AssembleVideo] Found {len(project.global_audio_tracks)} audio tracks to add", file=sys.stderr)
            
            # Prepare audio tracks info
            audio_tracks_info = []
            for audio_track in project.global_audio_tracks:
                if audio_track.local_path:
                    track_info = {
                        "path": audio_track.local_path,
                        "type": "voiceover" if audio_track.type == "speech" else "music",
                        "volume": 1.0 if audio_track.type == "speech" else 0.3
                    }
                    audio_tracks_info.append(track_info)
                    print(f"[AssembleVideo] - {track_info['type']}: volume={track_info['volume']}", file=sys.stderr)
            
            if len(audio_tracks_info) > 1:
                # Use the new method to mix all tracks at once
                # Create unique temp filename to avoid conflicts
                import time
                timestamp = int(time.time())
                temp_output = settings.get_project_dir(project_id) / f".temp_audio_mixed_{timestamp}.{output_format}"
                temp_files_created.append(temp_output)
                print(f"[AssembleVideo] Mixing {len(audio_tracks_info)} audio tracks in one pass", file=sys.stderr)
                
                audio_result = await ffmpeg_wrapper.add_multiple_audio_tracks(
                    video_path=str(output_path),
                    audio_tracks=audio_tracks_info,
                    output_path=str(temp_output)
                )
                
                if audio_result["success"]:
                    print(f"[AssembleVideo] Successfully mixed all audio tracks", file=sys.stderr)
                    # Replace original with audio version atomically
                    backup_path = output_path.with_suffix('.backup')
                    try:
                        Path(output_path).rename(backup_path)  # Backup original
                        Path(temp_output).rename(output_path)  # Move new file
                        backup_path.unlink()  # Delete backup
                        temp_files_created.remove(temp_output)  # No longer a temp file
                    except Exception as e:
                        print(f"[AssembleVideo] Error replacing file: {e}", file=sys.stderr)
                        # Restore backup if something went wrong
                        if backup_path.exists():
                            backup_path.rename(output_path)
                else:
                    print(f"[AssembleVideo] Failed to mix audio tracks: {audio_result.get('error', 'Unknown error')}", file=sys.stderr)
                    # Fall back to sequential adding
                    await _add_audio_tracks_sequentially(
                        ffmpeg_wrapper, output_path, audio_tracks_info, 
                        output_format, project_id, settings
                    )
            elif len(audio_tracks_info) == 1:
                # Single track, use simple add
                import time
                timestamp = int(time.time())
                temp_output = settings.get_project_dir(project_id) / f".temp_audio_single_{timestamp}.{output_format}"
                temp_files_created.append(temp_output)
                track = audio_tracks_info[0]
                
                print(f"[AssembleVideo] Adding single {track['type']} track", file=sys.stderr)
                audio_result = await ffmpeg_wrapper.add_audio_track(
                    video_path=str(output_path),
                    audio_path=track["path"],
                    output_path=str(temp_output),
                    audio_volume=track["volume"]
                )
                
                if audio_result["success"]:
                    print(f"[AssembleVideo] Successfully added {track['type']} track", file=sys.stderr)
                    # Replace original with audio version atomically
                    backup_path = output_path.with_suffix('.backup')
                    try:
                        Path(output_path).rename(backup_path)  # Backup original
                        Path(temp_output).rename(output_path)  # Move new file
                        backup_path.unlink()  # Delete backup
                        temp_files_created.remove(temp_output)  # No longer a temp file
                    except Exception as e:
                        print(f"[AssembleVideo] Error replacing file: {e}", file=sys.stderr)
                        if backup_path.exists():
                            backup_path.rename(output_path)
                else:
                    print(f"[AssembleVideo] Failed to add {track['type']} track: {audio_result.get('error', 'Unknown error')}", file=sys.stderr)
        
        # Add logo overlay if requested
        if add_logo:
            print(f"[AssembleVideo] Adding logo overlay at {logo_position}", file=sys.stderr)
            
            # Determine logo path - check for h2a.png in multiple locations
            logo_candidates = [
                settings.storage_dir / "assets" / "logos" / "h2a.png",  # Preferred location
                settings.base_dir / "h2a.png",  # Fallback to base directory
                Path("video-gen-mcp-monolithic") / "h2a.png",  # Local relative path
            ]
            
            logo_path = None
            for candidate in logo_candidates:
                if candidate.exists():
                    logo_path = candidate
                    print(f"[AssembleVideo] Found logo at: {logo_path}", file=sys.stderr)
                    break
            
            if not logo_path:
                print(f"[AssembleVideo] WARNING: Logo file h2a.png not found in any expected location", file=sys.stderr)
                print(f"[AssembleVideo] Searched locations: {[str(p) for p in logo_candidates]}", file=sys.stderr)
            else:
                # Create temp file for logo overlay
                import time
                timestamp = int(time.time())
                temp_logo_output = settings.get_project_dir(project_id) / f".temp_logo_{timestamp}.{output_format}"
                temp_files_created.append(temp_logo_output)
                
                logo_result = await ffmpeg_wrapper.add_logo_overlay(
                    input_path=str(output_path),
                    logo_path=str(logo_path),
                    output_path=str(temp_logo_output),
                    position=logo_position,
                    padding=logo_padding
                )
                
                if logo_result["success"]:
                    print(f"[AssembleVideo] Successfully added logo overlay", file=sys.stderr)
                    # Replace original with logo version atomically
                    backup_path = output_path.with_suffix('.logo_backup')
                    try:
                        Path(output_path).rename(backup_path)  # Backup original
                        Path(temp_logo_output).rename(output_path)  # Move new file
                        backup_path.unlink()  # Delete backup
                        temp_files_created.remove(temp_logo_output)  # No longer a temp file
                    except Exception as e:
                        print(f"[AssembleVideo] Error replacing file with logo version: {e}", file=sys.stderr)
                        if backup_path.exists():
                            backup_path.rename(output_path)
                else:
                    print(f"[AssembleVideo] Failed to add logo: {logo_result.get('error', 'Unknown error')}", file=sys.stderr)
        
        # Clean up temporary files we created
        print(f"[AssembleVideo] Cleaning up {len(temp_files_created)} temporary files", file=sys.stderr)
        for temp_file in temp_files_created:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    print(f"[AssembleVideo] Removed temporary file: {temp_file.name}", file=sys.stderr)
            except Exception as e:
                print(f"[AssembleVideo] Failed to remove {temp_file.name}: {e}", file=sys.stderr)
        
        # Also clean up any leftover temp files from previous runs
        project_dir = settings.get_project_dir(project_id)
        for old_temp in project_dir.glob(".temp_audio_*.mp4"):
            try:
                old_temp.unlink()
                print(f"[AssembleVideo] Removed old temp file: {old_temp.name}", file=sys.stderr)
            except Exception as e:
                print(f"[AssembleVideo] Failed to remove old temp {old_temp.name}: {e}", file=sys.stderr)
        
        # Update project status
        project.status = ProjectStatus.COMPLETED
        
        # Calculate final statistics
        total_duration = sum(scene.duration for scene in scenes)
        total_size_estimate = total_duration * 5  # MB estimate
        
        # Get actual file info
        video_info = await ffmpeg_wrapper.get_video_info(str(output_path))
        actual_size_mb = round(os.path.getsize(output_path) / (1024 * 1024), 2)
        
        # List all video files in project directory for debugging
        video_files = list(project_dir.glob(f"*.{output_format}"))
        print(f"[AssembleVideo] Final video files in project: {[f.name for f in video_files]}", file=sys.stderr)
        
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
                "seconds_trimmed": concat_result.get("trimmed_seconds", 0),
                "logo_added": add_logo,
                "logo_position": logo_position if add_logo else None,
                "logo_padding": logo_padding if add_logo else None,
                "end_video_added": add_end_video
            },
            "next_steps": [
                f"Video is COMPLETE with all audio mixed{' and logo overlay added' if add_logo else ''}{' and end video appended' if add_end_video else ''}!",
                "Download the video from the output path",
                "Share your creation!"
            ],
            "status": f"Video successfully assembled with ALL audio tracks mixed{' and logo overlay' if add_logo else ''}{' and end video' if add_end_video else ''}!",
            "note": f"Video includes all voiceover and music tracks{' plus logo overlay' if add_logo else ''}{' and H2A end video' if add_end_video else ''}. DO NOT call add_audio_track - audio is already mixed!"
        }
        
    except Exception as e:
        # Reset status on error
        if 'project' in locals():
            project.status = ProjectStatus.FAILED
        
        print(f"[AssembleVideo] Error: {str(e)}", file=sys.stderr)
        return {
            "success": False,
            "error": str(e)
        }
    
async def _add_audio_tracks_sequentially(
    ffmpeg_wrapper, output_path, audio_tracks_info, 
    output_format, project_id, settings
):
        """Fallback method to add audio tracks one by one."""
        current_output = str(output_path)
        temp_files_to_clean = []
        
        for i, track in enumerate(audio_tracks_info):
            import time
            timestamp = int(time.time())
            temp_output = settings.get_project_dir(project_id) / f".temp_audio_seq_{i}_{timestamp}.{output_format}"
            temp_files_to_clean.append(temp_output)
            
            print(f"[AssembleVideo] Adding {track['type']} track {i+1}/{len(audio_tracks_info)} (fallback)", file=sys.stderr)
            audio_result = await ffmpeg_wrapper.add_audio_track(
                video_path=current_output,
                audio_path=track["path"],
                output_path=str(temp_output),
                audio_volume=track["volume"]
            )
            
            if audio_result["success"]:
                print(f"[AssembleVideo] Successfully added {track['type']} track", file=sys.stderr)
                # Clean up previous temp file if not the original
                if current_output != str(output_path) and Path(current_output) in temp_files_to_clean:
                    try:
                        Path(current_output).unlink(missing_ok=True)
                        temp_files_to_clean.remove(Path(current_output))
                    except:
                        pass
                current_output = str(temp_output)
            else:
                print(f"[AssembleVideo] Failed to add {track['type']} track: {audio_result.get('error', 'Unknown error')}", file=sys.stderr)
        
        # Move final output to correct location
        if current_output != str(output_path):
            Path(current_output).rename(output_path)
            if Path(current_output) in temp_files_to_clean:
                temp_files_to_clean.remove(Path(current_output))
        
        # Clean up any remaining temp files
        for temp_file in temp_files_to_clean:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except:
                pass


