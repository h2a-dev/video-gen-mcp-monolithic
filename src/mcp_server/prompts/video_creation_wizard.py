"""Video creation wizard prompt implementation."""

from ..config import get_platform_spec
from ..models import ProjectManager


async def video_creation_wizard(platform: str, topic: str) -> str:
    """Interactive wizard for complete video creation."""
    
    # Get platform specifications
    aspect_ratio = get_platform_spec(platform, "default_aspect_ratio") or "16:9"
    max_duration = get_platform_spec(platform, "max_duration") or 600
    recommended_duration = get_platform_spec(platform, "recommended_duration") or 30
    recommendations = get_platform_spec(platform, "recommendations") or {}
    
    # Format duration displays
    def format_duration(seconds):
        if seconds < 60:
            return f"{seconds} seconds"
        else:
            return f"{seconds//60} minutes"
    
    return f"""# 🎬 Video Creation Wizard: {platform.replace('_', ' ').title()} - "{topic}"

Welcome! I'll guide you through creating an engaging {platform.replace('_', ' ')} video about {topic}.

## 📋 Platform Requirements for {platform.replace('_', ' ').title()}
- **Aspect Ratio**: {aspect_ratio}
- **Recommended Duration**: {format_duration(recommended_duration)}
- **Maximum Duration**: {format_duration(max_duration)}
- **Resolution**: {recommendations.get('resolution', '1920x1080')}
- **Frame Rate**: {recommendations.get('frame_rate', 30)} fps

## 🚀 Let's Get Started!

### Step 1: Create Your Project
I'll create a project optimized for {platform}:

```
create_project(
    title="{topic.replace(' ', '_')}_video",
    platform="{platform}",
    target_duration={recommended_duration}
)
```

### Step 2: Develop Your Script
For a {format_duration(recommended_duration)} video about {topic}, you'll need:
- **Opening Hook** (0-5 seconds): Grab attention immediately
- **Main Content** ({5 if recommended_duration <= 30 else 10}-{recommended_duration-5} seconds): Core message
- **Call to Action** (final 5 seconds): What should viewers do next?

Would you like me to:
1. Generate a script for you about {topic}
2. Analyze your existing script
3. Skip to scene planning

### Step 3: Scene Planning
Based on {recommended_duration} seconds, I recommend:
- **Number of Scenes**: {recommended_duration // 10 + (1 if recommended_duration % 10 >= 5 else 0)}
- **Scene Duration Mix**: {_get_scene_duration_recommendation(recommended_duration)}

### Step 4: Asset Generation Strategy

#### For Videos WITH Voiceover (Recommended Workflow):
1. **Generate voiceover FIRST** to establish timing:
   ```
   generate_speech(text=script, voice="Friendly_Person")
   ```
   Available voices:
   - **Wise_Woman**: Professional, authoritative
   - **Friendly_Person**: Warm, approachable 
   - **Deep_Voice_Man**: Deep, commanding
   - **Calm_Woman**: Soothing, peaceful
   - **Inspirational_girl**: Energetic, motivating

2. **Plan scenes based on voiceover timing** - ensures perfect sync
3. **Generate images** that match narration beats
   - 🎥 **TIP**: Use `cinematic_photography_guide()` for professional visuals!
4. **Animate images** with motion that complements the audio
5. **Add background music** at lower volume

#### For Videos WITHOUT Voiceover:
1. Generate images for visual storytelling
2. Animate with dynamic motion
3. Add music as the primary audio

#### Working with Existing Images:
If you have reference images or want to use local files:
1. **Local files are auto-uploaded**: Just provide the path
   ```
   generate_video_from_image("/path/to/image.jpg", "slow zoom in")
   ```
2. **Transform existing images**: Use generate_image_from_image
   ```
   generate_image_from_image("/path/to/image.jpg", "add cinematic lighting")
   ```
3. **URLs work directly**: No upload needed for web images

### Step 5: Production Workflow

#### Voiceover-First Workflow (RECOMMENDED for narrated videos):
1. **Generate voiceover** from your script first
2. **Analyze voiceover duration** to plan scene timing
3. **Create scenes** that match voiceover pacing
4. **Generate images** aligned with narration
5. **Animate images** to complement speech rhythm
6. **Add background music** if needed
7. **Assemble** with perfect audio-visual sync

#### Visual-First Workflow (for non-narrated videos):
1. **Create scenes** with visual descriptions
2. **Generate ALL images at once** (parallel generation!)
3. **Animate ALL images at once** (5x faster!)
4. **Generate music** that matches the mood
5. **Assemble** into final video

### 🚀 CRITICAL: Use Parallel Generation!
**Always generate multiple assets in ONE message for maximum speed:**
```
# Generate all scene images at once:
generate_image_from_text("scene 1", project_id=pid, scene_id=s1)
generate_image_from_text("scene 2", project_id=pid, scene_id=s2)
generate_image_from_text("scene 3", project_id=pid, scene_id=s3)

# Then animate all videos at once:
generate_video_from_image(img1, "zoom in", project_id=pid, scene_id=s1)
generate_video_from_image(img2, "pan left", project_id=pid, scene_id=s2)
generate_video_from_image(img3, "zoom out", project_id=pid, scene_id=s3)
```

## 💡 Platform-Specific Tips for {platform.replace('_', ' ').title()}
{_get_platform_specific_tips(platform)}

## 💰 Estimated Budget
For a {format_duration(recommended_duration)} video:
- Images: ~${0.04 * (recommended_duration // 10 + 1):.2f}
- Video generation: ~${0.05 * recommended_duration:.2f}
- Music (if needed): ~$0.10
- Voiceover (per 1000 chars): ~$0.10
- **Total estimate**: ~${_estimate_total_cost(recommended_duration):.2f}

## 🎯 Ready to Start?
Let's begin by creating your project! Once created, I'll help you:
- Plan engaging scenes
- Generate stunning visuals
- Create smooth animations
- Add professional audio
- Export in the perfect format

Just say "Let's start!" and I'll create your project and guide you through each step.
"""


