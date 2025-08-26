"""YouTube channel details tool for MCP server."""

from typing import Dict, Any
from mcp_server.services.youtube_service import get_youtube_service
import logging

logger = logging.getLogger(__name__)


async def get_youtube_channel_details_by_video_id(video_id: str) -> Dict[str, Any]:
    """Get detailed information about a YouTube channel based on a video ID.
    
    This tool first retrieves the video to get its channel ID, then fetches 
    comprehensive channel information including statistics and metadata.
    
    Args:
        video_id: YouTube video ID (e.g., "dQw4w9WgXcQ")
    
    Returns:
        Dictionary containing:
        - success: Whether the request was successful
        - channel: Channel object with:
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
    try:
        youtube_service = get_youtube_service()
        result = await youtube_service.get_channel_details_by_video_id(video_id)
        
        if result["success"]:
            logger.info(f"Successfully fetched channel details for video: {video_id}")
        else:
            logger.error(f"Failed to get channel details: {result.get('error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"Error in get_youtube_channel_details_by_video_id: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get channel details: {str(e)}"
        }