"""Get project timeline resource implementation."""

from typing import Dict, Any
from ..models import ProjectManager


async def get_project_timeline(project_id: str) -> Dict[str, Any]:
    """Get the scene timeline for a project."""
    try:
        project = ProjectManager.get_project(project_id)
        
        # Build timeline data
        timeline = []
        cumulative_time = 0
        
        for scene in sorted(project.scenes, key=lambda s: s.order):
            scene_data = {
                "scene_id": scene.id,
                "order": scene.order,
                "description": scene.description,
                "duration": scene.duration,
                "start_time": cumulative_time,
                "end_time": cumulative_time + scene.duration,
                "assets": {
                    "images": len([a for a in scene.assets if a.type == "image"]),
                    "videos": len([a for a in scene.assets if a.type == "video"]),
                    "audio": len(scene.audio_tracks)
                },
                "status": _get_scene_status(scene),
                "transitions": scene.transitions
            }
            timeline.append(scene_data)
            cumulative_time += scene.duration
        
        return {
            "mimetype": "application/json",
            "data": {
                "project_id": project_id,
                "total_duration": cumulative_time,
                "target_duration": project.target_duration,
                "scene_count": len(timeline),
                "timeline": timeline,
                "global_audio": [
                    {
                        "id": track.id,
                        "type": track.type,
                        "duration": track.metadata.get("duration", 0)
                    }
                    for track in project.global_audio_tracks
                ],
                "recommendations": _get_timeline_recommendations(project, cumulative_time)
            }
        }
        
    except Exception as e:
        return {
            "mimetype": "application/json",
            "data": {
                "error": str(e)
            }
        }


def _get_scene_status(scene):
    """Determine the status of a scene."""
    if not scene.assets:
        return "empty"
    
    has_video = any(a.type == "video" for a in scene.assets)
    if has_video:
        return "complete"
    
    has_image = any(a.type == "image" for a in scene.assets)
    if has_image:
        return "needs_animation"
    
    return "in_progress"


def _get_timeline_recommendations(project, current_duration):
    """Get recommendations for timeline optimization."""
    recommendations = []
    
    if project.target_duration:
        if current_duration < project.target_duration * 0.8:
            remaining = project.target_duration - current_duration
            scenes_needed = remaining // 10
            recommendations.append(f"Add {scenes_needed} more 10-second scenes to reach target duration")
        elif current_duration > project.target_duration * 1.2:
            excess = current_duration - project.target_duration
            recommendations.append(f"Consider removing {excess} seconds of content")
    
    # Check scene balance
    scene_durations = [s.duration for s in project.scenes]
    if scene_durations:
        if all(d == 5 for d in scene_durations):
            recommendations.append("Consider mixing in some 10-second scenes for variety")
        elif all(d == 10 for d in scene_durations):
            recommendations.append("Consider adding some 5-second scenes for faster pacing")
    
    return recommendations