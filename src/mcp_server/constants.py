"""Constants and configuration for video generation service."""

# Video model configurations
VIDEO_MODELS = {
    "kling_2.1": {
        "valid_durations": [5, 10],
        "cost_per_second": 0.05,
        "supports": ["negative_prompt", "cfg_scale"],
        "fal_model_id": "fal-ai/kling-video/v2.1/master/image-to-video",
        "default_negative_prompt": "blur, distort, and low quality",
        "default_cfg_scale": 0.5,
        "min_cfg_scale": 0.0,
        "max_cfg_scale": 1.0
    },
    "hailuo_02": {
        "valid_durations": [6, 10],
        "cost_per_second": 0.045,  # 10% cheaper than kling
        "supports": ["prompt_optimizer"],
        "fal_model_id": "fal-ai/minimax/hailuo-02/standard/image-to-video",
        "default_prompt_optimizer": True
    }
}

# Image model configurations
IMAGE_MODELS = {
    "imagen4": {
        "cost_per_image": 0.06,
        "fal_model_id": "fal-ai/imagen4/preview/ultra",
        "supports_aspect_ratios": True
    },
    "flux_pro": {
        "cost_per_image": 0.04,
        "fal_model_id": "fal-ai/flux-pro",
        "supports_aspect_ratios": True
    },
    "flux_kontext": {
        "cost_per_image": 0.04,
        "fal_model_id": "fal-ai/flux-pro/kontext",
        "fixed_guidance_scale": 3.5,
        "default_safety_tolerance": "3"
    }
}

# Audio model configurations
AUDIO_MODELS = {
    "lyria2": {
        "cost_per_generation": 0.10,
        "fal_model_id": "fal-ai/lyria2",
        "typical_duration": 95  # seconds
    },
    "minimax_speech": {
        "cost_per_1000_chars": 0.10,
        "fal_model_id": "fal-ai/minimax/speech-02-hd",
        "supports_voices": True
    }
}

# Valid aspect ratios
ASPECT_RATIOS = {
    "16:9": "Widescreen (YouTube, monitors)",
    "9:16": "Vertical (TikTok, Reels, mobile)",
    "1:1": "Square (Instagram posts)",
    "4:5": "Portrait (Instagram posts)"
}

# Platform configurations
PLATFORM_CONFIGS = {
    "youtube": {
        "default_aspect_ratio": "16:9",
        "recommended_duration": 300,  # 5 minutes
        "max_duration": None
    },
    "youtube_shorts": {
        "default_aspect_ratio": "9:16",
        "recommended_duration": 60,
        "max_duration": 60
    },
    "tiktok": {
        "default_aspect_ratio": "9:16",
        "recommended_duration": 30,
        "max_duration": 180  # 3 minutes
    },
    "instagram_reel": {
        "default_aspect_ratio": "9:16",
        "recommended_duration": 30,
        "max_duration": 90
    },
    "instagram_post": {
        "default_aspect_ratio": "1:1",
        "recommended_duration": 60,
        "max_duration": 60
    },
    "linkedin": {
        "default_aspect_ratio": "16:9",
        "recommended_duration": 120,
        "max_duration": 600  # 10 minutes
    }
}

# Voice configurations
VOICE_OPTIONS = {
    "Wise_Woman": "Professional and knowledgeable",
    "Friendly_Person": "Warm and approachable",
    "Deep_Voice_Man": "Commanding and authoritative",
    "Calm_Woman": "Soothing and peaceful",
    "Casual_Guy": "Relaxed and conversational",
    "Inspirational_girl": "Energetic and motivating",
    "Patient_Man": "Gentle and understanding",
    "Determined_Man": "Confident and assertive"
}

# Error retry configurations
RETRY_CONFIG = {
    "max_attempts": 3,
    "initial_delay": 2.0,
    "max_delay": 60.0,
    "exponential_base": 2.0,
    "jitter": True,
    "retryable_errors": [
        "rate limit",
        "too many requests",
        "503",
        "502",
        "timeout",
        "connection"
    ]
}

# Request timeout configurations (in seconds)
TIMEOUT_CONFIG = {
    "default": 120,
    "image_generation": 60,
    "video_generation_5s": 180,
    "video_generation_10s": 300,
    "music_generation": 120,
    "speech_generation": 60,
    "file_upload": 30,
    "connection": 5
}

# File size limits (in MB)
FILE_SIZE_LIMITS = {
    "image_upload": 10,
    "video_upload": 100,
    "audio_upload": 50
}

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
    "video": [".mp4", ".mov", ".avi", ".webm", ".mkv"],
    "audio": [".mp3", ".wav", ".m4a", ".aac", ".ogg"]
}