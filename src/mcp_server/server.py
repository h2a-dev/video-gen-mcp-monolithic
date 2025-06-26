"""Main MCP server implementation for Video Agent using FastMCP 2.0."""

import json
from fastmcp import FastMCP
from typing import List, Optional, Dict, Any
from .config import settings

# Import all tool implementations with aliases to avoid conflicts
from .tools.project import (
    create_project as create_project_impl,
    add_scene as add_scene_impl,
    list_projects as list_projects_impl
)
from .tools.generation import (
    generate_image_from_text as generate_image_from_text_impl,
    generate_image_from_image as generate_image_from_image_impl,
    generate_video_from_image as generate_video_from_image_impl,
    generate_music as generate_music_impl,
    generate_speech as generate_speech_impl
)
from .tools.assembly import (
    download_assets as download_assets_impl,
    add_audio_track as add_audio_track_impl,
    assemble_video as assemble_video_impl
)
from .tools.utility import (
    analyze_script as analyze_script_impl,
    suggest_scenes as suggest_scenes_impl,
    upload_image_file as upload_image_file_impl
)
from .tools.queue import (
    get_queue_status as get_queue_status_impl,
    cancel_task as cancel_task_impl
)

# Import resource implementations
from .resources import (
    get_current_project,
    get_project_timeline,
    get_cost_breakdown,
    get_platform_specs,
    get_queue_status_resource
)

# Import prompt implementations
from .prompts import (
    video_creation_wizard,
    script_to_scenes,
    cinematic_photography_guide,
    list_video_agent_capabilities
)

# Create the FastMCP server instance
mcp = FastMCP(
    name=settings.server_name,
    version=settings.version
)

# ============================================================================
# PROJECT MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
async def create_project(
    title: str,
    platform: str,
    script: Optional[str] = None,
    target_duration: Optional[int] = None,
    aspect_ratio: Optional[str] = None
) -> Dict[str, Any]:
    """
    Initialize a new video project with smart defaults based on platform.
    
    Args:
        title: Project title
        platform: Target platform (youtube, tiktok, instagram_reel, etc.)
        script: Optional script/narration text
        target_duration: Target duration in seconds (uses platform default if not specified)
        aspect_ratio: Video aspect ratio (uses platform default if not specified)
    
    Returns:
        Project details including ID, settings, and cost estimate
    """
    # Convert string parameters to proper types if needed
    if target_duration is not None and isinstance(target_duration, str):
        target_duration = int(target_duration)
    return await create_project_impl(title, platform, script, target_duration, aspect_ratio)


@mcp.tool()
async def add_scene(
    project_id: str,
    description: str,
    duration: int,
    position: Optional[int] = None
) -> Dict[str, Any]:
    """
    Add a scene to the project timeline.
    
    Args:
        project_id: Project ID
        description: Scene description for asset generation
        duration: Scene duration in seconds (5 or 10 recommended)
        position: Optional position in timeline (appends to end if not specified)
    
    Returns:
        Scene details with ID and timeline position
    """
    # Convert string parameters to proper types if needed
    if isinstance(duration, str):
        duration = int(duration)
    if position is not None and isinstance(position, str):
        position = int(position)
    return await add_scene_impl(project_id, description, duration, position)


@mcp.tool()
async def list_projects() -> Dict[str, Any]:
    """
    List all video projects with their current status.
    
    Returns:
        List of projects with basic info and status
    """
    return await list_projects_impl()


# ============================================================================
# IMAGE GENERATION TOOLS
# ============================================================================

