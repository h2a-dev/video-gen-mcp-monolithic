"""Cinematic prompt enhancement utilities for professional visual styling."""

from typing import Dict, List, Optional, Tuple
import random


class CinematicPromptEnhancer:
    """Enhance image and video prompts with professional visual techniques."""
    
    # Visual styles by mood
    VISUAL_STYLES = {
        "documentary": [
            "handheld documentary style, raw authentic feel",
            "natural aesthetic, slightly tilted frame, organic movement",
            "natural lighting, handheld movement, observational approach"
        ],
        "cinematic": [
            "cinematic widescreen composition, professional look",
            "film grain aesthetic, shallow depth of field, dramatic lighting",
            "cinematic color grading, movie-quality visuals"
        ],
        "vintage": [
            "medium format aesthetic, film grain, nostalgic mood",
            "vintage film look, warm tones, soft focus",
            "instant film aesthetic, soft focus, dreamy quality"
        ],
        "modern": [
            "high resolution, crystal clear quality, sharp details",
            "modern color science, vibrant and clean aesthetic",
            "HDR quality, professional photography style"
        ],
        "artistic": [
            "light leaks, heavy vignetting, experimental look",
            "double exposure effect, ethereal blend, ghostly overlay",
            "miniature effect, selective focus, artistic interpretation"
        ]
    }
    
    # Shot composition by type
    SHOT_COMPOSITIONS = {
        "wide_establishing": [
            "ultra-wide perspective, dramatic composition",
            "natural wide angle view, minimal distortion",
            "fisheye perspective, 180° view, circular distortion"
        ],
        "portrait": [
            "shallow depth of field, creamy bokeh background",
            "beautiful compression, subject isolation",
            "natural perspective, intimate framing"
        ],
        "detail": [
            "extreme close-up, macro detail",
            "selective focus, miniature effect",
            "compressed perspective, isolated details"
        ],
        "action": [
            "dynamic motion tracking, energetic framing",
            "compressed background, subject emphasis",
            "versatile framing, quick action capture"
        ]
    }
    
    # Camera movements for video
    CAMERA_MOVEMENTS = {
        "dramatic": [
            "slow dolly in, building tension",
            "crane shot rising, revealing scale",
            "360-degree orbit, dynamic perspective"
        ],
        "subtle": [
            "gentle pan left to right, following action",
            "slow zoom in, increasing intimacy",
            "slight handheld movement, organic feel"
        ],
        "energetic": [
            "quick whip pan, energetic transition",
            "handheld tracking shot, following subject",
            "dynamic push in, sudden focus"
        ],
        "smooth": [
            "steadicam glide, floating movement",
            "slider dolly, perfectly horizontal",
            "gimbal stabilized, silky smooth motion"
        ]
    }
    
    # Lighting conditions
    LIGHTING_STYLES = {
        "golden_hour": "golden hour lighting, warm tones, long shadows",
        "blue_hour": "blue hour, twilight glow, ethereal atmosphere",
        "studio": "professional studio lighting, three-point setup, controlled shadows",
        "natural": "natural lighting, soft window light, authentic mood",
        "dramatic": "dramatic chiaroscuro lighting, strong contrast, moody shadows",
        "neon": "neon lighting, cyberpunk aesthetic, color contrast"
    }
    
    @classmethod
    def enhance_image_prompt(
        cls,
        base_prompt: str,
        style: str = "cinematic",
        shot_type: str = "wide_establishing",
        lighting: Optional[str] = None,
        platform: Optional[str] = None
    ) -> str:
        """Enhance an image prompt with cinematic visual details."""
        
        # Select visual style and shot composition
        visual_style = random.choice(cls.VISUAL_STYLES.get(style, cls.VISUAL_STYLES["modern"]))
        composition = random.choice(cls.SHOT_COMPOSITIONS.get(shot_type, cls.SHOT_COMPOSITIONS["wide_establishing"]))
        
        # Add lighting if specified
        lighting_desc = ""
        if lighting:
            lighting_desc = cls.LIGHTING_STYLES.get(lighting, "natural lighting")
        
        # Platform-specific adjustments
        aspect_ratio_hints = {
            "youtube": "16:9 widescreen composition",
            "tiktok": "9:16 vertical framing",
            "instagram": "1:1 square format"
        }
        
        platform_hint = aspect_ratio_hints.get(platform, "")
        
        # Construct enhanced prompt
        enhanced_parts = [
            base_prompt,
            visual_style,
            composition,
            lighting_desc,
            platform_hint,
            "professional quality"
        ]
        
        # Filter out empty parts and join
        enhanced_prompt = ", ".join([part for part in enhanced_parts if part])
        
        return enhanced_prompt
    
    @classmethod
    def enhance_video_motion_prompt(
        cls,
        base_motion: str,
        movement_style: str = "smooth",
        duration: int = 5
    ) -> str:
        """Enhance a video motion prompt with professional movements."""
        
        # Select appropriate camera movement
        movement = random.choice(cls.CAMERA_MOVEMENTS.get(movement_style, cls.CAMERA_MOVEMENTS["smooth"]))
        
        # Add duration-specific guidance
        if duration <= 5:
            speed_hint = "subtle movement"
        else:
            speed_hint = "gradual progression"
        
        # Construct enhanced motion prompt
        enhanced_motion = f"{base_motion}, {movement}, {speed_hint}"
        
        return enhanced_motion
    
    @classmethod
    def get_scene_specific_enhancement(cls, scene_type: str) -> Dict[str, str]:
        """Get visual style recommendations for specific scene types."""
        
        scene_enhancements = {
            "opening": {
                "style": "cinematic",
                "shot": "wide_establishing",
                "movement": "dramatic",
                "lighting": "golden_hour"
            },
            "action": {
                "style": "modern",
                "shot": "action",
                "movement": "energetic",
                "lighting": "natural"
            },
            "emotional": {
                "style": "cinematic",
                "shot": "portrait",
                "movement": "subtle",
                "lighting": "dramatic"
            },
            "detail": {
                "style": "modern",
                "shot": "detail",
                "movement": "smooth",
                "lighting": "studio"
            },
            "closing": {
                "style": "cinematic",
                "shot": "wide_establishing",
                "movement": "smooth",
                "lighting": "blue_hour"
            }
        }
        
        return scene_enhancements.get(scene_type, scene_enhancements["opening"])
    
    @classmethod
    def suggest_visual_setup(cls, description: str) -> Tuple[str, str]:
        """Suggest visual style and composition based on scene description."""
        
        # Keywords to visual style/composition mapping
        keywords_to_setup = {
            # Wide shots
            ("landscape", "establishing", "wide", "panoramic"): ("wide_establishing", "cinematic"),
            # Portraits
            ("portrait", "face", "person", "character"): ("portrait", "cinematic"),
            # Action
            ("action", "motion", "movement", "dynamic"): ("action", "modern"),
            # Details
            ("detail", "close-up", "macro", "texture"): ("detail", "artistic"),
            # Vintage
            ("vintage", "retro", "nostalgic", "old"): ("portrait", "vintage"),
            # Documentary
            ("real", "authentic", "documentary", "raw"): ("wide_establishing", "documentary")
        }
        
        # Check description for keywords
        description_lower = description.lower()
        for keywords, (shot, style) in keywords_to_setup.items():
            if any(keyword in description_lower for keyword in keywords):
                return shot, style
        
        # Default to cinematic wide shot
        return "wide_establishing", "cinematic"


