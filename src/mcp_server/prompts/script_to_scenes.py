"""Script to scenes prompt implementation."""

from ..models import ProjectManager
import re


async def script_to_scenes(project_id: str) -> str:
    """Convert project script into optimized scene breakdown."""
    
    try:
        project = ProjectManager.get_project(project_id)
        
        if not project.script:
            return """# ❌ No Script Found

This project doesn't have a script yet. To add a script:

1. Update your project with a script:
   ```
   # Option 1: Create new project with script
   create_project(title="...", platform="...", script="Your script here")
   
   # Option 2: Use analyze_script tool
   analyze_script("Your script here", target_duration={target}, platform="{platform}")
   ```

2. Or proceed without a script by manually adding scenes:
   ```
   add_scene(project_id="{project_id}", description="Scene description", duration=5)
   ```
""".format(
                target=project.target_duration,
                platform=project.platform,
                project_id=project_id
            )
        
        # Analyze script
        word_count = len(project.script.split())
        sentence_count = len(re.split(r'[.!?]+', project.script))
        
        # Estimate speaking duration (average 150 words per minute)
        estimated_speaking_time = (word_count / 150) * 60
        
        # Calculate scene recommendations
        target_duration = project.target_duration or estimated_speaking_time
        optimal_scenes = _calculate_optimal_scenes(target_duration)
        
        # Parse script into potential scenes
        script_segments = _segment_script(project.script, optimal_scenes)
        
        return f"""# 🎬 Script-to-Scenes Breakdown

## 📊 Script Analysis
- **Word Count**: {word_count} words
- **Estimated Speaking Time**: {estimated_speaking_time:.1f} seconds
- **Target Video Duration**: {target_duration} seconds
- **Platform**: {project.platform}

## 🎯 Scene Planning
Based on your script and target duration, I recommend **{optimal_scenes} scenes**:

### Optimal Scene Structure:
{_generate_scene_structure(target_duration, optimal_scenes)}

## 📝 Script Segmentation
I've analyzed your script and identified these natural break points:

{_format_script_segments(script_segments, target_duration, optimal_scenes)}

## 🎨 Scene Descriptions
Here are visual scene suggestions based on your script:

{_generate_scene_suggestions(script_segments, project.platform)}

## 🚀 Quick Implementation
Copy and run these commands to create all scenes:

```python
# Create all scenes at once
{_generate_scene_commands(script_segments, project_id)}
```

## 💡 Next Steps
After creating scenes:
1. Generate images for each scene with `generate_image_from_text()`
2. Animate them with `generate_video_from_image()`
3. Add voiceover with `generate_speech()` using your script
   Choose from these voices:
   - **Wise_Woman**: Professional, authoritative female voice
   - **Friendly_Person**: Warm, approachable voice
   - **Deep_Voice_Man**: Deep, commanding male voice
   - **Calm_Woman**: Soothing, peaceful female voice
   - **Casual_Guy**: Relaxed, conversational male voice
   - **Inspirational_girl**: Energetic, motivating female voice
   Example: `generate_speech(text=script, voice="Friendly_Person")`
4. Add background music with `generate_music()`
5. Assemble with `assemble_video()`

## 🎯 Pro Tips
- {_get_pacing_tip(target_duration, optimal_scenes)}
- Match scene transitions to natural pauses in your script
- Use visual metaphors to reinforce key points
- Keep the most impactful content in the middle 60% of your video
"""
        
    except Exception as e:
        return f"Error analyzing script: {str(e)}"


