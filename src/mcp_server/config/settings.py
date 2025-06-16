"""Configuration settings for the Video Agent MCP server."""

import os
from pathlib import Path
from typing import Optional


class Settings:
    """Server configuration settings."""
    
    def __init__(self):
        # Server metadata
        self.server_name = "video-agent"
        self.version = "0.1.0"
        self.description = "Comprehensive video creation MCP server"
        
        # API configuration
        self.fal_api_key = os.getenv("FALAI_API_KEY", "")
        
        # Storage paths
        self.base_dir = Path(__file__).parent.parent.parent.parent
        self.storage_dir = Path(os.getenv("VIDEO_AGENT_STORAGE", str(self.base_dir / "storage")))
        self.temp_dir = self.storage_dir / "temp"
        self.projects_dir = self.storage_dir / "projects"
        self.templates_dir = self.base_dir / "templates"
        
        # Ensure directories exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        
        # API limits and defaults
        self.max_parallel_downloads = int(os.getenv("MAX_PARALLEL_DOWNLOADS", "5"))
        self.download_timeout = int(os.getenv("DOWNLOAD_TIMEOUT", "300"))  # seconds
        self.generation_timeout = int(os.getenv("GENERATION_TIMEOUT", "600"))  # seconds
        
        # Default generation parameters
        self.default_image_model = os.getenv("DEFAULT_IMAGE_MODEL", "imagen4")
        self.default_video_model = os.getenv("DEFAULT_VIDEO_MODEL", "kling-2.1")
        self.default_music_model = os.getenv("DEFAULT_MUSIC_MODEL", "lyria2")
        self.default_speech_model = os.getenv("DEFAULT_SPEECH_MODEL", "minimax")
        
        # Video assembly settings
        self.ffmpeg_path = os.getenv("FFMPEG_PATH", "ffmpeg")
        self.default_video_codec = os.getenv("DEFAULT_VIDEO_CODEC", "libx264")
        self.default_audio_codec = os.getenv("DEFAULT_AUDIO_CODEC", "aac")
        self.default_output_format = os.getenv("DEFAULT_OUTPUT_FORMAT", "mp4")
        
        # Cost tracking
        self.enable_cost_tracking = os.getenv("ENABLE_COST_TRACKING", "true").lower() == "true"
        self.cost_warning_threshold = float(os.getenv("COST_WARNING_THRESHOLD", "10.0"))  # USD
        
    def validate(self) -> bool:
        """Validate required settings."""
        if not self.fal_api_key:
            raise ValueError("FALAI_API_KEY environment variable is required")
        return True
    
    def get_project_dir(self, project_id: str) -> Path:
        """Get directory path for a specific project."""
        project_dir = self.projects_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
    
    def get_scene_dir(self, project_id: str, scene_id: str) -> Path:
        """Get directory path for a specific scene."""
        scene_dir = self.get_project_dir(project_id) / "scenes" / scene_id
        scene_dir.mkdir(parents=True, exist_ok=True)
        return scene_dir


# Singleton instance
settings = Settings()