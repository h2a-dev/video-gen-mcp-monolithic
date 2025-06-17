"""Create project tool implementation."""

from typing import Dict, Any, Optional
from ...models import ProjectManager, VideoProject
from ...config import get_platform_spec, estimate_project_cost
from ...utils import (
    create_error_response,
    ErrorType,
    validate_platform,
    validate_aspect_ratio,
    validate_range
)


# Valid platforms and aspect ratios
VALID_PLATFORMS = {
    "youtube": "Standard YouTube video (16:9, up to 12 hours)",
    "youtube_shorts": "YouTube Shorts (9:16, max 60 seconds)",
    "tiktok": "TikTok video (9:16, 15 seconds to 10 minutes)",
    "instagram_reel": "Instagram Reel (9:16, up to 90 seconds)",
    "instagram_post": "Instagram Feed video (1:1 or 4:5, up to 60 seconds)",
    "twitter": "Twitter/X video (16:9 or 1:1, up to 2:20)",
    "linkedin": "LinkedIn video (16:9 or 1:1, up to 10 minutes)",
    "facebook": "Facebook video (16:9, 9:16, or 1:1)",
    "custom": "Custom platform with your own specifications"
}

VALID_ASPECT_RATIOS = {
    "16:9": "Widescreen (YouTube, TV, monitors)",
    "9:16": "Vertical (TikTok, Reels, Stories)",
    "1:1": "Square (Instagram feed, some social media)",
    "4:5": "Portrait (Instagram feed)",
    "21:9": "Ultrawide (cinematic)",
    "4:3": "Classic TV format"
}


async def create_project(
    title: str,
    platform: str,
    script: Optional[str] = None,
    target_duration: Optional[int] = None,
    aspect_ratio: Optional[str] = None
) -> Dict[str, Any]:
    """Initialize a new video project with smart defaults based on platform.
    
    Args:
        title: Project title/name
        platform: Target platform (youtube, tiktok, instagram_reel, etc.)
        script: Optional script/narration text
        target_duration: Target video duration in seconds
        aspect_ratio: Video aspect ratio (uses platform default if not specified)
    """
    try:
        # Validate title
        if not title or not title.strip():
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Project title cannot be empty",
                details={"parameter": "title"},
                suggestion="Provide a descriptive title for your project",
                example="create_project(title='My Product Launch Video', platform='youtube')"
            )
        
        # Validate platform
        platform_validation = validate_platform(platform, VALID_PLATFORMS)
        if not platform_validation["valid"]:
            return platform_validation["error_response"]
        
        # Validate and convert target_duration if provided
        if target_duration is not None:
            try:
                target_duration = int(target_duration) if isinstance(target_duration, str) else target_duration
            except (ValueError, TypeError):
                return create_error_response(
                    ErrorType.VALIDATION_ERROR,
                    "Target duration must be a number",
                    details={"parameter": "target_duration", "provided": target_duration},
                    suggestion="Provide duration as an integer in seconds",
                    example="target_duration=30"
                )
            
            # Validate duration range
            duration_validation = validate_range(
                target_duration, 
                "target_duration", 
                1, 
                3600,  # 1 hour max
                "Target duration"
            )
            if not duration_validation["valid"]:
                return duration_validation["error_response"]
            
            # Platform-specific duration validation
            platform_max = get_platform_spec(platform, "max_duration")
            if platform_max and target_duration > platform_max:
                return create_error_response(
                    ErrorType.VALIDATION_ERROR,
                    f"{platform} videos cannot exceed {platform_max} seconds",
                    details={
                        "platform": platform,
                        "target_duration": target_duration,
                        "max_duration": platform_max
                    },
                    suggestion=f"Use a duration of {platform_max} seconds or less for {platform}",
                    example=f"target_duration={min(30, platform_max)}"
                )
        
        # Validate aspect ratio if provided
        if aspect_ratio:
            ratio_validation = validate_aspect_ratio(aspect_ratio, VALID_ASPECT_RATIOS)
            if not ratio_validation["valid"]:
                return ratio_validation["error_response"]
        else:
            # Get platform default if not specified
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
        return create_error_response(
            ErrorType.SYSTEM_ERROR,
            f"Failed to create project: {str(e)}",
            details={"error": str(e)},
            suggestion="Check your parameters and try again",
            example="create_project(title='My Video', platform='youtube')"
        )