def create_cinematic_image_prompt(
    base_description: str,
    scene_number: int,
    total_scenes: int,
    platform: Optional[str] = None
) -> str:
    """Create a cinematically enhanced image prompt based on scene position."""
    
    # Determine scene type based on position
    if scene_number == 1:
        scene_type = "opening"
    elif scene_number == total_scenes:
        scene_type = "closing"
    elif "detail" in base_description.lower() or "close" in base_description.lower():
        scene_type = "detail"
    elif "action" in base_description.lower() or "motion" in base_description.lower():
        scene_type = "action"
    else:
        scene_type = "emotional"
    
    # Get scene-specific enhancements
    enhancements = CinematicPromptEnhancer.get_scene_specific_enhancement(scene_type)
    
    # Auto-detect best visual setup from description
    shot_type, style = CinematicPromptEnhancer.suggest_visual_setup(base_description)
    
    # Override with scene-specific if available
    shot_type = enhancements.get("shot", shot_type)
    style = enhancements.get("style", style)
    lighting = enhancements.get("lighting", "natural")
    
    # Enhance the prompt
    enhanced_prompt = CinematicPromptEnhancer.enhance_image_prompt(
        base_description,
        style=style,
        shot_type=shot_type,
        lighting=lighting,
        platform=platform
    )
    
    return enhanced_prompt


def create_cinematic_motion_prompt(
    base_motion: str,
    scene_type: str,
    duration: int = 5
) -> str:
    """Create a cinematically enhanced motion prompt."""
    
    # Get scene-specific movement style
    enhancements = CinematicPromptEnhancer.get_scene_specific_enhancement(scene_type)
    movement_style = enhancements.get("movement", "smooth")
    
    # Enhance the motion prompt
    enhanced_motion = CinematicPromptEnhancer.enhance_video_motion_prompt(
        base_motion,
        movement_style=movement_style,
        duration=duration
    )
    
    return enhanced_motion