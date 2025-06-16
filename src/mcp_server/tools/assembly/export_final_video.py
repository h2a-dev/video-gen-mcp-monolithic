"""Export final video tool implementation."""

from typing import Dict, Any, Optional
from pathlib import Path
from ...models import ProjectManager, ProjectStatus
from ...config import settings, get_platform_spec
from ...services import ffmpeg_wrapper


async def export_final_video(
    project_id: str,
    platform: str,
    include_captions: bool = False,
    include_watermark: bool = False,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """Export video with platform-specific optimizations."""
    try:
        project = ProjectManager.get_project(project_id)
        
        # Check if video has been assembled
        assembled_videos = list(settings.get_project_dir(project_id).glob("*.mp4"))
        if not assembled_videos:
            return {
                "success": False,
                "error": "No assembled video found. Run assemble_video() first."
            }
        
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
        if video_info.get("duration", 0) > platform_specs["max_duration"]:
            return {
                "success": False,
                "error": f"Video duration ({video_info['duration']}s) exceeds platform limit ({platform_specs['max_duration']}s)",
                "suggestion": "Trim your video or remove scenes"
            }
        
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
        if output_size > platform_specs["max_file_size"]:
            size_mb = output_size / (1024 * 1024)
            max_mb = platform_specs["max_file_size"] / (1024 * 1024)
            return {
                "success": False,
                "error": f"Output file ({size_mb:.1f}MB) exceeds platform limit ({max_mb:.1f}MB)",
                "suggestion": "Reduce quality preset or shorten video duration",
                "output_path": str(output_path)  # Still provide path for inspection
            }
        
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
        return {
            "success": False,
            "error": str(e)
        }


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