def _calculate_optimal_scenes(duration: int) -> int:
    """Calculate optimal number of scenes for duration."""
    if duration <= 15:
        return max(1, duration // 5)
    elif duration <= 30:
        return 3
    elif duration <= 60:
        return duration // 15
    else:
        # For longer videos, aim for scene changes every 15-20 seconds
        return duration // 17


def _segment_script(script: str, target_scenes: int) -> list:
    """Segment script into scenes based on natural breaks."""
    # Split by sentences
    sentences = [s.strip() for s in re.split(r'[.!?]+', script) if s.strip()]
    
    if len(sentences) <= target_scenes:
        # Each sentence becomes a scene
        return sentences
    
    # Group sentences into scenes
    sentences_per_scene = max(1, len(sentences) // target_scenes)
    segments = []
    
    for i in range(0, len(sentences), sentences_per_scene):
        segment = '. '.join(sentences[i:i+sentences_per_scene])
        if segment:
            segments.append(segment + '.')
    
    # Merge last segment if too short
    if len(segments) > target_scenes and len(segments[-1].split()) < 10:
        segments[-2] += ' ' + segments[-1]
        segments.pop()
    
    return segments[:target_scenes]


def _generate_scene_structure(duration: int, scenes: int) -> str:
    """Generate recommended scene duration structure."""
    if scenes == 1:
        return f"- 1 scene: {duration} seconds"
    
    # Calculate mix of 5 and 10 second scenes
    ten_second_scenes = duration // 10
    remaining = duration % 10
    five_second_scenes = 0
    
    if remaining >= 5:
        five_second_scenes = 1
        ten_second_scenes = (duration - 5) // 10
    
    structure = []
    if ten_second_scenes > 0:
        structure.append(f"{ten_second_scenes} × 10-second scenes")
    if five_second_scenes > 0:
        structure.append(f"{five_second_scenes} × 5-second scene")
    
    return "- " + "\n- ".join(structure)


def _format_script_segments(segments: list, duration: int, scenes: int) -> str:
    """Format script segments with timing."""
    if not segments:
        return "No segments identified"
    
    # Calculate duration per segment
    base_duration = duration // len(segments)
    remainder = duration % len(segments)
    
    formatted = []
    current_time = 0
    
    for i, segment in enumerate(segments):
        # Add extra second to early scenes if there's remainder
        scene_duration = base_duration + (1 if i < remainder else 0)
        
        # Prefer 5 or 10 second durations
        if scene_duration > 7:
            scene_duration = 10
        elif scene_duration > 2:
            scene_duration = 5
        
        formatted.append(f"""### Scene {i+1} (0:{current_time:02d} - 0:{current_time+scene_duration:02d})
**Duration**: {scene_duration} seconds
**Script**: "{segment[:100]}{'...' if len(segment) > 100 else ''}"
""")
        current_time += scene_duration
    
    return '\n'.join(formatted)


def _generate_scene_suggestions(segments: list, platform: str) -> str:
    """Generate visual suggestions for each script segment."""
    suggestions = []
    
    for i, segment in enumerate(segments):
        # Extract key concepts from segment
        key_words = [word for word in segment.split() if len(word) > 4][:3]
        
        suggestion = f"""### Scene {i+1} Visual Concept:
**Script excerpt**: "{segment[:60]}..."
**Visual suggestion**: {_create_visual_suggestion(key_words, i, platform)}
**Motion idea**: {_create_motion_suggestion(i, len(segments))}
"""
        suggestions.append(suggestion)
    
    return '\n'.join(suggestions)


def _create_visual_suggestion(key_words: list, scene_index: int, platform: str) -> str:
    """Create visual suggestion based on keywords."""
    # Opening scene
    if scene_index == 0:
        return f"Eye-catching opener featuring {' and '.join(key_words)}, {platform}-optimized composition"
    # Closing scene
    elif scene_index >= 3:
        return f"Conclusive visual with {key_words[0] if key_words else 'summary'}, call-to-action overlay"
    # Middle scenes
    else:
        return f"Illustrative scene showing {' and '.join(key_words[:2])}, dynamic composition"


def _create_motion_suggestion(scene_index: int, total_scenes: int) -> str:
    """Create motion suggestion based on scene position."""
    if scene_index == 0:
        return "Zoom in or fade in for engaging start"
    elif scene_index == total_scenes - 1:
        return "Slow zoom out or fade for closure"
    elif scene_index % 2 == 0:
        return "Subtle pan or drift for visual interest"
    else:
        return "Gentle zoom or parallax effect"


def _generate_scene_commands(segments: list, project_id: str) -> str:
    """Generate add_scene commands for all segments."""
    commands = []
    
    for i, segment in enumerate(segments):
        # Determine duration (prefer 10s for longer segments)
        duration = 10 if len(segment.split()) > 15 else 5
        
        # Create concise description
        description = segment[:50].replace('"', "'") + "..."
        
        command = f'add_scene(project_id="{project_id}", description="{description}", duration={duration})'
        commands.append(command)
    
    return '\n'.join(commands)


def _get_pacing_tip(duration: int, scenes: int) -> str:
    """Get pacing tip based on video length."""
    pace = duration / scenes
    
    if pace < 7:
        return "Fast-paced video - ensure smooth transitions"
    elif pace < 15:
        return "Well-paced video - balance action and breathing room"
    else:
        return "Slower pace - focus on compelling visuals and narrative"