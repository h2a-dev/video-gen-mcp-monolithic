"""Main MCP server implementation for Video Agent using FastMCP 2.0."""

import json
from fastmcp import FastMCP
from typing import List, Optional, Dict, Any, Union
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
    upload_image_file as upload_image_file_impl,
    get_youtube_categories as get_youtube_categories_impl,
    analyze_youtube_video as analyze_youtube_video_impl,
    youtube_publish as youtube_publish_impl,
    get_youtube_channel_details_by_video_id as get_youtube_channel_details_impl
)
from .tools.queue import (
    get_queue_status as get_queue_status_impl,
    cancel_task as cancel_task_impl
)
from .tools.youtube_search import (
    search_youtube_videos,
    get_youtube_video_details,
    get_youtube_trending_videos,
    get_youtube_videos_batch_details
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
    target_duration: Optional[Union[int, str]] = None,
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
    duration: Union[int, str],
    position: Optional[Union[int, str]] = None
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
    style_modifiers: Optional[Union[List[str], str]] = None,
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
    duration: Union[int, str] = 5,
    aspect_ratio: str = "16:9",
    model: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    cfg_scale: Optional[Union[float, str]] = None,
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
        aspect_ratio: Video aspect ratio (only used for Hailuo, not Kling)
        model: Video generation model ("kling_2.1" or "hailuo_02"). Defaults to settings
        negative_prompt: Negative prompt for Kling model (default: "blur, distort, and low quality")
        cfg_scale: CFG scale for Kling model (0.0-1.0, default: 0.5)
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
    if cfg_scale is not None and isinstance(cfg_scale, str):
        cfg_scale = float(cfg_scale)
    return await generate_video_from_image_impl(
        image_url, motion_prompt, duration, aspect_ratio, 
        model, negative_prompt, cfg_scale, prompt_optimizer, project_id, scene_id,
        use_queue, return_queue_id
    )


# ============================================================================
# AUDIO GENERATION TOOLS
# ============================================================================

@mcp.tool()
async def generate_music(
    prompt: str,
    duration: Union[int, str] = 95,
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
    speed: Union[float, str] = 1.0,
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
    status_filter: Optional[Union[List[str], str]] = None,
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
    asset_urls: Union[List[str], str],
    project_id: str,
    asset_type: Optional[str] = None,
    parallel_downloads: Union[int, str] = 5
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
    volume_adjustment: Union[float, str] = 1.0,
    fade_in: Union[float, str] = 0,
    fade_out: Union[float, str] = 0
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
    quality_preset: str = "high",
    add_logo: bool = False,
    logo_position: str = "bottom_right",
    logo_padding: int = 10,
    add_end_video: bool = False
) -> Dict[str, Any]:
    """
    Assemble scenes into a complete video using ffmpeg.
    
    Args:
        project_id: Project ID to assemble
        scene_ids: Optional specific scenes (uses all if not specified)
        output_format: Output format (mp4, mov, etc.)
        quality_preset: Quality level (low, medium, high)
        add_logo: Whether to add H2A logo overlay (default: False)
        logo_position: Corner position - bottom_right, bottom_left, top_right, top_left (default: bottom_right)
        logo_padding: Padding from edges in pixels (default: 10)
        add_end_video: Whether to append H2A end video (default: False)
    
    Returns:
        Assembled video path and metadata
    """
    return await assemble_video_impl(
        project_id, scene_ids, output_format, quality_preset,
        add_logo, logo_position, logo_padding, add_end_video
    )


# ============================================================================
# UTILITY TOOLS
# ============================================================================

@mcp.tool()
async def analyze_script(
    script: str,
    target_duration: Optional[Union[int, str]] = None,
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
async def get_youtube_categories(
    region_code: str = "US",
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve YouTube video categories for a specific region.
    
    Args:
        region_code: ISO 3166-1 alpha-2 country code (default: "US")
                    Examples: "US", "UK", "CA", "AU", "DE", "FR", "JP", "BR"
        language: Optional language code for category names (default: uses region default)
                 Examples: "en_US", "es_ES", "pt_BR", "ja_JP"
    
    Returns:
        Dictionary containing:
        - categories: List of available video categories with IDs and titles
        - region_code: The region code used
        - language: The language code used
        - total_count: Number of categories returned
    """
    return await get_youtube_categories_impl(region_code, language)


@mcp.tool()
async def analyze_youtube_video(
    youtube_url: str,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a YouTube video to extract scenes and create a script for generative AI video creation.
    
    This tool uses Gemini API to analyze video content and extract:
    - Scene-by-scene breakdown with timestamps
    - AI image generation prompts for each scene
    - Motion descriptions for image-to-video generation
    - Narration/audio transcript
    - Background music descriptions
    
    Perfect for recreating video structures using generative AI tools.
    
    Args:
        youtube_url: YouTube video URL (must be public)
        project_id: Optional project to associate the analysis with
        
    Returns:
        Analysis results with scene breakdown and AI prompts
    """
    return await analyze_youtube_video_impl(youtube_url, project_id)


@mcp.tool()
async def get_youtube_channel_details_by_video_id(
    video_id: str
) -> Dict[str, Any]:
    """
    Get detailed information about a YouTube channel based on a video ID.
    
    This tool retrieves comprehensive channel information by first finding the
    channel that owns the specified video, then fetching the channel's statistics,
    metadata, and content details.
    
    Args:
        video_id: YouTube video ID (e.g., "dQw4w9WgXcQ")
    
    Returns:
        Dictionary containing:
        - success: Whether the request was successful
        - channel: Channel details including:
            - channel_id: Unique channel identifier
            - title: Channel name
            - description: Channel description
            - custom_url: Custom channel URL (if set)
            - published_at: Channel creation date
            - country: Channel country (if set)
            - thumbnail_url: Channel thumbnail image URL
            - subscriber_count: Number of subscribers
            - video_count: Total number of videos
            - view_count: Total channel views
            - hidden_subscriber_count: Whether subscriber count is hidden
            - uploads_playlist_id: ID of the uploads playlist
            - video_id: The original video ID used for the query
        - video_id: The video ID used for the query
        - error: Error message if unsuccessful
    """
    return await get_youtube_channel_details_impl(video_id)


@mcp.tool()
async def youtube_publish(
    project_id: str,
    title: str,
    description: str = "",
    tags: Optional[Union[List[str], str]] = None,
    category_id: str = "22",
    privacy_status: str = "private",
    notify_subscribers: bool = True,
    use_hashtag_shorts: bool = True
) -> Dict[str, Any]:
    """
    Publish a project's video to YouTube.
    
    Args:
        project_id: ID of the project containing the video
        title: Video title (YouTube Shorts should be < 100 chars)
        description: Video description (optional, can include hashtags)
        tags: List of tags/keywords for the video (optional)
        category_id: YouTube category ID (default: 22 - People & Blogs)
        privacy_status: Privacy setting - 'public', 'private', or 'unlisted' (default: private)
        notify_subscribers: Whether to notify channel subscribers (default: true)
        use_hashtag_shorts: Auto-append #Shorts to title/description for short videos (default: true)
    
    Returns:
        Success: { success: true, video_id, video_url, title, privacy_status }
        Error: { success: false, error: message }
    
    Note: Requires YouTube API authentication. Videos under 60s will auto-tag as Shorts.
    """
    return await youtube_publish_impl(
        project_id, title, description, tags, category_id, 
        privacy_status, notify_subscribers, use_hashtag_shorts
    )


@mcp.tool()
async def search_youtube_videos_tool(
    query: str,
    max_results: int = 10,
    order: str = "relevance",
    published_after: Optional[str] = None,
    published_before: Optional[str] = None,
    region_code: Optional[str] = None,
    video_duration: Optional[str] = None,
    video_category_id: Optional[str] = None,
    channel_id: Optional[str] = None,
    next_page_token: Optional[str] = None
) -> Dict[str, Any]:
    """Search for YouTube videos with various filters and parameters.
    
    Args:
        query: Search query string (required)
        max_results: Maximum number of results to return (1-50, default: 10)
        order: Sort order - one of: relevance, date, rating, title, viewCount (default: relevance)
        published_after: ISO 8601 datetime string (e.g., "2024-01-01T00:00:00Z") for minimum publish date
        published_before: ISO 8601 datetime string for maximum publish date
        region_code: ISO 3166-1 alpha-2 country code (e.g., "US", "UK", "JP")
        video_duration: Duration filter - one of: short (<4min), medium (4-20min), long (>20min)
        video_category_id: YouTube category ID (use get_youtube_categories to find IDs)
        channel_id: Filter results to only videos from this channel
        next_page_token: Token for pagination (from previous search results)
    
    Returns:
        Dictionary containing:
        - success: Whether the search was successful
        - videos: List of video objects with metadata
        - total_results: Estimated total number of results
        - results_per_page: Number of results returned
        - next_page_token: Token to get next page of results
        - prev_page_token: Token to get previous page of results
        - error: Error message if unsuccessful
    """
    return await search_youtube_videos(
        query, max_results, order, published_after, published_before,
        region_code, video_duration, video_category_id, channel_id, next_page_token
    )


@mcp.tool()
async def get_youtube_video_details_tool(video_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific YouTube video.
    
    Args:
        video_id: YouTube video ID (e.g., "dQw4w9WgXcQ")
    
    Returns:
        Dictionary containing:
        - success: Whether the request was successful
        - video: Video object with full metadata if found
        - error: Error message if unsuccessful
    """
    return await get_youtube_video_details(video_id)


@mcp.tool()
async def get_youtube_trending_videos_tool(
    region_code: str = "US",
    category_id: Optional[str] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """Get trending YouTube videos for a specific region.
    
    Args:
        region_code: ISO 3166-1 alpha-2 country code (default: "US")
                    Examples: "US", "UK", "CA", "AU", "DE", "FR", "JP", "BR"
        category_id: Optional YouTube category ID to filter by (Note: may not work with all regions)
                    (use get_youtube_categories to find category IDs)
        max_results: Maximum number of results (1-50, default: 10)
    
    Returns:
        Dictionary containing:
        - success: Whether the request was successful
        - videos: List of trending video objects
        - region_code: The region code used
        - category_id: The category ID used (if any)
        - total_count: Number of videos returned
        - error: Error message if unsuccessful
    """
    return await get_youtube_trending_videos(region_code, category_id, max_results)


@mcp.tool()
async def get_youtube_videos_batch_details_tool(video_ids: List[str]) -> Dict[str, Any]:
    """Get detailed information for multiple YouTube videos in a single request.
    
    Args:
        video_ids: List of YouTube video IDs (e.g., ["dQw4w9WgXcQ", "jNQXAC9IVRw"])
                  Maximum 50 IDs per request
    
    Returns:
        Dictionary containing:
        - success: Whether the request was successful
        - videos: List of video objects with full metadata including thumbnails
        - total_count: Number of videos returned
        - error: Error message if unsuccessful
    """
    return await get_youtube_videos_batch_details(video_ids)


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