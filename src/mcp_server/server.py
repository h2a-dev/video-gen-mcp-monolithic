"""Main MCP server implementation for Video Agent."""

from mcp.server import FastMCP
from typing import List, Optional, Dict, Any
from .config import settings

# Create the FastMCP server instance
mcp = FastMCP(
    name=settings.server_name,
    version=settings.version,
    description=settings.description
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
    from .tools.project import create_project as impl
    # Convert string parameters to proper types if needed
    if target_duration is not None and isinstance(target_duration, str):
        target_duration = int(target_duration)
    return await impl(title, platform, script, target_duration, aspect_ratio)


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
    from .tools.project import add_scene as impl
    # Convert string parameters to proper types if needed
    if isinstance(duration, str):
        duration = int(duration)
    if position is not None and isinstance(position, str):
        position = int(position)
    return await impl(project_id, description, duration, position)


@mcp.tool()
async def list_projects() -> Dict[str, Any]:
    """
    List all video projects with their current status.
    
    Returns:
        List of projects with basic info and status
    """
    from .tools.project import list_projects as impl
    return await impl()


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
    from .tools.generation import generate_image_from_text as impl
    return await impl(prompt, model, aspect_ratio, style_modifiers, project_id, scene_id)


# ============================================================================
# ASSEMBLY TOOLS
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
    from .tools.assembly import download_assets as impl
    # Convert string parameters to proper types if needed
    if isinstance(parallel_downloads, str):
        parallel_downloads = int(parallel_downloads)
    return await impl(asset_urls, project_id, asset_type, parallel_downloads)


@mcp.tool()
async def add_audio_track(
    video_path: str,
    audio_path: str,
    track_type: str = "background",
    volume_adjustment: float = 1.0,
    fade_in: float = 0.0,
    fade_out: float = 0.0
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
    from .tools.assembly import add_audio_track as impl
    # Convert string parameters to proper types if needed
    if isinstance(volume_adjustment, str):
        volume_adjustment = float(volume_adjustment)
    if isinstance(fade_in, str):
        fade_in = float(fade_in)
    if isinstance(fade_out, str):
        fade_out = float(fade_out)
    return await impl(video_path, audio_path, track_type, volume_adjustment, fade_in, fade_out)


# ============================================================================
# VIDEO GENERATION TOOLS
# ============================================================================

@mcp.tool()
async def generate_video_from_image(
    image_url: str,
    motion_prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    motion_strength: float = 0.7,
    model: Optional[str] = None,
    prompt_optimizer: bool = True,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert a single image to video with AI-generated motion.
    
    Args:
        image_url: URL or local path of the source image
        motion_prompt: Description of desired motion/animation
        duration: Video duration in seconds (5 or 10 for Kling, 6 or 10 for Hailuo)
        aspect_ratio: Output video aspect ratio
        motion_strength: Motion intensity (0.0-1.0) - only used for Kling model
        model: Video generation model ("kling_2.1" or "hailuo_02"). Defaults to settings
        prompt_optimizer: Whether to use prompt optimization - only used for Hailuo model
        project_id: Optional project to associate with
        scene_id: Optional scene to associate with
    
    Returns:
        Generated video URL and metadata
    """
    from .tools.generation import generate_video_from_image as impl
    # Convert string parameters to proper types if needed
    if isinstance(duration, str):
        duration = int(duration)
    if isinstance(motion_strength, str):
        motion_strength = float(motion_strength)
    if isinstance(prompt_optimizer, str):
        prompt_optimizer = prompt_optimizer.lower() == "true"
    return await impl(image_url, motion_prompt, duration, aspect_ratio, motion_strength, model, prompt_optimizer, project_id, scene_id)


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
    from .tools.generation import generate_music as impl
    # Convert string parameters to proper types if needed
    if isinstance(duration, str):
        duration = int(duration)
    return await impl(prompt, duration, project_id)


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
    from .tools.generation import generate_speech as impl
    # Convert string parameters to proper types if needed
    if isinstance(speed, str):
        speed = float(speed)
    return await impl(text, voice, speed, project_id, scene_id)


@mcp.tool()
async def generate_image_from_image(
    image_url: str,
    prompt: str,
    guidance_scale: float = 3.5,
    safety_tolerance: int = 5,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transform an image based on a text prompt using AI.
    
    Args:
        image_url: Source image - can be a URL or local file path
        prompt: Text description of the transformation to apply
        guidance_scale: How closely to follow the prompt (1.0-10.0, default 3.5)
        safety_tolerance: Safety filter level (1-6, default 5. 1=strictest, 6=most permissive)
        project_id: Optional project to associate the image with
        scene_id: Optional scene within the project
        
    Returns:
        Dict with transformed image results
    """
    from .tools.generation import generate_image_from_image as impl
    # Convert string parameters to proper types if needed
    if isinstance(guidance_scale, str):
        guidance_scale = float(guidance_scale)
    if isinstance(safety_tolerance, str):
        safety_tolerance = int(safety_tolerance)
    return await impl(image_url, prompt, guidance_scale, safety_tolerance, project_id, scene_id)


@mcp.tool()
async def generate_video_from_image_batch(
    requests: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate multiple videos from images in parallel.
    
    Args:
        requests: List of video generation requests, each containing:
            - image_url: Source image URL or path (required)
            - motion_prompt: Motion description (required)
            - duration: Video duration (default: 6)
            - aspect_ratio: Video aspect ratio (default: "16:9")
            - motion_strength: Motion intensity for Kling (default: 0.7)
            - model: Video model (default: from settings)
            - prompt_optimizer: For Hailuo model (default: True)
            - project_id: Optional project ID
            - scene_id: Optional scene ID
    
    Returns:
        Dict with results for all videos
    """
    from .tools.generation import generate_video_from_image_batch as impl
    return await impl(requests)


@mcp.tool()
async def generate_image_from_image_batch(
    requests: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Transform multiple images in parallel using AI.
    
    Args:
        requests: List of image transformation requests, each containing:
            - image_url: Source image URL or path (required)
            - prompt: Transformation description (required)
            - guidance_scale: How closely to follow prompt (default: 3.5)
            - safety_tolerance: Safety filter level (default: 5)
            - project_id: Optional project ID
            - scene_id: Optional scene ID
    
    Returns:
        Dict with results for all images
    """
    from .tools.generation import generate_image_from_image_batch as impl
    return await impl(requests)


# ============================================================================
# ASSEMBLY TOOLS
# ============================================================================

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
    from .tools.assembly import assemble_video as impl
    return await impl(project_id, scene_ids, output_format, quality_preset)


# ============================================================================
# PROJECT RESOURCES
# ============================================================================

@mcp.resource("project://current")
async def get_current_project_resource() -> Dict[str, Any]:
    """Get the currently active project details."""
    from .resources import get_current_project
    return await get_current_project()


@mcp.resource("project://{project_id}/timeline")
async def get_project_timeline(project_id: str) -> Dict[str, Any]:
    """Get the scene timeline for a project."""
    from .resources import get_project_timeline
    return await get_project_timeline(project_id)


@mcp.resource("project://{project_id}/costs")
async def get_cost_breakdown(project_id: str) -> Dict[str, Any]:
    """Get detailed cost breakdown for a project."""
    from .resources import get_cost_breakdown
    return await get_cost_breakdown(project_id)


@mcp.resource("platform://{platform_name}/specs")
async def get_platform_specs(platform_name: str) -> Dict[str, Any]:
    """Get specifications and recommendations for a platform."""
    from .resources import get_platform_specs
    return await get_platform_specs(platform_name)


# ============================================================================
# WORKFLOW PROMPTS
# ============================================================================

@mcp.prompt()
async def video_creation_wizard(platform: str, topic: str) -> str:
    """
    Start an interactive video creation workflow.
    
    Args:
        platform: Target platform (youtube, tiktok, etc.)
        topic: Video topic/theme
    
    Returns:
        Guided workflow instructions
    """
    from .prompts import video_creation_wizard as impl
    return await impl(platform, topic)


@mcp.prompt()
async def script_to_scenes(project_id: str) -> str:
    """
    Convert project script into optimized scene breakdown.
    
    Args:
        project_id: Project ID with script
    
    Returns:
        Scene planning guidance
    """
    from .prompts import script_to_scenes as impl
    return await impl(project_id)


@mcp.prompt()
async def list_video_agent_capabilities() -> str:
    """
    List all available MCP server capabilities and provide getting started guide.
    
    Returns:
        Comprehensive guide of all tools, resources, and prompts
    """
    from .prompts import list_video_agent_capabilities as impl
    return await impl()


@mcp.prompt()
async def cinematic_photography_guide() -> str:
    """
    Professional cinematography guide for creating high-quality, cinematic visuals.
    
    Provides camera models, lenses, movements, and lighting techniques to enhance
    AI-generated images and videos with authentic photographic aesthetics.
    
    Returns:
        Comprehensive guide with examples and platform-specific recommendations
    """
    from .prompts import cinematic_photography_guide as impl
    return await impl()


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
    from .tools.utility import analyze_script as impl
    # Convert string parameters to proper types if needed
    if target_duration is not None and isinstance(target_duration, str):
        target_duration = int(target_duration)
    return await impl(script, target_duration, platform)


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
    from .tools.utility import suggest_scenes as impl
    return await impl(project_id, style)


@mcp.tool()
async def upload_image_file(file_path: str) -> Dict[str, Any]:
    """
    Upload a local image file to FAL and get a URL.
    
    Args:
        file_path: Path to the local image file
        
    Returns:
        Dict with upload results including the URL
    """
    from .tools.utility import upload_image_file as impl
    return await impl(file_path)


# Simplified tool for testing
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


def get_server():
    """Get the MCP server instance."""
    return mcp


if __name__ == "__main__":
    # Validate settings before running
    settings.validate()
    mcp.run()