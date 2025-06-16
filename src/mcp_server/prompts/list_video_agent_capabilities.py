"""List Video Agent capabilities prompt implementation."""


async def list_video_agent_capabilities() -> str:
    """List all available MCP server capabilities and provide getting started guide."""
    return """# 🎬 Video Agent MCP Server Capabilities

## 📝 Prompts
Interactive workflows and creation guides:

• **video_creation_wizard** (platform, topic) - Complete video creation workflow from concept to export
• **script_to_scenes** (project_id) - Convert script into optimized scene breakdown
• **list_video_agent_capabilities** () - This comprehensive guide you're reading now!

## 🔧 Tools
Video creation and manipulation functions:

### Project Management
• **create_project** (title, platform, script, target_duration, aspect_ratio) - Initialize new video project
• **add_scene** (project_id, description, duration, position) - Add scene to timeline
• **list_projects** () - View all video projects

### Content Generation
• **generate_image_from_text** (prompt, model, aspect_ratio, style_modifiers, project_id, scene_id) - Text to image
• **generate_video_from_image** (image_url, motion_prompt, duration, aspect_ratio, motion_strength) - Image to video
• **generate_music** (prompt, duration, project_id) - Background music generation
• **generate_speech** (text, voice, speed, project_id, scene_id) - Text to speech/voiceover

### Video Assembly
• **assemble_video** (project_id, scene_ids, output_format, quality_preset) - Combine scenes into video

### Utility Tools
• **analyze_script** (script, target_duration, platform) - Get scene suggestions from script
• **suggest_scenes** (project_id, style) - AI-powered scene recommendations
• **get_server_info** () - Server configuration and status

## 📊 Resources
Dynamic project and platform information:

### Project Resources
• **project://current** - Currently active project details and status
• **project://{project_id}/timeline** - Scene timeline with durations and order
• **project://{project_id}/costs** - Detailed cost breakdown by service

### Platform Resources
• **platform://{platform_name}/specs** - Platform requirements and best practices

---

**🚀 Quick Start Guide:**

1. **Simple Video Creation:**
   ```
   Use prompt: video_creation_wizard("tiktok", "cooking tips")
   ```

2. **Manual Workflow:**
   - create_project("My Video", "youtube")
   - analyze_script("Your script here...")
   - add_scene() for each scene
   - generate_image_from_text() for visuals
   - generate_video_from_image() to animate
   - assemble_video() to combine

3. **From Existing Assets:**
   - create_project() with your platform
   - Use generate_video_from_image() with your images
   - Add generate_music() for background
   - assemble_video() to finish

**💡 Pro Tips:**
• Start with prompts for guided workflows
• Use analyze_script() to plan scenes efficiently
• Check platform specs before generating content
• Monitor costs with project resources
• Download assets early to avoid timeouts

**💰 Cost Optimization:**
• 5-second videos cost less than 10-second
• Image generation: ~$0.04 per image
• Video generation: ~$0.05 per second
• Music: ~$0.10 per 30 seconds
• Speech: ~$0.10 per 1000 characters

**🎯 Common Workflows:**

1. **TikTok/Reels (Short Form)**
   - Target: 15-30 seconds
   - 3-6 quick scenes
   - Trending music + captions
   - Vertical format (9:16)

2. **YouTube (Long Form)**
   - Target: 3-10 minutes
   - Mix of scenes and narration
   - Background music + voiceover
   - Horizontal format (16:9)

3. **Product Demo**
   - Show features visually
   - Clear voiceover explanation
   - Professional transitions
   - Platform-specific formatting

**📚 Available Platforms:**
• youtube - Long-form content
• youtube_shorts - Vertical short videos
• tiktok - Trending short content
• instagram_reel - Visual storytelling
• instagram_post - Square/vertical posts
• twitter - Brief impactful content
• linkedin - Professional content
• facebook - Versatile formats
• custom - Any specifications

**🎨 Available Models:**
• **Images**: imagen4, flux_pro
• **Video**: kling_2.1 (5-10 second clips)
• **Music**: lyria2 (~95 seconds)
• **Speech**: minimax (multiple voices)

Need help? Start with: `video_creation_wizard("your_platform", "your_topic")`"""