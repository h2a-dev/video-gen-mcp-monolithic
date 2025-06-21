"""List Video Agent capabilities prompt implementation."""


async def list_video_agent_capabilities() -> str:
    """List all available MCP server capabilities and provide getting started guide."""
    
    # This returns a comprehensive hardcoded list of all server capabilities
    # In production, this could be generated dynamically from server introspection
    
    return """# 🎬 Video Agent MCP Server Capabilities

## 📝 Prompts
Interactive workflows and creation guides:

• **video_creation_wizard** (platform, topic) - Complete video creation workflow from concept to export
• **script_to_scenes** (project_id) - Convert script into optimized scene breakdown with timing
• **cinematic_photography_guide** () - Professional camera techniques for cinematic visuals
• **list_video_agent_capabilities** () - This comprehensive guide you're reading now!

## 🔧 Tools
Video creation and manipulation functions:

### Project Management
• **create_project** (title, platform, script, target_duration, aspect_ratio) - Initialize new video project with platform defaults
• **add_scene** (project_id, description, duration, position) - Add scene to project timeline
• **list_projects** () - View all video projects with status and costs

### Content Generation
• **generate_image_from_text** (prompt, model, aspect_ratio, style_modifiers, project_id, scene_id) - AI text-to-image generation
• **generate_image_from_image** (image_url, prompt, guidance_scale, safety_tolerance, project_id, scene_id) - Transform images with AI
  - Accepts: URL or local file path for image_url (auto-uploads files)
  - Safety tolerance: 1-6 (default 5, higher = more permissive)
• **generate_video_from_image** (image_url, motion_prompt, duration, aspect_ratio, motion_strength, model, prompt_optimizer, project_id, scene_id) - Animate still images with AI
  - Accepts: URL or local file path for image_url (auto-uploads files)
  - Models: "kling_2.1" (5 or 10 sec) or "hailuo_02" (6 or 10 sec)
  - Motion strength: Only for Kling model (0.1-1.0)
  - Prompt optimizer: Only for Hailuo model (default True)
• **generate_music** (prompt, duration, project_id) - Generate background music (~95 seconds)
• **generate_speech** (text, voice, speed, project_id, scene_id) - Text-to-speech with multiple voices

### Video Assembly
• **download_assets** (asset_urls, project_id, asset_type, parallel_downloads) - Download generated assets locally
• **assemble_video** (project_id, scene_ids, output_format, quality_preset) - Combine scenes AND mix all audio tracks in one step (call only ONCE)
• **add_audio_track** (video_path, audio_path, track_type, volume_adjustment, fade_in, fade_out) - Add audio to existing video (rarely needed)
• **export_final_video** (project_id, platform, include_captions, include_watermark, output_path) - Create platform-optimized copy in exports folder (optional)

### Utility Tools
• **analyze_script** (script, target_duration, platform) - Analyze script for scene suggestions and timing
• **suggest_scenes** (project_id, style) - Generate scene ideas based on script and style
• **upload_image_file** (file_path) - Upload local image file to FAL and get URL for use in other tools
• **get_server_info** () - Server configuration and status

## 📊 Resources
Dynamic project and platform information:

### Project Resources
• **project://current** - Currently active project details, progress, and next actions
• **project://{project_id}/timeline** - Scene timeline with durations, order, and status
• **project://{project_id}/costs** - Detailed cost breakdown by service with projections

### Platform Resources
• **platform://{platform_name}/specs** - Platform requirements, limits, and best practices

---

## 🚀 Quick Start Guide

### 1. **Simple Video Creation (Recommended)**
```
Use prompt: video_creation_wizard("tiktok", "cooking tips")
```
This will guide you through the entire process step-by-step.

### 2. **Voiceover-First Workflow (RECOMMENDED for narrated videos)**
```python
# Create project
create_project("My Tutorial", "youtube", script="Your full script here...", target_duration=300)

# Analyze your script (includes voice recommendations)
analyze_script("Your script here...", target_duration=300, platform="youtube")

# Generate voiceover FIRST to establish timing
generate_speech("Your full script text", voice="Friendly_Person", project_id=project_id)

# Add scenes based on voiceover timing
add_scene(project_id, "Opening shot of kitchen", duration=10)
add_scene(project_id, "Ingredients close-up", duration=5)

# Generate visuals that match narration
generate_image_from_text("modern kitchen with cooking ingredients", project_id=project_id, scene_id=scene_id)

# Animate the images to complement speech rhythm
generate_video_from_image(image_url, "slow pan across ingredients", duration=10, model="kling_2.1")

# Add background music at low volume
generate_music("upbeat cooking show music", project_id=project_id)

# Assemble everything ONCE (automatically mixes ALL audio tracks)
assemble_video(project_id)  # This creates the final video with all audio

# OPTIONAL: Create platform-optimized copy in exports folder
export_final_video(project_id, platform="youtube")  # Only if you need a separate export
```

### 3. **From Existing Assets**
```python
# Create project for your platform
create_project("My Video", "instagram_reel")

# Download your assets
download_assets([url1, url2, url3], project_id)

# Generate videos from your images (supports URL or local file)
generate_video_from_image(your_image_url, "zoom in with dramatic effect", model="kling_2.1")
# Or from local file (auto-uploads):
generate_video_from_image("/path/to/local/image.png", "pan left slowly", model="kling_2.1", duration=5)

# Transform existing images
generate_image_from_image("/path/to/image.jpg", "make it more cinematic")
generate_image_from_image(image_url, "add warm sunset lighting")

# Add generated audio
generate_music("trendy upbeat music")

# Assemble and export
assemble_video(project_id)
export_final_video(project_id, "instagram_reel")
```

## 🚀 Example: Complete Video Project Workflow

```python
# Step 1: Transform reference images (if needed)
generate_image_from_image(ref1, "add cinematic lighting", project_id=pid, scene_id=s1)
generate_image_from_image(ref2, "enhance colors", project_id=pid, scene_id=s2)
generate_image_from_image(ref3, "add dramatic shadows", project_id=pid, scene_id=s3)

# Step 2: Generate videos from images
generate_video_from_image(img1, "slow zoom in", duration=5, model="kling_2.1", project_id=pid, scene_id=s1)
generate_video_from_image(img2, "pan left", duration=5, model="kling_2.1", project_id=pid, scene_id=s2)
generate_video_from_image(img3, "zoom out", duration=5, model="kling_2.1", project_id=pid, scene_id=s3)

# Step 3: Generate audio
generate_speech(text1, project_id=pid, scene_id=s1)
generate_music("epic background music", project_id=pid)

# Step 4: Assemble final video
assemble_video(project_id)
```

## 💡 Pro Tips

### Workflow Best Practices
• **RECOMMENDED**: Process scenes sequentially for clear progress tracking
• **IMPORTANT**: Generate voiceover FIRST for narrated videos - this ensures perfect audio-visual sync
• **CRITICAL**: When user provides reference image URL, use `generate_image_from_image`, NOT `generate_image_from_text`
• Start with `video_creation_wizard()` for guided workflows
• Use `analyze_script()` to get voice recommendations and optimize timing
• Account for frame trimming: videos will be ~0.5s shorter per scene transition
• Check platform specs with `platform://specs` before generating
• Monitor costs in real-time with `project://costs` resource

### Cost Optimization
• Use 5-second videos instead of 10-second when possible (50% savings)
• Reuse images across scenes with different animations
• Skip background music for sub-60 second videos
• Generate voiceover only for key scenes

### Platform-Specific Tips
• **TikTok/Reels**: Keep scenes under 5 seconds, use vertical format (9:16)
• **YouTube**: Mix scene durations, add voiceover for engagement
• **LinkedIn**: Professional tone, include captions for silent viewing

### Asset Management
• Download assets immediately after generation to avoid timeouts
• Use `download_assets()` to delegate download tasks to agent
• Check storage with `get_server_info()` to monitor disk usage

## 💰 Pricing Reference

### Generation Costs
• **Images**: $0.04 per image (imagen4, flux_pro)
• **Video**: 
  - $0.05 per second (kling_2.1)
  - $0.045 per second (hailuo_02) - 10% cheaper!
• **Music**: $0.10 per ~95 second track (lyria2)
• **Speech**: $0.10 per 1000 characters (minimax)

### Example Project Costs
• **30s TikTok**: ~$1.50-2.00 (3 images, 30s video, music)
• **60s Instagram Reel**: ~$3.00-4.00 (6 images, 60s video, music, voiceover)
• **5min YouTube**: ~$15.00-20.00 (multiple scenes, full production)

## 🎨 Reference Image Workflows

### 🔴 CRITICAL: Character Consistency Rule
**When user provides a reference image containing a CHARACTER:**
1. **ANALYZE the reference first** to identify the character/subject
2. **USE generate_image_from_image for ALL scenes** with that character
3. **NEVER switch to generate_image_from_text** for the same character

```python
# Example: User provides "/home/user/kevin.png" (Kevin from Home Alone)
# First, understand what's in the image
image_content = "Young boy with blonde hair in winter clothing"

# ✅ CORRECT: Use reference for ALL Kevin scenes
generate_image_from_image("/home/user/kevin.png", "Kevin sledding down hill", project_id=pid, scene_id=s1)
generate_image_from_image("/home/user/kevin.png", "Kevin looking shocked", project_id=pid, scene_id=s2)
generate_image_from_image("/home/user/kevin.png", "Kevin with paint cans", project_id=pid, scene_id=s3)

# ❌ WRONG: Switching to text generation loses character consistency
generate_image_from_image("/home/user/kevin.png", "Kevin standing", ...)
generate_image_from_text("young boy with sled in snow", ...)  # NO! This loses the character!
```

### Technical Details for Reference Images

1. **For Local Files** - Auto-uploaded, use path directly:
```python
generate_image_from_image(
    "/home/user/photos/character.jpg",  # Automatically uploaded
    "character in new scene with dramatic lighting",
    safety_tolerance=5  # Default 5 for creative freedom
)  # guidance_scale is fixed at 3.5
```

2. **For URLs** - Use directly:
```python
generate_image_from_image(
    "https://example.com/character.jpg", 
    "character in action pose with explosions",
    safety_tolerance=5
)
```

3. **Character vs Non-Character References**:
- **Character/Person**: MUST use for all scenes with that character
- **Object/Product**: Can mix with text generation for variety
- **Style Reference**: Can use selectively for specific scenes

## 🎯 Common Workflows

### 1. **Social Media Short (15-30s)**
```python
# Quick engaging content
video_creation_wizard("tiktok", "life hack")
# → 3-6 scenes, fast cuts, trending music
```

### 2. **Style-Consistent Content (with reference)**
```python
# User provides reference image
reference_image = "https://example.com/brand-style.jpg"

# Create project
project_id = create_project("Brand Video", "instagram_reel")

# Generate consistent images from reference
for scene in ["opening shot", "product showcase", "closing shot"]:
    img_url = generate_image_from_image(reference_image, scene, model="flux_kontext")
    add_scene(project_id, scene, duration=5)
    generate_video_from_image(img_url, "smooth camera movement")
```

### 3. **Educational Content (2-5min)**
```python
# Structured tutorial
create_project("Python Tutorial", "youtube", script=tutorial_script)
analyze_script(tutorial_script, target_duration=180)
# → Clear sections, voiceover, supporting visuals
```

### 3. **Product Showcase (30-60s)**
```python
# Highlight features
create_project("Product Demo", "instagram_reel")
suggest_scenes(project_id, style="cinematic")
# → Dynamic shots, professional look, call-to-action
```

### 4. **Story/Narrative (1-3min)**
```python
# Emotional journey
script_to_scenes(project_id)  # After adding script
# → Scene variety, music sync, voice narration
```

## 📚 Platform Support

### Supported Platforms
• **youtube** - Standard videos (up to 12 hours)
• **youtube_shorts** - Vertical shorts (up to 60s)
• **tiktok** - Short-form vertical (up to 10min)
• **instagram_reel** - Vertical stories (up to 90s)
• **instagram_post** - Feed videos (up to 60s)
• **twitter** - Quick videos (up to 2:20)
• **linkedin** - Professional content (up to 10min)
• **facebook** - Versatile formats (up to 4 hours)
• **custom** - Any specifications

### Available AI Models
• **Image Generation**: 
  - imagen4 (Google), flux_pro (Black Forest Labs) - For creating new images from text
  - **IMPORTANT**: Use generate_image_from_text for new images WITHOUT reference
• **Image-to-Image (Style Transfer)**: 
  - flux_kontext - Transform ONE reference image with new prompts
  - flux_kontext_multi - Transform MULTIPLE reference images together
  - **IMPORTANT**: Use generate_image_from_image when user provides reference image URL
• **Video Generation**: 
  - kling_2.1 (default) - 5 or 10 second videos, motion_strength parameter
  - hailuo_02 - 6 or 10 second videos, prompt_optimizer parameter, 10% cheaper
  - kling_1.6_elements - multi-image to video
• **Music**: lyria2 (DeepMind) - ~95 second tracks
• **Speech**: minimax (multiple voices)
  - Wise_Woman (professional, authoritative)
  - Friendly_Person (warm, approachable)
  - Deep_Voice_Man (commanding)
  - Calm_Woman (soothing)
  - Casual_Guy (relaxed)
  - Inspirational_girl (energetic)
  - Patient_Man (gentle)
  - Determined_Man (confident)

## 🛠️ Advanced Features

### Script Analysis
• Word count and speaking time estimation (140 words/minute)
• Scene count recommendations with frame trimming adjustments
• Key moment and theme identification
• Voice selection recommendations based on content
• Effective duration calculation (accounts for transitions)
• Cost projections

### Scene Management
• Automatic duration optimization
• Timeline visualization
• Scene reordering support
• Transition planning

### Asset Handling
• Agent-managed downloads (up to 10 concurrent)
• Automatic retries with FAL API error handling
• Local storage management
• Format validation
• Audio mixing: Multiple tracks (voiceover + music) properly combined
• Dynamic transitions: 15 frames trimmed between scenes for smoother flow

### Video Assembly
• Fast concatenation with copy codec (no re-encoding)
• Dynamic transitions (0.5s trimmed between scenes)
• Automatic audio mixing (voiceover + music)
• Platform-optimized output format

## ❓ Need Help?

1. **Get Started**: `video_creation_wizard("your_platform", "your_topic")`
2. **Check Status**: Access `project://current` resource
3. **View Costs**: Access `project://{id}/costs` resource
4. **Platform Info**: Access `platform://{name}/specs` resource

Remember: This is an MCP server - all interactions happen through Claude!"""