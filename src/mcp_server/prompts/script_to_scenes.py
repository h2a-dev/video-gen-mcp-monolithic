"""Script to scenes prompt implementation."""

from ..models import ProjectManager
import re


async def script_to_scenes(script: str, target_duration: int, style: str = "dynamic") -> list:
    """Convert a script into detailed scene breakdowns."""
    
    # Analyze script structure
    sentences = re.split(r'[.!?]+', script)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Calculate timing
    words_per_second = 2.5  # Average speaking rate
    total_words = len(script.split())
    estimated_duration = total_words / words_per_second
    
    # Scene duration recommendations
    if style == "dynamic":
        scene_length = 5  # Quick cuts
    elif style == "cinematic":
        scene_length = 10  # Longer takes
    else:  # minimal
        scene_length = 7  # Medium pacing
    
    # Calculate number of scenes
    num_scenes = max(3, min(12, target_duration // scene_length))
    
    content = f"""# 🎬 Script-to-Scenes Breakdown

## 📝 Script Analysis
- **Total words**: {total_words}
- **Estimated narration time**: {estimated_duration:.1f} seconds
- **Target duration**: {target_duration} seconds
- **Style**: {style}
- **Recommended scenes**: {num_scenes}

## 🎯 Scene Breakdown Strategy

### Timing Considerations
- **Scene length**: {scene_length} seconds each
- **Total scenes**: {num_scenes}
- **Pacing**: {'Fast cuts for energy' if style == 'dynamic' else 'Longer takes for impact' if style == 'cinematic' else 'Balanced pacing'}

### Scene Distribution
"""
    
    # Distribute script across scenes
    sentences_per_scene = max(1, len(sentences) // num_scenes)
    
    scene_suggestions = []
    for i in range(num_scenes):
        start_idx = i * sentences_per_scene
        end_idx = start_idx + sentences_per_scene if i < num_scenes - 1 else len(sentences)
        scene_text = ' '.join(sentences[start_idx:end_idx])
        
        if scene_text:
            scene_suggestions.append({
                "scene": i + 1,
                "duration": scene_length,
                "text": scene_text[:150] + "..." if len(scene_text) > 150 else scene_text,
                "timing": f"{i * scene_length}-{(i + 1) * scene_length}s"
            })
    
    # Add scene details to content
    for scene in scene_suggestions:
        content += f"""
#### Scene {scene['scene']} ({scene['timing']})
- **Duration**: {scene['duration']} seconds
- **Content**: "{scene['text']}"
- **Visual suggestion**: {_get_visual_suggestion(scene['text'], style)}
"""
    
    content += f"""
## 🎥 Production Workflow

### Step 1: Create Project
```
project = create_project(
    title="Your Video Title",
    platform="youtube",  # or your target platform
    script=\"\"\"{script[:200]}...\"\"\"",
    target_duration={target_duration}
)
```

### Step 2: Add Scenes
"""
    
    # Add scene creation commands
    for i, scene in enumerate(scene_suggestions):
        content += f"""
```
# Scene {scene['scene']}
add_scene(
    project_id=project['project']['id'],
    description="{_get_scene_description(scene['text'], style)}",
    duration={scene['duration']}
)
```
"""
    
    content += """
### Step 3: Generate Voiceover (if narrated)
```
generate_speech(
    text=script,
    voice="Friendly_Person",  # or choose appropriate voice
    project_id=project['project']['id']
)
```

### Step 4: Generate Visuals
For each scene, generate images that match the narration:
```
# For each scene
generate_image_from_text(
    prompt="[scene-specific visual description]",
    model="imagen4",
    aspect_ratio="16:9",
    style_modifiers=["cinematic"],
    project_id=project['project']['id'],
    scene_id=scene_id
)
```

### Step 5: Animate Images
```
generate_video_from_image(
    image_url=image_url,
    motion_prompt="[appropriate motion for scene]",
    duration=scene_duration,
    project_id=project['project']['id'],
    scene_id=scene_id
)
```

### Step 6: Add Music (optional)
```
generate_music(
    prompt="[mood-appropriate music description]",
    project_id=project['project']['id']
)
```

### Step 7: Final Assembly
```
assemble_video(project_id=project['project']['id'])
```

## 💡 Style-Specific Tips

"""
    
    if style == "dynamic":
        content += """### Dynamic Style
- Use quick cuts between scenes
- Add energetic motion to each clip
- Consider upbeat music
- Emphasize visual variety"""
    elif style == "cinematic":
        content += """### Cinematic Style
- Use slower, deliberate camera movements
- Focus on composition and lighting
- Add dramatic pauses between scenes
- Consider orchestral or ambient music"""
    else:
        content += """### Minimal Style
- Keep visuals simple and clean
- Use subtle movements
- Focus on the message
- Consider minimal or no music"""
    
    content += """

## 🎯 Ready to Create?
This breakdown provides a structured approach to convert your script into a compelling video. Adjust the scenes and timing as needed for your specific content!
"""
    
    # Return in FastMCP 2.0 format
    return [{"role": "assistant", "content": content}]


def _get_visual_suggestion(text: str, style: str) -> str:
    """Generate visual suggestion based on text content and style."""
    text_lower = text.lower()
    
    if style == "dynamic":
        if any(word in text_lower for word in ["action", "move", "run", "jump"]):
            return "Fast-paced action shot with motion blur"
        elif any(word in text_lower for word in ["talk", "say", "speak"]):
            return "Close-up with dynamic background"
        else:
            return "Vibrant scene with movement"
    elif style == "cinematic":
        if any(word in text_lower for word in ["landscape", "view", "scene"]):
            return "Wide establishing shot with depth"
        elif any(word in text_lower for word in ["emotion", "feel", "heart"]):
            return "Intimate close-up with soft lighting"
        else:
            return "Composed shot with cinematic framing"
    else:
        return "Clean, focused composition"


def _get_scene_description(text: str, style: str) -> str:
    """Generate scene description for image generation."""
    base_description = text[:100].strip()
    
    if style == "dynamic":
        return f"Dynamic scene: {base_description}, vibrant colors, energetic composition"
    elif style == "cinematic":
        return f"Cinematic scene: {base_description}, dramatic lighting, professional composition"
    else:
        return f"Minimal scene: {base_description}, clean aesthetic, focused subject"