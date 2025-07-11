"""YouTube search tools for MCP server."""

from typing import Dict, Any, Optional, List
from mcp_server.services.youtube_service import get_youtube_service
import logging

logger = logging.getLogger(__name__)


async def search_youtube_videos(
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
    try:
        youtube_service = get_youtube_service()
        result = await youtube_service.search_videos(
            query=query,
            max_results=max_results,
            order=order,
            published_after=published_after,
            published_before=published_before,
            region_code=region_code,
            video_duration=video_duration,
            video_category_id=video_category_id,
            channel_id=channel_id,
            next_page_token=next_page_token
        )
        
        if result["success"]:
            logger.info(f"Successfully searched YouTube videos for query: {query}")
        else:
            logger.error(f"Failed to search YouTube videos: {result.get('error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"Error in search_youtube_videos: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to search videos: {str(e)}"
        }


async def get_youtube_video_details(video_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific YouTube video.
    
    Args:
        video_id: YouTube video ID (e.g., "dQw4w9WgXcQ")
    
    Returns:
        Dictionary containing:
        - success: Whether the request was successful
        - video: Video object with full metadata if found
        - error: Error message if unsuccessful
    """
    try:
        youtube_service = get_youtube_service()
        result = await youtube_service.get_video_by_id(video_id)
        
        if result["success"]:
            logger.info(f"Successfully fetched details for video: {video_id}")
        else:
            logger.error(f"Failed to get video details: {result.get('error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"Error in get_youtube_video_details: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get video details: {str(e)}"
        }


async def get_youtube_videos_batch_details(video_ids: List[str]) -> Dict[str, Any]:
    """Get detailed information for multiple YouTube videos in a single request.
    
    Args:
        video_ids: List of YouTube video IDs (e.g., ["dQw4w9WgXcQ", "jNQXAC9IVRw"])
                  Maximum 50 IDs per request
    
    Returns:
        Dictionary containing:
        - success: Whether the request was successful
        - videos: List of video objects with full metadata
        - error: Error message if unsuccessful
    """
    try:
        if not video_ids:
            return {
                "success": False,
                "error": "No video IDs provided"
            }
        
        if len(video_ids) > 50:
            logger.warning(f"Truncating video IDs list from {len(video_ids)} to 50 (API limit)")
            video_ids = video_ids[:50]
        
        youtube_service = get_youtube_service()
        # Access the internal method directly
        videos = await youtube_service._get_video_details(video_ids)
        
        return {
            "success": True,
            "videos": videos,
            "total_count": len(videos)
        }
        
    except Exception as e:
        logger.error(f"Error in get_youtube_videos_batch_details: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get batch video details: {str(e)}"
        }


async def get_youtube_trending_videos(
    region_code: str = "US",
    category_id: Optional[str] = None,
    max_results: int = 10,
    locale: Optional[str] = "en_US"
) -> Dict[str, Any]:
    """Get trending YouTube videos for a specific region.
    
    Args:
        region_code: ISO 3166-1 alpha-2 country code (default: "US")
                    Examples: "US", "UK", "CA", "AU", "DE", "FR", "JP", "BR"
        category_id: Optional YouTube category ID to filter by
                    (use get_youtube_categories to find category IDs)
        max_results: Maximum number of results (1-50, default: 10)
        locale: The locale for the API response (default: "en_US")
                Examples: "en_US", "es_ES", "pt_BR", "ja_JP"
    
    Returns:
        Dictionary containing:
        - success: Whether the request was successful
        - videos: List of trending video objects
        - region_code: The region code used
        - category_id: The category ID used (if any)
        - total_count: Number of videos returned
        - error: Error message if unsuccessful
    """
    try:
        youtube_service = get_youtube_service()
        result = await youtube_service.get_trending_videos(
            region_code=region_code,
            category_id=category_id,
            max_results=max_results,
            locale=locale
        )
        
        if result["success"]:
            logger.info(f"Successfully fetched trending videos for region: {region_code}")
        else:
            logger.error(f"Failed to get trending videos: {result.get('error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"Error in get_youtube_trending_videos: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get trending videos: {str(e)}"
        }