def _get_scene_duration_recommendation(total_duration: int) -> str:
    """Get scene duration mix recommendation."""
    if total_duration <= 30:
        return "Use 5-second scenes for quick, punchy content"
    elif total_duration <= 60:
        return "Mix of 5-second and 10-second scenes (start fast, then slow down)"
    else:
        return "Primarily 10-second scenes with some 5-second transitions"


def _get_platform_specific_tips(platform: str) -> str:
    """Get platform-specific content tips."""
    tips = {
        "youtube": """- Use an engaging thumbnail (I can generate one separately)
- Include chapters in your description
- Hook viewers in the first 10 seconds
- End with subscribe reminder and next video suggestion""",
        
        "youtube_shorts": """- No intro needed - start with the action
- Use bold text overlays for key points
- Ensure content loops naturally
- Vertical format is essential""",
        
        "tiktok": """- Jump straight into the content
- Use trending sounds when possible
- Add captions for accessibility
- Quick cuts keep attention""",
        
        "instagram_reel": """- First frame should be visually striking
- Use Instagram's native features in mind
- Keep text short and readable
- Save best moment for the end""",
        
        "twitter": """- Assume autoplay without sound
- Front-load the most important content
- Keep it concise and impactful
- Include captions always""",
        
        "linkedin": """- Professional tone and appearance
- Educational or inspirational content works best
- Include your professional context
- End with a discussion prompt"""
    }
    
    return tips.get(platform, """- Focus on clear messaging
- Ensure good pacing
- Use high-quality visuals
- Include captions for accessibility""")


def _estimate_total_cost(duration: int) -> float:
    """Rough cost estimate for a video."""
    scenes = duration // 10 + (1 if duration % 10 >= 5 else 0)
    image_cost = scenes * 0.04
    video_cost = duration * 0.05
    audio_cost = 0.10 if duration > 15 else 0  # Assume music for longer videos
    speech_cost = 0.10  # Assume some narration
    
    return image_cost + video_cost + audio_cost + speech_cost