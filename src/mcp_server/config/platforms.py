"""Platform-specific configurations for video generation."""

from typing import Dict, List, Any


PLATFORMS: Dict[str, Dict[str, Any]] = {
    "youtube": {
        "name": "YouTube",
        "aspect_ratios": ["16:9", "9:16", "4:3", "1:1"],
        "default_aspect_ratio": "16:9",
        "max_duration": 43200,  # 12 hours in seconds
        "recommended_duration": 600,  # 10 minutes
        "formats": ["mp4", "mov", "avi", "webm"],
        "max_file_size": 137438953472,  # 128 GB in bytes
        "recommendations": {
            "resolution": "1920x1080",
            "frame_rate": 30,
            "bitrate": "8-12 Mbps",
            "audio_bitrate": "384 kbps"
        }
    },
    "youtube_shorts": {
        "name": "YouTube Shorts",
        "aspect_ratios": ["9:16"],
        "default_aspect_ratio": "9:16",
        "max_duration": 60,
        "recommended_duration": 30,
        "formats": ["mp4"],
        "max_file_size": 1073741824,  # 1 GB in bytes
        "recommendations": {
            "resolution": "1080x1920",
            "frame_rate": 30,
            "bitrate": "8-10 Mbps",
            "audio_bitrate": "256 kbps"
        }
    },
    "tiktok": {
        "name": "TikTok",
        "aspect_ratios": ["9:16"],
        "default_aspect_ratio": "9:16",
        "max_duration": 600,  # 10 minutes
        "recommended_duration": 60,
        "formats": ["mp4"],
        "max_file_size": 4294967296,  # 4 GB in bytes
        "recommendations": {
            "resolution": "1080x1920",
            "frame_rate": 30,
            "bitrate": "8-10 Mbps",
            "audio_bitrate": "256 kbps"
        }
    },
    "instagram_reel": {
        "name": "Instagram Reel",
        "aspect_ratios": ["9:16"],
        "default_aspect_ratio": "9:16",
        "max_duration": 90,
        "recommended_duration": 30,
        "formats": ["mp4"],
        "max_file_size": 1073741824,  # 1 GB in bytes
        "recommendations": {
            "resolution": "1080x1920",
            "frame_rate": 30,
            "bitrate": "5-8 Mbps",
            "audio_bitrate": "192 kbps"
        }
    },
    "instagram_post": {
        "name": "Instagram Post",
        "aspect_ratios": ["1:1", "4:5"],
        "default_aspect_ratio": "1:1",
        "max_duration": 60,
        "recommended_duration": 30,
        "formats": ["mp4"],
        "max_file_size": 1073741824,  # 1 GB in bytes
        "recommendations": {
            "resolution": "1080x1080",
            "frame_rate": 30,
            "bitrate": "5-8 Mbps",
            "audio_bitrate": "192 kbps"
        }
    },
    "twitter": {
        "name": "Twitter/X",
        "aspect_ratios": ["16:9", "1:1"],
        "default_aspect_ratio": "16:9",
        "max_duration": 140,
        "recommended_duration": 60,
        "formats": ["mp4"],
        "max_file_size": 536870912,  # 512 MB in bytes
        "recommendations": {
            "resolution": "1280x720",
            "frame_rate": 30,
            "bitrate": "5-6 Mbps",
            "audio_bitrate": "192 kbps"
        }
    },
    "linkedin": {
        "name": "LinkedIn",
        "aspect_ratios": ["16:9", "1:1", "4:5"],
        "default_aspect_ratio": "16:9",
        "max_duration": 600,  # 10 minutes
        "recommended_duration": 120,
        "formats": ["mp4"],
        "max_file_size": 5368709120,  # 5 GB in bytes
        "recommendations": {
            "resolution": "1920x1080",
            "frame_rate": 30,
            "bitrate": "8-10 Mbps",
            "audio_bitrate": "256 kbps"
        }
    },
    "facebook": {
        "name": "Facebook",
        "aspect_ratios": ["16:9", "9:16", "1:1", "4:5"],
        "default_aspect_ratio": "16:9",
        "max_duration": 14400,  # 4 hours
        "recommended_duration": 180,
        "formats": ["mp4", "mov"],
        "max_file_size": 10737418240,  # 10 GB in bytes
        "recommendations": {
            "resolution": "1920x1080",
            "frame_rate": 30,
            "bitrate": "8-12 Mbps",
            "audio_bitrate": "256 kbps"
        }
    },
    "custom": {
        "name": "Custom",
        "aspect_ratios": ["16:9", "9:16", "1:1", "4:5", "4:3", "21:9"],
        "default_aspect_ratio": "16:9",
        "max_duration": 3600,  # 1 hour
        "recommended_duration": 300,
        "formats": ["mp4", "mov", "avi", "webm", "mkv"],
        "max_file_size": 53687091200,  # 50 GB in bytes
        "recommendations": {
            "resolution": "1920x1080",
            "frame_rate": 30,
            "bitrate": "10-15 Mbps",
            "audio_bitrate": "320 kbps"
        }
    }
}


def get_platform_spec(platform: str, spec: str) -> Any:
    """Get a specific specification for a platform."""
    if platform not in PLATFORMS:
        platform = "custom"
    return PLATFORMS[platform].get(spec)


def get_all_platforms() -> List[str]:
    """Get list of all supported platforms."""
    return list(PLATFORMS.keys())


def get_aspect_ratio_dimensions(aspect_ratio: str, height: int = 1080) -> tuple[int, int]:
    """Convert aspect ratio string to dimensions."""
    ratios = {
        "16:9": (1920, 1080),
        "9:16": (1080, 1920),
        "1:1": (1080, 1080),
        "4:5": (864, 1080),
        "4:3": (1440, 1080),
        "21:9": (2560, 1080)
    }
    
    if aspect_ratio in ratios and height == 1080:
        return ratios[aspect_ratio]
    
    # Calculate custom dimensions
    parts = aspect_ratio.split(":")
    if len(parts) == 2:
        width_ratio = float(parts[0])
        height_ratio = float(parts[1])
        width = int(height * (width_ratio / height_ratio))
        return (width, height)
    
    return (1920, 1080)  # Default fallback