"""Get platform specs resource implementation."""

from typing import Dict, Any
from ..config import PLATFORMS, get_platform_spec, get_aspect_ratio_dimensions


async def get_platform_specs(platform_name: str) -> Dict[str, Any]:
    """Get specifications and recommendations for a platform."""
    try:
        # Check if platform exists
        if platform_name not in PLATFORMS:
            # Return list of available platforms
            return {
                "mimetype": "application/json",
                "data": {
                    "error": f"Unknown platform: {platform_name}",
                    "available_platforms": list(PLATFORMS.keys()),
                    "suggestion": "Use 'custom' for general purpose videos"
                }
            }
        
        platform = PLATFORMS[platform_name]
        
        # Get dimension examples for aspect ratios
        dimension_examples = {}
        for ratio in platform["aspect_ratios"]:
            dimensions = get_aspect_ratio_dimensions(ratio)
            dimension_examples[ratio] = f"{dimensions[0]}x{dimensions[1]}"
        
        # Format file size for readability
        max_size_mb = platform["max_file_size"] / (1024 * 1024)
        max_size_gb = max_size_mb / 1024
        file_size_display = f"{max_size_gb:.1f} GB" if max_size_gb >= 1 else f"{max_size_mb:.0f} MB"
        
        return {
            "mimetype": "application/json",
            "data": {
                "platform": platform_name,
                "display_name": platform["name"],
                "specifications": {
                    "aspect_ratios": {
                        "supported": platform["aspect_ratios"],
                        "default": platform["default_aspect_ratio"],
                        "dimensions": dimension_examples
                    },
                    "duration": {
                        "max_seconds": platform["max_duration"],
                        "max_display": _format_duration(platform["max_duration"]),
                        "recommended_seconds": platform["recommended_duration"],
                        "recommended_display": _format_duration(platform["recommended_duration"])
                    },
                    "file": {
                        "formats": platform["formats"],
                        "max_size": file_size_display,
                        "max_size_bytes": platform["max_file_size"]
                    },
                    "technical": platform["recommendations"]
                },
                "content_tips": _get_platform_content_tips(platform_name),
                "example_commands": _get_platform_example_commands(platform_name)
            }
        }
        
    except Exception as e:
        return {
            "mimetype": "application/json",
            "data": {
                "error": str(e)
            }
        }


def _format_duration(seconds: int) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining = seconds % 60
        if remaining:
            return f"{minutes} minutes {remaining} seconds"
        return f"{minutes} minutes"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes:
            return f"{hours} hours {minutes} minutes"
        return f"{hours} hours"


def _get_platform_content_tips(platform: str) -> list:
    """Get content creation tips for specific platforms."""
    tips = {
        "youtube": [
            "Hook viewers in the first 5-10 seconds",
            "Use engaging thumbnails (generate separately)",
            "Include clear call-to-action at the end",
            "Optimize for both mobile and desktop viewing"
        ],
        "youtube_shorts": [
            "Get to the point immediately - no long intros",
            "Use vertical format for mobile viewing",
            "Add captions for silent viewing",
            "Loop-worthy content performs best"
        ],
        "tiktok": [
            "Start with the payoff or hook",
            "Use trending audio when possible",
            "Quick cuts and dynamic visuals",
            "Text overlays for key points"
        ],
        "instagram_reel": [
            "Visually striking opening frame",
            "Use Instagram's trending audio library",
            "Keep text concise and readable",
            "End with a question or call-to-action"
        ],
        "twitter": [
            "Autoplay without sound - use captions",
            "Front-load the most important content",
            "Short and punchy messaging",
            "Include your handle as a watermark"
        ]
    }
    
    return tips.get(platform, [
        "Focus on clear, engaging content",
        "Ensure good audio quality",
        "Use appropriate pacing for your audience",
        "Test on target devices before publishing"
    ])


def _get_platform_example_commands(platform: str) -> list:
    """Get example commands for creating content for the platform."""
    examples = {
        "youtube": [
            "create_project('Tutorial: Python Basics', 'youtube', target_duration=600)",
            "generate_speech(script, voice='en-US-1')",
            "generate_music('upbeat educational background music')"
        ],
        "tiktok": [
            "create_project('Quick Recipe', 'tiktok', target_duration=30)",
            "add_scene('ingredients laid out', duration=5)",
            "generate_video_from_image(image_url, 'smooth pan across ingredients')"
        ],
        "instagram_reel": [
            "create_project('Fashion Transition', 'instagram_reel')",
            "generate_image_from_text('stylish outfit flat lay')",
            "generate_music('trendy upbeat fashion music')"
        ]
    }
    
    return examples.get(platform, [
        f"create_project('My Video', '{platform}')",
        "analyze_script('Your content here...')",
        "add_scene('Opening shot', duration=5)"
    ])