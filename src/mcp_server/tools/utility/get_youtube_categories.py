"""Get YouTube video categories tool implementation."""

from typing import Dict, Any, Optional
from ...services.youtube_service import get_youtube_service
from ...utils.error_helpers import create_error_response


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
        
    Example response:
        {
            "success": true,
            "region_code": "US",
            "language": "en_US",
            "total_count": 15,
            "categories": [
                {
                    "id": "1",
                    "title": "Film & Animation",
                    "assignable": true
                },
                {
                    "id": "10",
                    "title": "Music",
                    "assignable": true
                }
            ]
        }
    """
    try:
        # Default language based on region if not specified
        if language is None:
            language_map = {
                "US": "en_US",
                "UK": "en_GB",
                "CA": "en_CA",
                "AU": "en_AU",
                "DE": "de_DE",
                "FR": "fr_FR",
                "ES": "es_ES",
                "IT": "it_IT",
                "JP": "ja_JP",
                "KR": "ko_KR",
                "BR": "pt_BR",
                "MX": "es_MX",
                "IN": "hi_IN",
                "NL": "nl_NL",
                "PL": "pl_PL",
                "RU": "ru_RU",
                "SE": "sv_SE",
                "TR": "tr_TR",
                "ZA": "en_ZA"
            }
            language = language_map.get(region_code, "en_US")
        
        # Get YouTube service
        youtube_service = get_youtube_service()
        
        # Fetch categories
        result = await youtube_service.get_video_categories(
            region_code=region_code,
            hl=language
        )
        
        if not result["success"]:
            return create_error_response("API_ERROR", result.get("error", "Failed to fetch categories"))
        
        # Add helpful information
        result["usage_tips"] = [
            "Use category IDs when creating content for better YouTube optimization",
            "Not all categories may be assignable in all regions",
            "Gaming (20) and Entertainment (24) are popular choices for general content"
        ]
        
        # Add common category reference
        result["common_categories"] = {
            "entertainment": "24",
            "gaming": "20",
            "education": "27",
            "music": "10",
            "comedy": "23",
            "howto": "26",
            "tech": "28",
            "sports": "17"
        }
        
        return result
        
    except Exception as e:
        return create_error_response("API_ERROR", f"Error fetching YouTube categories: {str(e)}")