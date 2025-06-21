"""Add scene tool implementation."""

from typing import Dict, Any, Optional
from datetime import datetime
from ...models import ProjectManager, Scene
from ...utils import (
    create_error_response,
    ErrorType,
    validate_duration,
    validate_range,
    validate_project_exists
)


async def add_scene(
    project_id: str,
    description: str,
    duration: int,
    position: Optional[int] = None
) -> Dict[str, Any]:
    """Add a scene to the project timeline."""
    try:
        # Validate description
        if not description or not description.strip():
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Scene description cannot be empty",
                details={"parameter": "description"},
                suggestion="Provide a clear description of what should happen in this scene",
                example="add_scene(project_id='...', description='Hero walking through city streets', duration=10)"
            )
        
        # Validate duration (5, 6, or 10 seconds to support both Kling and Hailuo)
        duration_validation = validate_duration(duration, valid_durations=[5, 6, 10])
        if not duration_validation["valid"]:
            return duration_validation["error_response"]
        duration = duration_validation["value"]
        
        # Validate position if provided
        if position is not None:
            position_validation = validate_range(
                position, "position", 0, 100, "Scene position"
            )
            if not position_validation["valid"]:
                return position_validation["error_response"]
            position = int(position_validation["value"])
        
        # Validate project exists
        project_validation = validate_project_exists(project_id, ProjectManager)
        if not project_validation["valid"]:
            return project_validation["error_response"]
        
        project = project_validation["project"]
        
        # Create the scene
        scene = Scene(
            description=description,
            duration=duration,
            order=position if position is not None else len(project.scenes)
        )
        
        # Check if position is valid before adding
        if position is not None and position > len(project.scenes):
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                f"Position {position} is invalid (project has {len(project.scenes)} scenes)",
                details={
                    "position": position,
                    "current_scenes": len(project.scenes)
                },
                suggestion=f"Use a position between 0 and {len(project.scenes)}",
                example=f"add_scene(..., position={len(project.scenes)})  # Add at end"
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
        # Check for specific error patterns
        error_str = str(e).lower()
        if "not found" in error_str:
            return create_error_response(
                ErrorType.RESOURCE_NOT_FOUND,
                f"Project not found: {project_id}",
                details={"project_id": project_id},
                suggestion="Use list_projects() to see available projects",
                example="First check projects: list_projects()"
            )
        
        return create_error_response(
            ErrorType.SYSTEM_ERROR,
            f"Failed to add scene: {str(e)}",
            details={"error": str(e)},
            suggestion="Check your parameters and try again",
            example="add_scene(project_id='...', description='Scene description', duration=10)"
        )