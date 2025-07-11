"""Video creation wizard prompt implementation."""

from ..config import get_platform_spec
from ..models import ProjectManager


async def video_creation_wizard(platform: str, topic: str) -> list:
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
    
    content = f"""# 🎬 Video Creation Wizard: {platform.replace('_', ' ').title()} - "{topic}"

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

🔍 **If user provides a reference image**: 
- First use Read tool to analyze and understand the image content
- Identify if it contains a character, object, or style reference
- Plan to use generate_image_from_image for ALL scenes with that character

### Step 4: Asset Generation Strategy

#### For Videos WITH Voiceover (Recommended Workflow):
1. **Generate voiceover FIRST** to establish timing:
   ```
   generate_speech(text=script, voice="Friendly_Person", speed=1.0, project_id=project_id, scene_id=scene_id)
   ```
   Common voices (17 total available):
   - **Wise_Woman**: Professional, authoritative female
   - **Friendly_Person**: Warm, approachable narrator (default)
   - **Deep_Voice_Man**: Deep, commanding male
   - **Calm_Woman**: Soothing, peaceful female
   - **Inspirational_girl**: Energetic, motivating young female
   - **Casual_Guy**: Relaxed, conversational male
   - See all 17 voices in tool documentation

2. **Plan scenes based on voiceover timing** - ensures perfect sync
3. **Generate images** that match narration beats
   ```
   generate_image_from_text(prompt, model="imagen4", aspect_ratio="16:9", style_modifiers=["cinematic"], project_id=pid, scene_id=sid)
   ```
   - Models: **imagen4** (default, fast) or **flux_pro** (artistic)
   - 🎥 **TIP**: Use `cinematic_photography_guide()` for professional visuals!
   
4. **Animate images** with motion that complements the audio
   ```
   generate_video_from_image(image_url, motion_prompt, duration=5, aspect_ratio="16:9", model="kling_2.1", project_id=pid, scene_id=sid)
   ```
   - Duration: 5 or 10 seconds for Kling (default), 6 or 10 for Hailuo
   - Model: "kling_2.1" (default, reliable) or "hailuo_02" (10% cheaper)
   - Prompt optimizer: True by default (Hailuo only, improves results)
   - Motion strength: 0.1-1.0 (Kling only)
   - **NEW**: Queue support with `return_queue_id=True` for non-blocking generation
   
5. **Add background music** at lower volume
   ```
   generate_music(prompt, duration=95, project_id=project_id)
   ```

#### For Videos WITHOUT Voiceover:
1. Generate images for visual storytelling
2. Animate with dynamic motion
3. Add music as the primary audio

#### Working with Existing Images:
🔴 **CRITICAL RULE**: If the user provides a reference image with a character, you MUST:
1. **First analyze the reference image** to understand what character/subject it contains
2. **Use generate_image_from_image for ALL scenes** where that character appears
3. **NEVER switch to generate_image_from_text** for scenes with the same character
4. **ALWAYS refer to the subject as "character"** in prompts - avoid names, pronouns (he/she), or specific identifiers

Example workflow when user provides character reference:
```
# User provides: "/path/to/character.png" (e.g., a specific person/character)
# ✅ CORRECT: Use for ALL scenes with this character
generate_image_from_image("/path/to/character.png", "character with sled in snow", project_id=pid, scene_id=s1)
generate_image_from_image("/path/to/character.png", "character looking surprised", project_id=pid, scene_id=s2)
generate_image_from_image("/path/to/character.png", "character setting up traps", project_id=pid, scene_id=s3)

# ❌ WRONG: Switching to text generation for same character
generate_image_from_image("/path/to/character.png", "character standing", ...)
generate_image_from_text("person with sled", ...)  # NO! Use the reference!
```

Technical details:
1. **Local files are auto-uploaded**: Just provide the path
2. **Transform existing images**: Use generate_image_from_image
   - Guidance scale: Fixed at 3.5 for optimal results
   - Safety tolerance: 1-6 (default 5)
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
2. **Create scenes** with visual descriptions
3. **Generate images** for each scene sequentially
4. **Animate images** into videos one by one
5. **Generate music** that matches the mood
6. **Assemble** into final video

### 📈 Sequential vs Queued Processing

#### Sequential Processing (Default)
Call generation tools one at a time for:
- Clear progress tracking in the UI
- Easier debugging if something fails
- Better readability of the generation process

#### Queued Processing (NEW)
For long-running tasks, use queue-based generation:
```
# Submit video generation and get queue ID immediately
queue_id = generate_video_from_image(image_url, motion_prompt, duration=10, return_queue_id=True)
# Returns: {"queued": True, "queue_id": "abc123", "estimated_cost": 0.50}

# Check status anytime
status = get_queue_status(task_id=queue_id)
# Returns: {"status": "in_progress", "queue_position": 2, "progress": 45}

# Monitor all project tasks
get_queue_status(project_id=project_id, include_completed=True)
```

Benefits:
- Non-blocking: Continue with other tasks while videos generate
- Progress tracking: Real-time updates on queue position and progress
- Batch processing: Submit multiple videos and monitor them together
- Cancellation: Cancel tasks if needed with `cancel_task(task_id)`

## 💡 Platform-Specific Tips for {platform.replace('_', ' ').title()}
{_get_platform_specific_tips(platform)}

## 🛠️ Assembly & Export Tools

### Final Assembly (call ONCE after all generation):
```
assemble_video(project_id, scene_ids=None, output_format="mp4", quality_preset="high")
```
- Automatically combines ALL scenes and audio tracks
- Quality presets: "low", "medium", "high"

### Optional Export for Platform:
```
export_final_video(project_id, platform="youtube", include_captions=False, include_watermark=False)
```

### Download Assets Locally:
```
download_assets(asset_urls, project_id, asset_type="video", parallel_downloads=5)
```

## 📊 Helpful Analysis & Monitoring Tools

### Analysis Tools
- **analyze_script**(script, target_duration, platform) - Get scene suggestions and timing
- **suggest_scenes**(project_id, style="dynamic") - Generate scene ideas

### Project Resources
- **Get current status**: Use resource `project://current`
- **Check costs**: Use resource `project://{project_id}/costs`

### Queue Management (NEW)
- **get_queue_status**(task_id) - Check specific task progress
- **get_queue_status**(project_id=pid) - Monitor all project tasks
- **cancel_task**(task_id) - Cancel a queued/running task
- **Queue resources**:
  - `queue://status` - Overall queue statistics
  - `queue://task/{task_id}` - Specific task details
  - `queue://project/{project_id}` - Project queue status

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
    
    # Return in FastMCP 2.0 format
    return [{"role": "assistant", "content": content}]


def _get_scene_duration_recommendation(total_duration: int) -> str:
    """Get scene duration mix recommendation."""
    if total_duration <= 30:
        return "Use 5-second scenes with Kling for reliable results"
    elif total_duration <= 60:
        return "Mix of 5-second and 10-second scenes"
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
    """Rough cost estimate for a video using Hailuo model."""
    scenes = duration // 10 + (1 if duration % 10 >= 5 else 0)
    image_cost = scenes * 0.04
    video_cost = duration * 0.05  # Default Kling pricing
    audio_cost = 0.10 if duration > 15 else 0  # Assume music for longer videos
    speech_cost = 0.10  # Assume some narration
    
    return image_cost + video_cost + audio_cost + speech_cost