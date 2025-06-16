"""Service pricing configuration for cost tracking."""

from typing import Dict, Any


# Pricing per service in USD
PRICING: Dict[str, Dict[str, float]] = {
    # Image generation services
    "imagen4": {
        "per_image": 0.04,
        "description": "Google Imagen 4 - Text to image"
    },
    "flux_pro": {
        "per_image": 0.04,
        "description": "FLUX Pro - Text to image"
    },
    "flux_kontext": {
        "per_image": 0.04,
        "description": "FLUX Pro Kontext - Image to image editing"
    },
    "flux_kontext_multi": {
        "per_image": 0.04,
        "description": "FLUX Pro Kontext Multi - Multiple images to image"
    },
    
    # Video generation services
    "kling_2.1": {
        "per_second": 0.05,
        "description": "Kling 2.1 - Image to video"
    },
    "kling_1.6_elements": {
        "per_second": 0.045,
        "description": "Kling 1.6 Elements - Multiple images to video"
    },
    
    # Audio generation services
    "lyria2": {
        "per_30_seconds": 0.1,
        "description": "Lyria 2 - Text to music"
    },
    "minimax_speech": {
        "per_1000_chars": 0.1,
        "description": "MiniMax - Text to speech"
    }
}


def calculate_image_cost(model: str, count: int = 1) -> float:
    """Calculate cost for image generation."""
    if model not in PRICING:
        raise ValueError(f"Unknown model: {model}")
    return PRICING[model]["per_image"] * count


def calculate_video_cost(model: str, duration_seconds: int) -> float:
    """Calculate cost for video generation."""
    if model not in PRICING:
        raise ValueError(f"Unknown model: {model}")
    return PRICING[model]["per_second"] * duration_seconds


def calculate_music_cost(duration_seconds: int) -> float:
    """Calculate cost for music generation."""
    # Lyria2 charges per 30 seconds
    chunks = (duration_seconds + 29) // 30  # Round up to nearest 30s chunk
    return PRICING["lyria2"]["per_30_seconds"] * chunks


def calculate_speech_cost(text: str) -> float:
    """Calculate cost for text-to-speech."""
    char_count = len(text)
    # MiniMax charges per 1000 characters
    chunks = (char_count + 999) // 1000  # Round up to nearest 1000 chars
    return PRICING["minimax_speech"]["per_1000_chars"] * chunks


def estimate_project_cost(
    image_count: int = 0,
    video_seconds: int = 0,
    music_seconds: int = 0,
    speech_chars: int = 0,
    image_model: str = "imagen4",
    video_model: str = "kling_2.1"
) -> Dict[str, Any]:
    """Estimate total project cost."""
    breakdown = {}
    total = 0.0
    
    if image_count > 0:
        cost = calculate_image_cost(image_model, image_count)
        breakdown["images"] = {
            "count": image_count,
            "model": image_model,
            "cost": cost
        }
        total += cost
    
    if video_seconds > 0:
        cost = calculate_video_cost(video_model, video_seconds)
        breakdown["video"] = {
            "duration_seconds": video_seconds,
            "model": video_model,
            "cost": cost
        }
        total += cost
    
    if music_seconds > 0:
        cost = calculate_music_cost(music_seconds)
        breakdown["music"] = {
            "duration_seconds": music_seconds,
            "model": "lyria2",
            "cost": cost
        }
        total += cost
    
    if speech_chars > 0:
        cost = calculate_speech_cost(speech_chars)
        breakdown["speech"] = {
            "character_count": speech_chars,
            "model": "minimax_speech",
            "cost": cost
        }
        total += cost
    
    return {
        "breakdown": breakdown,
        "total": round(total, 3)
    }