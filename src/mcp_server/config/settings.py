"""Configuration settings for the Video Agent MCP server."""

import os
import platform
import shutil
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
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        
        # Storage paths
        self.base_dir = Path(__file__).parent.parent.parent.parent
        self.storage_dir = Path(os.getenv("VIDEO_AGENT_STORAGE", str(self.base_dir / "storage")))
        self.temp_dir = self.storage_dir / "temp"
        self.projects_dir = self.storage_dir / "projects"
        self.templates_dir = self.base_dir / "templates"
        self.assets_dir = self.storage_dir / "assets"
        self.logos_dir = self.assets_dir / "logos"
        
        # Ensure directories exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.logos_dir.mkdir(parents=True, exist_ok=True)
        
        # API limits and defaults
        self.max_parallel_downloads = int(os.getenv("MAX_PARALLEL_DOWNLOADS", "5"))
        self.download_timeout = int(os.getenv("DOWNLOAD_TIMEOUT", "300"))  # seconds
        self.generation_timeout = int(os.getenv("GENERATION_TIMEOUT", "600"))  # seconds
        
        # Default generation parameters
        self.default_image_model = os.getenv("DEFAULT_IMAGE_MODEL", "imagen4")
        self.default_video_model = os.getenv("DEFAULT_VIDEO_MODEL", "kling_2.1")
        self.default_music_model = os.getenv("DEFAULT_MUSIC_MODEL", "lyria2")
        self.default_speech_model = os.getenv("DEFAULT_SPEECH_MODEL", "minimax")
        
        # Video assembly settings
        self.ffmpeg_path = self._get_ffmpeg_path()
        self.default_video_codec = os.getenv("DEFAULT_VIDEO_CODEC", "libx264")
        self.default_audio_codec = os.getenv("DEFAULT_AUDIO_CODEC", "aac")
        self.default_output_format = os.getenv("DEFAULT_OUTPUT_FORMAT", "mp4")
        
        # Logo overlay settings
        self.default_logo_path = self.logos_dir / "h2a.png"
        self.default_logo_position = os.getenv("DEFAULT_LOGO_POSITION", "bottom_right")
        self.default_logo_padding = int(os.getenv("DEFAULT_LOGO_PADDING", "10"))
        
        # End video settings
        self.default_end_video = "h2a_end.mp4"
        self.default_end_video_path = self.logos_dir / self.default_end_video
        
        # Cost tracking
        self.enable_cost_tracking = os.getenv("ENABLE_COST_TRACKING", "true").lower() == "true"
        self.cost_warning_threshold = float(os.getenv("COST_WARNING_THRESHOLD", "10.0"))  # USD
        
    def validate(self) -> bool:
        """Validate required settings."""
        if not self.fal_api_key:
            raise ValueError("FALAI_API_KEY environment variable is required")
        # YouTube API key is optional - only warn if not present
        if not self.youtube_api_key:
            import logging
            logging.warning("YOUTUBE_API_KEY or GOOGLE_API_KEY not set - YouTube search features will not work")
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
    
    def _get_ffmpeg_path(self) -> str:
        """Get the appropriate ffmpeg executable path for the current platform."""
        # First check if user has set a custom path
        custom_path = os.getenv("FFMPEG_PATH")
        if custom_path:
            return custom_path
        
        # Determine the executable name based on platform
        if platform.system() == "Windows":
            ffmpeg_name = "ffmpeg.exe"
        else:
            ffmpeg_name = "ffmpeg"
        
        # Check if ffmpeg is in PATH
        ffmpeg_in_path = shutil.which(ffmpeg_name)
        if ffmpeg_in_path:
            return ffmpeg_in_path
        
        # Return the default name and let FFmpegWrapper handle the error
        return ffmpeg_name


# Singleton instance
settings = Settings()