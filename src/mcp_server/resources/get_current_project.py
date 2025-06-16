"""Get current project resource implementation."""

from typing import Dict, Any
from ..models import ProjectManager


async def get_current_project() -> Dict[str, Any]:
    """Get the currently active project details."""
    try:
        project = ProjectManager.get_current_project()
        
        if not project:
            return {
                "mimetype": "application/json",
                "data": {
                    "status": "no_active_project",
                    "message": "No project currently active. Use create_project() to start."
                }
            }
        
        # Calculate progress
        progress = 0
        if project.target_duration and project.actual_duration > 0:
            progress = min(100, int((project.actual_duration / project.target_duration) * 100))
        
        return {
            "mimetype": "application/json",
            "data": {
                "project": {
                    "id": project.id,
                    "title": project.title,
                    "platform": project.platform,
                    "status": project.status,
                    "aspect_ratio": project.aspect_ratio,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat()
                },
                "progress": {
                    "scenes": len(project.scenes),
                    "actual_duration": project.actual_duration,
                    "target_duration": project.target_duration,
                    "progress_percentage": progress,
                    "total_cost": project.total_cost
                },
                "assets": {
                    "scene_assets": sum(len(scene.assets) for scene in project.scenes),
                    "global_audio_tracks": len(project.global_audio_tracks)
                },
                "next_actions": _get_next_actions(project)
            }
        }
        
    except Exception as e:
        return {
            "mimetype": "application/json",
            "data": {
                "error": str(e)
            }
        }


def _get_next_actions(project):
    """Determine next recommended actions based on project state."""
    actions = []
    
    if not project.scenes:
        actions.append("Add scenes with add_scene()")
        if project.script:
            actions.append("Use analyze_script() to plan scenes")
    else:
        # Check if scenes have assets
        scenes_without_assets = [s for s in project.scenes if not s.assets]
        if scenes_without_assets:
            actions.append(f"Generate assets for {len(scenes_without_assets)} scenes")
        
        # Check if we have audio
        if not project.global_audio_tracks:
            actions.append("Add background music with generate_music()")
            if project.script:
                actions.append("Generate voiceover with generate_speech()")
        
        # Ready to assemble?
        if all(scene.assets for scene in project.scenes):
            actions.append("Ready to assemble_video()")
    
    return actions