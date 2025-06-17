"""Export final video tool implementation."""

from typing import Dict, Any, Optional
from pathlib import Path
from ...models import ProjectManager, ProjectStatus
from ...config import settings, get_platform_spec
from ...services import ffmpeg_wrapper
from ...utils import (
    create_error_response,
    ErrorType,
    validate_platform,
    validate_project_exists,
    handle_file_operation_error
)

# Valid platforms for export
VALID_PLATFORMS = {
    "youtube": "YouTube optimized (H.264, AAC)",
    "youtube_shorts": "YouTube Shorts (vertical, <60s)",
    "tiktok": "TikTok optimized (vertical)",
    "instagram_reel": "Instagram Reels (vertical)",
    "instagram_post": "Instagram Feed video",
    "twitter": "Twitter/X video",
    "linkedin": "LinkedIn video",
    "facebook": "Facebook video",
    "generic": "Generic MP4 (compatible everywhere)"
}


async def export_final_video(
    project_id: str,
    platform: str,
    include_captions: bool = False,
    include_watermark: bool = False,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """Export video with platform-specific optimizations."""
    try:
        # Validate project exists
        project_validation = validate_project_exists(project_id, ProjectManager)
        if not project_validation["valid"]:
            return project_validation["error_response"]
        
        project = project_validation["project"]
        
        # Validate platform
        platform_validation = validate_platform(platform, VALID_PLATFORMS)
        if not platform_validation["valid"]:
            return platform_validation["error_response"]
        
        # Check if video has been assembled
        assembled_videos = list(settings.get_project_dir(project_id).glob("*.mp4"))
        if not assembled_videos:
            return create_error_response(
                ErrorType.STATE_ERROR,
                "No assembled video found for this project",
                details={"project_id": project_id},
                suggestion="Run assemble_video() first to create the video",
                example=f"assemble_video(project_id='{project_id}')"
            )
        
        # Use the most recent assembled video
        input_video = max(assembled_videos, key=lambda p: p.stat().st_mtime)
        
        # Determine output path
        if not output_path:
            output_filename = f"{project.title.replace(' ', '_')}_{platform}_final.mp4"
            output_path = settings.get_project_dir(project_id) / "exports" / output_filename
            output_path.parent.mkdir(exist_ok=True)
        
        # Get platform specifications
        platform_specs = {
            "aspect_ratio": get_platform_spec(platform, "default_aspect_ratio"),
            "max_duration": get_platform_spec(platform, "max_duration"),
            "max_file_size": get_platform_spec(platform, "max_file_size"),
            "recommendations": get_platform_spec(platform, "recommendations")
        }
        
        # Check duration compliance
        video_info = await ffmpeg_wrapper.get_video_info(str(input_video))
        video_duration = video_info.get("duration", 0)
        max_duration = platform_specs.get("max_duration")
        
        if max_duration and video_duration > max_duration:
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                f"Video duration exceeds {platform} limit",
                details={
                    "video_duration": f"{video_duration}s",
                    "platform_limit": f"{max_duration}s",
                    "excess": f"{video_duration - max_duration}s"
                },
                suggestion="Trim your video or remove scenes to meet platform requirements",
                example="Consider removing scenes or shortening durations"
            )
        
        # Export with platform optimization
        watermark_text = project.title if include_watermark else None
        
        result = await ffmpeg_wrapper.export_for_platform(
            input_path=str(input_video),
            output_path=str(output_path),
            platform=platform,
            include_watermark=include_watermark,
            watermark_text=watermark_text
        )
        
        if not result["success"]:
            return result
        
        # Check file size compliance
        output_size = result["size"]
        max_file_size = platform_specs.get("max_file_size")
        
        if max_file_size and output_size > max_file_size:
            size_mb = output_size / (1024 * 1024)
            max_mb = max_file_size / (1024 * 1024)
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                f"Output file size exceeds {platform} limit",
                details={
                    "file_size": f"{size_mb:.1f}MB",
                    "platform_limit": f"{max_mb:.1f}MB",
                    "excess": f"{size_mb - max_mb:.1f}MB",
                    "output_path": str(output_path)  # Still provide path for inspection
                },
                suggestion="Reduce quality preset or shorten video duration",
                example="Try exporting with lower quality or remove some scenes"
            )
        
        # Update project status
        project.status = ProjectStatus.COMPLETED
        
        # Platform-specific recommendations
        platform_tips = _get_platform_export_tips(platform)
        
        return {
            "success": True,
            "output": {
                "path": str(output_path),
                "size_mb": result["size_mb"],
                "duration": result["duration"],
                "platform": platform,
                "optimizations_applied": {
                    "watermark": include_watermark,
                    "captions": include_captions,
                    "platform_preset": platform
                }
            },
            "platform_compliance": {
                "aspect_ratio": platform_specs["aspect_ratio"],
                "duration_ok": video_info.get("duration", 0) <= platform_specs["max_duration"],
                "size_ok": output_size <= platform_specs["max_file_size"]
            },
            "platform_tips": platform_tips,
            "next_steps": [
                f"Upload to {platform.replace('_', ' ').title()}",
                "Review video quality and make adjustments if needed",
                "Consider creating versions for other platforms"
            ]
        }
        
    except Exception as e:
        # Check for specific error patterns
        error_str = str(e).lower()
        if "not found" in error_str:
            return create_error_response(
                ErrorType.RESOURCE_NOT_FOUND,
                "Resource not found",
                details={"error": str(e)},
                suggestion="Check that the project exists and has been assembled",
                example="First run: assemble_video(project_id='...')"
            )
        
        if "permission" in error_str:
            return handle_file_operation_error(e, str(output_path) if 'output_path' in locals() else "output", "exporting video")
        
        # Generic error
        return create_error_response(
            ErrorType.SYSTEM_ERROR,
            f"Failed to export video: {str(e)}",
            details={"error": str(e)},
            suggestion="Check project status and try again",
            example="Ensure the video has been assembled first"
        )


def _get_platform_export_tips(platform: str) -> list:
    """Get platform-specific export tips."""
    tips = {
        "youtube": [
            "Add an eye-catching thumbnail separately",
            "Include timestamps in description for chapters",
            "Upload in highest quality for YouTube processing"
        ],
        "youtube_shorts": [
            "Ensure video is exactly vertical (9:16)",
            "Add #Shorts to title or description",
            "Keep under 60 seconds for Shorts shelf"
        ],
        "tiktok": [
            "Upload directly from mobile for best results",
            "Add trending sounds after upload",
            "Use TikTok's built-in text and effects"
        ],
        "instagram_reel": [
            "Share to Reels, not regular posts",
            "Add location tags for better reach",
            "Use Instagram's music library when possible"
        ],
        "twitter": [
            "Keep under 2:20 for best engagement",
            "Add captions for silent autoplay",
            "Tweet with relevant hashtags"
        ],
        "linkedin": [
            "Native uploads perform better than YouTube links",
            "Add professional context in post",
            "Tag relevant people and companies"
        ]
    }
    
    return tips.get(platform, [
        "Check platform's latest requirements",
        "Test on target devices",
        "Monitor initial engagement"
    ])