"""Add scene tool implementation."""

from typing import Dict, Any, Optional
from datetime import datetime
from ...models import ProjectManager, Scene


async def add_scene(
    project_id: str,
    description: str,
    duration: int,
    position: Optional[int] = None
) -> Dict[str, Any]:
    """Add a scene to the project timeline."""
    try:
        # Validate duration
        if duration not in [5, 10]:
            return {
                "success": False,
                "error": "Duration must be 5 or 10 seconds for optimal generation"
            }
        
        # Get the project
        project = ProjectManager.get_project(project_id)
        
        # Create the scene
        scene = Scene(
            description=description,
            duration=duration,
            order=position if position is not None else len(project.scenes)
        )
        
        # Add to project
        added_scene = ProjectManager.add_scene(project_id, scene)
        
        # Check if we're exceeding target duration
        new_total = project.calculate_duration()
        duration_warning = None
        if project.target_duration and new_total > project.target_duration:
            duration_warning = f"Total duration ({new_total}s) exceeds target ({project.target_duration}s)"
        
        return {
            "success": True,
            "scene": {
                "id": added_scene.id,
                "order": added_scene.order,
                "description": added_scene.description,
                "duration": added_scene.duration
            },
            "project_status": {
                "total_scenes": len(project.scenes),
                "total_duration": new_total,
                "target_duration": project.target_duration
            },
            "duration_warning": duration_warning,
            "next_steps": [
                f"Generate image: generate_image_from_text('{description}', project_id='{project_id}', scene_id='{added_scene.id}')",
                f"Then animate: generate_video_from_image(image_url, motion_prompt, project_id='{project_id}', scene_id='{added_scene.id}')"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }