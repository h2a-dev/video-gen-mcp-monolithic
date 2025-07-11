"""Prompts module for Video Agent MCP server."""

from .video_creation_wizard import video_creation_wizard
from .script_to_scenes import script_to_scenes
from .list_video_agent_capabilities import list_video_agent_capabilities

__all__ = [
    "video_creation_wizard",
    "script_to_scenes",
    "list_video_agent_capabilities"
]