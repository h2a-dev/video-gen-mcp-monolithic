"""Configuration module for Video Agent MCP server."""

from .settings import settings
from .platforms import PLATFORMS, get_platform_spec, get_all_platforms, get_aspect_ratio_dimensions
from .pricing import (
    PRICING,
    calculate_image_cost,
    calculate_video_cost,
    calculate_music_cost,
    calculate_speech_cost,
    estimate_project_cost
)

__all__ = [
    "settings",
    "PLATFORMS",
    "get_platform_spec",
    "get_all_platforms",
    "get_aspect_ratio_dimensions",
    "PRICING",
    "calculate_image_cost",
    "calculate_video_cost",
    "calculate_music_cost",
    "calculate_speech_cost",
    "estimate_project_cost"
]