@mcp.tool()
async def generate_image_from_text(
    prompt: str,
    model: str = "imagen4",
    aspect_ratio: str = "16:9",
    style_modifiers: Optional[List[str]] = None,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an image from a text prompt.
    
    Args:
        prompt: Text description of the image to generate
        model: AI model to use (imagen4, flux_pro)
        aspect_ratio: Image aspect ratio
        style_modifiers: Optional style keywords (cinematic, realistic, etc.)
        project_id: Optional project to associate with
        scene_id: Optional scene to associate with
    
    Returns:
        Generated image URL and metadata
    """
    # Handle case where style_modifiers is passed as JSON string
    if style_modifiers is not None and isinstance(style_modifiers, str):
        try:
            style_modifiers = json.loads(style_modifiers)
        except:
            # If JSON parsing fails, treat as a single modifier
            style_modifiers = [style_modifiers]
    
    return await generate_image_from_text_impl(
        prompt, model, aspect_ratio, style_modifiers, project_id, scene_id
    )


@mcp.tool()
async def generate_image_from_image(
    image_url: str,
    prompt: str,
    safety_tolerance: str = "3",
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transform an image based on a text prompt using AI.
    Uses Flux Kontext with fixed guidance scale of 3.5 for optimal results.
    
    Args:
        image_url: Source image - can be a URL or local file path
        prompt: Text description of the transformation to apply
        safety_tolerance: Safety filter level (1-6, default 3. 1=strictest, 6=most permissive)
        project_id: Optional project to associate the image with
        scene_id: Optional scene within the project
        
    Returns:
        Dict with transformed image results
    """
    # Convert safety_tolerance to int if it's a string
    if isinstance(safety_tolerance, str):
        safety_tolerance = int(safety_tolerance)
    return await generate_image_from_image_impl(
        image_url, prompt, safety_tolerance, project_id, scene_id
    )


# ============================================================================
# VIDEO GENERATION TOOLS
# ============================================================================

@mcp.tool()
async def generate_video_from_image(
    image_url: str,
    motion_prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    model: Optional[str] = None,
    motion_strength: float = 0.7,
    prompt_optimizer: bool = True,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None,
    use_queue: bool = True,
    return_queue_id: bool = False
) -> Dict[str, Any]:
    """
    Convert a single image to video with AI-generated motion.
    
    Args:
        image_url: URL or local path of the source image
        motion_prompt: Description of desired motion/animation
        duration: Video duration in seconds (5 or 10 for Kling, 6 or 10 for Hailuo)
        aspect_ratio: Video aspect ratio
        motion_strength: Motion intensity (0.0-1.0) - only used for Kling model
        model: Video generation model ("kling_2.1" or "hailuo_02"). Defaults to settings
        prompt_optimizer: Whether to use prompt optimization - only used for Hailuo model
        project_id: Optional project to associate with
        scene_id: Optional scene to associate with
        use_queue: Whether to use queued processing for better tracking (default: True)
        return_queue_id: Return queue ID immediately without waiting for result
    
    Returns:
        Generated video URL and metadata, or queue ID if return_queue_id=True
    """
    # Convert string parameters to proper types if needed
    if isinstance(duration, str):
        duration = int(duration)
    if isinstance(motion_strength, str):
        motion_strength = float(motion_strength)
    return await generate_video_from_image_impl(
        image_url, motion_prompt, duration, aspect_ratio, 
        motion_strength, model, prompt_optimizer, project_id, scene_id,
        use_queue, return_queue_id
    )


# ============================================================================
# AUDIO GENERATION TOOLS
# ============================================================================

@mcp.tool()
async def generate_music(
    prompt: str,
    duration: int = 95,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate background music from a text description.
    
    Args:
        prompt: Music style/mood description
        duration: Duration in seconds (Lyria2 generates ~95 seconds)
        project_id: Optional project to associate with
    
    Returns:
        Generated music URL and metadata
    """
    if isinstance(duration, str):
        duration = int(duration)
    return await generate_music_impl(prompt, duration, project_id)


@mcp.tool()
async def generate_speech(
    text: str,
    voice: str = "en-US-1",
    speed: float = 1.0,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate speech/voiceover from text.
    
    Args:
        text: Text to convert to speech
        voice: Voice ID (see available voices)
        speed: Speech speed multiplier
        project_id: Optional project to associate with
        scene_id: Optional scene to associate with
    
    Returns:
        Generated speech audio URL and metadata
    """
    if isinstance(speed, str):
        speed = float(speed)
    return await generate_speech_impl(text, voice, speed, project_id, scene_id)


# ============================================================================
# QUEUE MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
async def get_queue_status(
    task_id: Optional[str] = None,
    project_id: Optional[str] = None,
    status_filter: Optional[List[str]] = None,
    include_completed: bool = False
) -> Dict[str, Any]:
    """
    Get status of queued generation tasks.
    
    Args:
        task_id: Specific task ID to check
        project_id: Filter by project ID
        status_filter: Filter by status (queued, in_progress, completed, failed, cancelled)
        include_completed: Include completed/failed/cancelled tasks (default: False)
    
    Returns:
        Queue status information with task details
    """
    # Handle case where status_filter is passed as JSON string
    if status_filter is not None and isinstance(status_filter, str):
        try:
            status_filter = json.loads(status_filter)
        except:
            # If JSON parsing fails, treat as a single status
            status_filter = [status_filter]
    
    return await get_queue_status_impl(task_id, project_id, status_filter, include_completed)


@mcp.tool()
async def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    Cancel a queued or running generation task.
    
    Args:
        task_id: Task ID to cancel
    
    Returns:
        Cancellation result
    """
    return await cancel_task_impl(task_id)


# ============================================================================
# ASSEMBLY AND DOWNLOAD TOOLS
# ============================================================================

@mcp.tool()
async def download_assets(
    asset_urls: List[str],
    project_id: str,
    asset_type: Optional[str] = None,
    parallel_downloads: int = 5
) -> Dict[str, Any]:
    """
    Download generated assets from FAL or other sources.
    
    Args:
        asset_urls: List of URLs to download
        project_id: Project to associate assets with
        asset_type: Type of assets (image, video, audio)
        parallel_downloads: Max concurrent downloads (agent handles download tasks)
    
    Returns:
        Download summary and local paths
    """
    # Handle case where asset_urls is passed as JSON string
    if isinstance(asset_urls, str):
        try:
            asset_urls = json.loads(asset_urls)
        except:
            # If JSON parsing fails, treat as a single URL
            asset_urls = [asset_urls]
    
    if isinstance(parallel_downloads, str):
        parallel_downloads = int(parallel_downloads)
    return await download_assets_impl(asset_urls, project_id, asset_type, parallel_downloads)


@mcp.tool()
async def add_audio_track(
    video_path: str,
    audio_path: str,
    track_type: str = "background",
    volume_adjustment: float = 1.0,
    fade_in: float = 0,
    fade_out: float = 0
) -> Dict[str, Any]:
    """
    Add audio track to video without re-encoding video stream.
    
    Args:
        video_path: Path to video file
        audio_path: Path to audio file
        track_type: Type of audio (background, voiceover, sfx, music)
        volume_adjustment: Volume multiplier (0.0-2.0)
        fade_in: Fade in duration in seconds
        fade_out: Fade out duration in seconds
    
    Returns:
        Output path with mixed audio
    """
    # Convert string parameters to proper types if needed
    if isinstance(volume_adjustment, str):
        volume_adjustment = float(volume_adjustment)
    if isinstance(fade_in, str):
        fade_in = float(fade_in)
    if isinstance(fade_out, str):
        fade_out = float(fade_out)
    return await add_audio_track_impl(
        video_path, audio_path, track_type, volume_adjustment, fade_in, fade_out
    )


@mcp.tool()
async def assemble_video(
    project_id: str,
    scene_ids: Optional[List[str]] = None,
    output_format: str = "mp4",
    quality_preset: str = "high"
) -> Dict[str, Any]:
    """
    Assemble scenes into a complete video using ffmpeg.
    
    Args:
        project_id: Project ID to assemble
        scene_ids: Optional specific scenes (uses all if not specified)
        output_format: Output format (mp4, mov, etc.)
        quality_preset: Quality level (low, medium, high)
    
    Returns:
        Assembled video path and metadata
    """
    return await assemble_video_impl(project_id, scene_ids, output_format, quality_preset)


# ============================================================================
# UTILITY TOOLS
# ============================================================================

@mcp.tool()
async def analyze_script(
    script: str,
    target_duration: Optional[int] = None,
    platform: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a script for video production insights.
    
    Args:
        script: The script text to analyze
        target_duration: Target video duration in seconds
        platform: Target platform for optimization
    
    Returns:
        Analysis with scene suggestions, duration estimates, and key moments
    """
    if target_duration is not None and isinstance(target_duration, str):
        target_duration = int(target_duration)
    return await analyze_script_impl(script, target_duration, platform)


@mcp.tool()
async def suggest_scenes(
    project_id: str,
    style: str = "dynamic"
) -> Dict[str, Any]:
    """
    Generate scene suggestions based on project script.
    
    Args:
        project_id: Project ID with script
        style: Visual style (dynamic, minimal, cinematic)
    
    Returns:
        List of scene suggestions with descriptions
    """
    return await suggest_scenes_impl(project_id, style)


@mcp.tool()
async def upload_image_file(file_path: str) -> Dict[str, Any]:
    """
    Upload a local image file to FAL and get a URL.
    
    Args:
        file_path: Path to the local image file
        
    Returns:
        Dict with upload results including the URL
    """
    return await upload_image_file_impl(file_path)


@mcp.tool()
async def get_server_info() -> Dict[str, Any]:
    """Get information about the Video Agent server."""
    return {
        "name": settings.server_name,
        "version": settings.version,
        "description": settings.description,
        "storage_dir": str(settings.storage_dir),
        "fal_api_configured": bool(settings.fal_api_key)
    }


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("project://current")
async def resource_current_project() -> Dict[str, Any]:
    """Get the currently active project details."""
    return await get_current_project()


@mcp.resource("project://{project_id}/timeline")
async def resource_project_timeline(project_id: str) -> Dict[str, Any]:
    """Get detailed timeline for a specific project."""
    return await get_project_timeline(project_id)


@mcp.resource("project://{project_id}/costs")
async def resource_cost_breakdown(project_id: str) -> Dict[str, Any]:
    """Get detailed cost breakdown for a project."""
    return await get_cost_breakdown(project_id)


@mcp.resource("platform://{platform}/specs")
async def resource_platform_specs(platform: str) -> Dict[str, Any]:
    """Get specifications and recommendations for a platform."""
    return await get_platform_specs(platform)


@mcp.resource("queue://status")
async def resource_queue_status() -> Dict[str, Any]:
    """Get overall queue status and statistics."""
    return await get_queue_status_resource(["status"])


@mcp.resource("queue://task/{task_id}")
async def resource_queue_task(task_id: str) -> Dict[str, Any]:
    """Get status of a specific queued task."""
    return await get_queue_status_resource(["task", task_id])


@mcp.resource("queue://project/{project_id}")
async def resource_queue_project(project_id: str) -> Dict[str, Any]:
    """Get queue status for all tasks in a project."""
    return await get_queue_status_resource(["project", project_id])


# ============================================================================
# PROMPTS
# ============================================================================

@mcp.prompt("video_creation_wizard")
async def prompt_video_creation_wizard(
    platform: str,
    topic: str
) -> List[Dict[str, Any]]:
    """
    Interactive wizard for creating videos from scratch.
    
    Args:
        platform: Target platform (youtube, tiktok, etc.)
        topic: Video topic or theme
    
    Returns:
        List of messages for the video creation workflow
    """
    return await video_creation_wizard(platform, topic)


@mcp.prompt("script_to_scenes")
async def prompt_script_to_scenes(
    script: str,
    target_duration: int,
    style: str = "dynamic"
) -> List[Dict[str, Any]]:
    """
    Convert a script into detailed scene breakdowns.
    
    Args:
        script: The video script
        target_duration: Target video duration in seconds
        style: Visual style (dynamic, minimal, cinematic)
    
    Returns:
        List of messages with scene breakdowns
    """
    return await script_to_scenes(script, target_duration, style)


@mcp.prompt("cinematic_photography_guide")
async def prompt_cinematic_photography_guide(
    scene_type: str,
    mood: str
) -> List[Dict[str, Any]]:
    """
    Get cinematic photography guidance for scenes.
    
    Args:
        scene_type: Type of scene (dialogue, action, landscape, etc.)
        mood: Desired mood (dramatic, peaceful, energetic, etc.)
    
    Returns:
        List of messages with cinematic guidance
    """
    return await cinematic_photography_guide(scene_type, mood)


@mcp.prompt("list_video_agent_capabilities")
async def prompt_list_capabilities() -> List[Dict[str, Any]]:
    """
    List all Video Agent capabilities and features.
    
    Returns:
        List of messages describing capabilities
    """
    return await list_video_agent_capabilities()


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

def get_server():
    """Get the MCP server instance."""
    return mcp


if __name__ == "__main__":
    # Validate settings before running
    settings.validate()
    mcp.run()