"""Analyze script tool implementation."""

import re
from typing import Dict, Any, Optional, List
from ...config import get_platform_spec


async def analyze_script(
    script: str,
    target_duration: Optional[int] = None,
    platform: Optional[str] = None
) -> Dict[str, Any]:
    """Analyze a script for video production insights."""
    try:
        # Convert target_duration to int if it's passed as string
        if target_duration is not None and isinstance(target_duration, str):
            target_duration = int(target_duration)
        
        # Basic text analysis
        word_count = len(script.split())
        sentence_count = len(re.split(r'[.!?]+', script.strip()))
        char_count = len(script)
        
        # Estimate speaking duration (140 words per minute for more realistic pacing)
        # This accounts for pauses and natural speech rhythm
        estimated_speaking_seconds = (word_count / 140) * 60
        
        # Get platform recommendations if specified
        platform_info = {}
        if platform:
            platform_info = {
                "recommended_duration": get_platform_spec(platform, "recommended_duration"),
                "max_duration": get_platform_spec(platform, "max_duration"),
                "aspect_ratio": get_platform_spec(platform, "default_aspect_ratio")
            }
            
            if not target_duration:
                target_duration = platform_info["recommended_duration"]
        
        # Use target duration or estimate
        if not target_duration:
            target_duration = int(estimated_speaking_seconds)
        
        # Calculate scene recommendations
        scene_analysis = _analyze_scene_requirements(script, target_duration)
        
        # Adjust for frame trimming (0.5 seconds per scene after the first)
        trimmed_duration = 0.5 * (scene_analysis["recommended_scenes"] - 1)
        effective_duration = target_duration - trimmed_duration
        
        # Identify key moments and themes
        key_moments = _extract_key_moments(script)
        themes = _extract_themes(script)
        
        # Generate scene suggestions
        scene_suggestions = _generate_scene_suggestions(
            script, 
            scene_analysis["recommended_scenes"],
            key_moments
        )
        
        # Get voice recommendations
        voice_recommendations = _get_voice_recommendations(script, themes)
        
        return {
            "success": True,
            "analysis": {
                "text_stats": {
                    "word_count": word_count,
                    "sentence_count": sentence_count,
                    "character_count": char_count,
                    "estimated_speaking_seconds": round(estimated_speaking_seconds, 1)
                },
                "duration_analysis": {
                    "target_duration": target_duration,
                    "effective_duration": round(effective_duration, 1),
                    "speaking_duration": round(estimated_speaking_seconds, 1),
                    "trimmed_seconds": round(trimmed_duration, 1),
                    "pacing": _determine_pacing(effective_duration, estimated_speaking_seconds),
                    "recommended_script_duration": round(effective_duration - 1, 1)  # 1 second buffer
                },
                "scene_analysis": scene_analysis,
                "key_moments": key_moments,
                "themes": themes,
                "platform_info": platform_info
            },
            "recommendations": {
                "scene_suggestions": scene_suggestions,
                "production_tips": _get_production_tips(target_duration, estimated_speaking_seconds),
                "cost_estimate": _estimate_production_cost(scene_analysis["recommended_scenes"], target_duration),
                "voice_selection": voice_recommendations
            },
            "next_steps": [
                f"Create project: create_project('Title', '{platform or 'custom'}', script=script, target_duration={target_duration})",
                f"Generate voiceover FIRST: generate_speech(text=script, voice='{voice_recommendations['recommended_voice']}', project_id=project_id)",
                "Add scenes based on timing: Use add_scene() for each visual beat",
                "Batch generate visuals: Use return_queue_id=True for non-blocking generation",
                "Monitor all tasks: get_queue_status(project_id=project_id)",
                "Final assembly: assemble_video() when all generation is complete"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _analyze_scene_requirements(script: str, target_duration: int) -> Dict[str, Any]:
    """Analyze how many scenes are needed."""
    # Split script into logical segments
    sentences = [s.strip() for s in re.split(r'[.!?]+', script) if s.strip()]
    
    # Calculate optimal scenes based on duration
    if target_duration <= 15:
        recommended_scenes = min(3, max(1, target_duration // 5))
    elif target_duration <= 30:
        recommended_scenes = 3
    elif target_duration <= 60:
        recommended_scenes = target_duration // 15
    else:
        recommended_scenes = target_duration // 20
    
    # Adjust based on content density
    if len(sentences) > recommended_scenes * 3:
        recommended_scenes = min(recommended_scenes + 1, target_duration // 5)
    
    # Calculate scene duration mix
    total_10s_scenes = min(recommended_scenes, target_duration // 10)
    remaining_duration = target_duration - (total_10s_scenes * 10)
    total_5s_scenes = remaining_duration // 5
    
    return {
        "recommended_scenes": recommended_scenes,
        "scene_duration_mix": {
            "10_second_scenes": total_10s_scenes,
            "5_second_scenes": total_5s_scenes
        },
        "sentences_per_scene": max(1, len(sentences) // recommended_scenes)
    }


def _extract_key_moments(script: str) -> List[str]:
    """Extract key moments or important points from script."""
    key_moments = []
    
    # Look for emphasis patterns
    emphasis_patterns = [
        r'important[:\s]+(.*?)(?:[.!?]|$)',
        r'remember[:\s]+(.*?)(?:[.!?]|$)',
        r'key point[:\s]+(.*?)(?:[.!?]|$)',
        r'don\'t forget[:\s]+(.*?)(?:[.!?]|$)',
        r'the main[:\s]+(.*?)(?:[.!?]|$)'
    ]
    
    for pattern in emphasis_patterns:
        matches = re.findall(pattern, script.lower())
        key_moments.extend(matches)
    
    # Look for lists or numbered points
    numbered_points = re.findall(r'\d+[\.\)]\s*([^.!?]+)', script)
    key_moments.extend(numbered_points[:5])  # Limit to 5
    
    # Deduplicate and clean
    key_moments = list(set(moment.strip() for moment in key_moments if moment.strip()))[:5]
    
    return key_moments if key_moments else ["Opening statement", "Main point", "Conclusion"]


def _extract_themes(script: str) -> List[str]:
    """Extract main themes or topics from script."""
    # Common words to ignore
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'after',
                  'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had'}
    
    # Extract words
    words = re.findall(r'\b[a-z]+\b', script.lower())
    
    # Count word frequency
    word_freq = {}
    for word in words:
        if word not in stop_words and len(word) > 3:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Get top themes
    themes = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return [theme[0] for theme in themes]


def _generate_scene_suggestions(script: str, num_scenes: int, key_moments: List[str]) -> List[Dict[str, Any]]:
    """Generate specific scene suggestions."""
    sentences = [s.strip() for s in re.split(r'[.!?]+', script) if s.strip()]
    
    suggestions = []
    sentences_per_scene = max(1, len(sentences) // num_scenes)
    
    for i in range(num_scenes):
        start_idx = i * sentences_per_scene
        end_idx = start_idx + sentences_per_scene
        scene_sentences = sentences[start_idx:end_idx]
        
        # Determine scene type
        if i == 0:
            scene_type = "opening"
            visual_style = "attention-grabbing, high impact"
        elif i == num_scenes - 1:
            scene_type = "closing"
            visual_style = "conclusive, call-to-action"
        else:
            scene_type = "body"
            visual_style = "informative, engaging"
        
        # Extract key words from this segment
        segment_text = ' '.join(scene_sentences)
        segment_words = [w for w in segment_text.split() if len(w) > 4][:3]
        
        suggestion = {
            "scene_number": i + 1,
            "type": scene_type,
            "duration": 10 if len(segment_text) > 50 else 5,
            "description": f"Scene showing {', '.join(segment_words)}",
            "visual_style": visual_style,
            "script_excerpt": segment_text[:100] + "..." if len(segment_text) > 100 else segment_text
        }
        
        suggestions.append(suggestion)
    
    return suggestions


def _determine_pacing(target_duration: int, speaking_duration: float) -> str:
    """Determine video pacing based on durations."""
    ratio = speaking_duration / target_duration
    
    if ratio < 0.8:
        return "relaxed - plenty of time for visuals"
    elif ratio < 1.0:
        return "balanced - good mix of speech and visuals"
    elif ratio < 1.2:
        return "brisk - consider trimming script slightly"
    else:
        return "rushed - script may be too long for target duration"


def _get_production_tips(target_duration: int, speaking_duration: float) -> List[str]:
    """Get production tips based on analysis."""
    tips = []
    
    # Calculate effective duration after frame trimming
    # Assuming average of 3-4 scenes for most videos
    avg_scenes = min(4, max(2, target_duration // 15))
    trimmed_duration = 0.5 * (avg_scenes - 1)
    effective_duration = target_duration - trimmed_duration
    
    # ALWAYS recommend voiceover-first workflow for scripts
    tips.append("🎯 GENERATE VOICEOVER FIRST for perfect audio-visual sync")
    
    # Pacing tips
    if speaking_duration > effective_duration:
        tips.append(f"Script is {speaking_duration - effective_duration:.0f}s too long (accounting for transitions) - trim to {effective_duration - 1:.0f}s")
    elif speaking_duration < effective_duration * 0.7:
        tips.append("Add visual sequences or slower pacing to fill time")
    
    tips.append(f"Target script duration: {effective_duration - 1:.0f}s (includes 1s buffer for frame trimming)")
    
    # Duration-based tips
    if target_duration <= 30:
        tips.append("Keep scenes fast-paced and impactful")
        tips.append("Use quick cuts and dynamic transitions")
    elif target_duration <= 60:
        tips.append("Balance quick cuts with moments to breathe")
        tips.append("Use 5-second scenes for transitions")
    else:
        tips.append("Vary scene lengths to maintain interest")
        tips.append("Include establishing shots and b-roll")
    
    return tips


def _estimate_production_cost(num_scenes: int, duration: int) -> Dict[str, float]:
    """Estimate production costs."""
    return {
        "images": round(num_scenes * 0.04, 2),
        "videos": round(duration * 0.05, 2),
        "music": 0.10 if duration > 15 else 0,
        "speech": 0.10,  # Rough estimate
        "total_estimate": round(
            (num_scenes * 0.04) + 
            (duration * 0.05) + 
            (0.10 if duration > 15 else 0) + 
            0.10, 
            2
        )
    }


def _get_voice_recommendations(script: str, themes: List[str]) -> Dict[str, Any]:
    """Recommend voices based on script content and themes."""
    script_lower = script.lower()
    
    # Analyze tone
    professional_words = ['business', 'professional', 'corporate', 'executive', 'management']
    friendly_words = ['welcome', 'friends', 'community', 'together', 'share']
    inspirational_words = ['inspire', 'achieve', 'dream', 'success', 'motivation']
    calming_words = ['peace', 'relax', 'calm', 'meditation', 'gentle']
    
    # Count tone indicators
    tone_scores = {
        'professional': sum(1 for word in professional_words if word in script_lower),
        'friendly': sum(1 for word in friendly_words if word in script_lower),
        'inspirational': sum(1 for word in inspirational_words if word in script_lower),
        'calming': sum(1 for word in calming_words if word in script_lower)
    }
    
    # Determine primary tone
    primary_tone = max(tone_scores.items(), key=lambda x: x[1])[0] if any(tone_scores.values()) else 'neutral'
    
    # Map tones to voice recommendations
    voice_recommendations = {
        'professional': {
            'primary': 'Wise_Woman',
            'alternative': 'Deep_Voice_Man',
            'reason': 'Professional and authoritative tone detected'
        },
        'friendly': {
            'primary': 'Friendly_Person',
            'alternative': 'Casual_Guy',
            'reason': 'Warm and approachable content'
        },
        'inspirational': {
            'primary': 'Inspirational_girl',
            'alternative': 'Determined_Man',
            'reason': 'Motivational and uplifting message'
        },
        'calming': {
            'primary': 'Calm_Woman',
            'alternative': 'Patient_Man',
            'reason': 'Soothing and peaceful content'
        },
        'neutral': {
            'primary': 'Friendly_Person',
            'alternative': 'Wise_Woman',
            'reason': 'Versatile voice for general content'
        }
    }
    
    recommendation = voice_recommendations.get(primary_tone, voice_recommendations['neutral'])
    
    return {
        'recommended_voice': recommendation['primary'],
        'alternative_voice': recommendation['alternative'],
        'tone_analysis': primary_tone,
        'reason': recommendation['reason'],
        'all_voices': [
            {'id': 'Wise_Woman', 'description': 'Professional, authoritative female'},
            {'id': 'Friendly_Person', 'description': 'Warm, approachable'},
            {'id': 'Deep_Voice_Man', 'description': 'Deep, commanding male'},
            {'id': 'Calm_Woman', 'description': 'Soothing, peaceful female'},
            {'id': 'Casual_Guy', 'description': 'Relaxed, conversational male'},
            {'id': 'Inspirational_girl', 'description': 'Energetic, motivating female'},
            {'id': 'Patient_Man', 'description': 'Understanding, gentle male'},
            {'id': 'Determined_Man', 'description': 'Strong, confident male'}
        ],
        'usage_example': f'generate_speech(text=script, voice="{recommendation["primary"]}")'  
    }