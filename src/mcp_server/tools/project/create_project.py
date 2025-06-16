"""Create project tool implementation."""

from typing import Dict, Any, Optional
from ...models import ProjectManager, VideoProject
from ...config import get_platform_spec, estimate_project_cost


async def create_project(
    title: str,
    platform: str,
    script: Optional[str] = None,
    target_duration: int = None,
    aspect_ratio: Optional[str] = None
) -> Dict[str, Any]:
    """Initialize a new video project with smart defaults based on platform."""
    try:
        # Convert target_duration to int if it's passed as string
        if target_duration is not None and isinstance(target_duration, str):
            target_duration = int(target_duration)
        
        # Get platform defaults if not specified
        if not aspect_ratio:
            aspect_ratio = get_platform_spec(platform, "default_aspect_ratio") or "16:9"
        
        if not target_duration:
            target_duration = get_platform_spec(platform, "recommended_duration") or 30
        
        # Create the project
        project = ProjectManager.create_project(
            title=title,
            platform=platform,
            script=script,
            target_duration=target_duration,
            aspect_ratio=aspect_ratio,
            description=f"Video project for {platform}"
        )
        
        # Estimate initial cost based on target duration
        # Rough estimate: 1 scene per 10 seconds
        estimated_scenes = max(1, target_duration // 10)
        cost_estimate = estimate_project_cost(
            image_count=estimated_scenes,
            video_seconds=target_duration,
            music_seconds=target_duration if target_duration > 30 else 0,
            speech_chars=len(script) if script else 0
        )
        
        return {
            "success": True,
            "project": {
                "id": project.id,
                "title": project.title,
                "platform": project.platform,
                "aspect_ratio": project.aspect_ratio,
                "target_duration": project.target_duration,
                "status": project.status,
                "created_at": project.created_at.isoformat()
            },
            "platform_info": {
                "max_duration": get_platform_spec(platform, "max_duration"),
                "formats": get_platform_spec(platform, "formats"),
                "recommendations": get_platform_spec(platform, "recommendations")
            },
            "cost_estimate": cost_estimate,
            "next_steps": [
                "Use analyze_script() to plan scenes if you have a script",
                "Add scenes with add_scene()",
                "Generate assets for each scene",
                "Assemble the final video"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }