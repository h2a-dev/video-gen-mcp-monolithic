"""Suggest scenes tool implementation."""

from typing import Dict, Any, List
import re
from ...models import ProjectManager


async def suggest_scenes(
    project_id: str,
    style: str = "dynamic"
) -> Dict[str, Any]:
    """Generate scene suggestions based on project script."""
    try:
        project = ProjectManager.get_project(project_id)
        
        if not project.script:
            return {
                "success": False,
                "error": "Project has no script. Add a script first or use analyze_script()."
            }
        
        # Analyze existing scenes
        existing_scenes = len(project.scenes)
        remaining_duration = (project.target_duration or 30) - project.calculate_duration()
        
        if remaining_duration <= 0:
            return {
                "success": True,
                "message": "Project already meets or exceeds target duration",
                "current_duration": project.calculate_duration(),
                "target_duration": project.target_duration,
                "existing_scenes": existing_scenes
            }
        
        # Generate suggestions based on style
        suggestions = _generate_style_based_suggestions(
            project.script,
            style,
            remaining_duration,
            project.platform,
            existing_scenes
        )
        
        # Create scene commands
        scene_commands = _create_scene_commands(suggestions, project_id)
        
        return {
            "success": True,
            "analysis": {
                "existing_scenes": existing_scenes,
                "current_duration": project.calculate_duration(),
                "remaining_duration": remaining_duration,
                "style": style
            },
            "suggestions": suggestions,
            "quick_add_commands": scene_commands,
            "style_descriptions": {
                "dynamic": "Fast-paced with varied shots and movements",
                "minimal": "Clean, focused shots with subtle movements",
                "cinematic": "Dramatic, film-like compositions and transitions",
                "documentary": "Realistic, observational style",
                "energetic": "High energy with quick cuts and bold visuals"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _generate_style_based_suggestions(
    script: str,
    style: str,
    remaining_duration: int,
    platform: str,
    start_index: int
) -> List[Dict[str, Any]]:
    """Generate scene suggestions based on visual style."""
    
    # Style-specific visual approaches
    style_guides = {
        "dynamic": {
            "transitions": ["quick cut", "whip pan", "zoom transition"],
            "movements": ["fast zoom", "dynamic pan", "energetic movement"],
            "compositions": ["bold angles", "close-ups", "action shots"]
        },
        "minimal": {
            "transitions": ["fade", "simple cut", "dissolve"],
            "movements": ["slow drift", "subtle zoom", "gentle pan"],
            "compositions": ["centered", "negative space", "symmetrical"]
        },
        "cinematic": {
            "transitions": ["cinematic fade", "match cut", "L-cut"],
            "movements": ["dolly shot", "crane movement", "parallax"],
            "compositions": ["rule of thirds", "depth of field", "wide shots"]
        },
        "documentary": {
            "transitions": ["straight cut", "natural transition", "time-lapse"],
            "movements": ["handheld feel", "observational pan", "follow shot"],
            "compositions": ["candid framing", "environmental shots", "detail shots"]
        },
        "energetic": {
            "transitions": ["glitch cut", "flash transition", "spin transition"],
            "movements": ["rapid zoom", "shake effect", "rotating motion"],
            "compositions": ["tilted angles", "extreme close-ups", "split screens"]
        }
    }
    
    guide = style_guides.get(style, style_guides["dynamic"])
    
    # Extract key concepts from script
    sentences = [s.strip() for s in re.split(r'[.!?]+', script) if s.strip()]
    
    # Calculate how many scenes we can add
    max_new_scenes = remaining_duration // 5  # Minimum 5 seconds per scene
    
    suggestions = []
    for i in range(min(max_new_scenes, 5)):  # Limit to 5 suggestions
        scene_index = start_index + i
        
        # Get relevant script portion
        script_portion = sentences[i % len(sentences)] if sentences else "General content"
        
        # Extract key visual elements
        key_words = [w for w in script_portion.split() if len(w) > 4][:3]
        
        # Determine scene duration
        duration = 10 if remaining_duration >= 10 and i < 2 else 5
        
        suggestion = {
            "scene_number": scene_index + 1,
            "duration": duration,
            "description": _create_scene_description(key_words, style, platform),
            "visual_style": f"{style} style with {guide['compositions'][i % len(guide['compositions'])]}",
            "motion": guide['movements'][i % len(guide['movements'])],
            "transition": guide['transitions'][i % len(guide['transitions'])],
            "script_reference": script_portion[:80] + "..." if len(script_portion) > 80 else script_portion
        }
        
        suggestions.append(suggestion)
        remaining_duration -= duration
        
        if remaining_duration < 5:
            break
    
    return suggestions


def _create_scene_description(key_words: List[str], style: str, platform: str) -> str:
    """Create scene description based on keywords and style."""
    
    # Platform-specific adjustments
    platform_modifiers = {
        "tiktok": "vertical, mobile-optimized",
        "youtube_shorts": "vertical, attention-grabbing",
        "instagram_reel": "visually striking, instagram-worthy",
        "youtube": "high-quality, professional",
        "linkedin": "professional, business-focused"
    }
    
    platform_mod = platform_modifiers.get(platform, "optimized")
    
    # Style-specific descriptors
    style_descriptors = {
        "dynamic": "energetic and impactful",
        "minimal": "clean and focused",
        "cinematic": "dramatic and atmospheric",
        "documentary": "authentic and realistic",
        "energetic": "vibrant and exciting"
    }
    
    descriptor = style_descriptors.get(style, "engaging")
    
    if key_words:
        return f"{descriptor} {platform_mod} scene featuring {', '.join(key_words[:2])}"
    else:
        return f"{descriptor} {platform_mod} visual composition"


def _create_scene_commands(suggestions: List[Dict[str, Any]], project_id: str) -> List[str]:
    """Create add_scene commands for all suggestions."""
    commands = []
    
    for suggestion in suggestions:
        # Clean description for command
        description = suggestion['description'].replace('"', "'")
        
        command = f'add_scene(project_id="{project_id}", description="{description}", duration={suggestion["duration"]})'
        commands.append(command)
    
    return commands