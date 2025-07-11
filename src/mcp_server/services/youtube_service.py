"""YouTube API service for fetching video categories, searching videos, and uploading videos."""

import os
import random
import time
import json
import http.client
import httplib2
from typing import Dict, Any, List, Optional, Tuple
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Upload retry settings
httplib2.RETRIES = 1
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
                        http.client.IncompleteRead, http.client.ImproperConnectionState,
                        http.client.CannotSendRequest, http.client.CannotSendHeader,
                        http.client.ResponseNotReady, http.client.BadStatusLine)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# OAuth 2.0 settings
CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

@dataclass
class YouTubeVideo:
    """Represents a YouTube video with metadata."""
    video_id: str
    title: str
    description: str
    channel_id: str
    channel_title: str
    published_at: str
    duration: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    tags: List[str] = None


class YouTubeService:
    """Service for interacting with YouTube Data API v3."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize YouTube service with API key."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("YOUTUBE_API_KEY")
        # API key is optional - only required for search/categories functionality
        # Upload functionality uses OAuth2 authentication instead
        
        # Only build the service if we have an API key (for search functionality)
        self.youtube = None
        if self.api_key:
            self.youtube = build("youtube", "v3", developerKey=self.api_key)
        self._categories_cache: Dict[str, List[Dict[str, Any]]] = {}
    
    async def get_video_categories(
        self, 
        region_code: str = "US",
        hl: str = "en_US"
    ) -> Dict[str, Any]:
        """
        Fetch YouTube video categories for a specific region.
        
        Args:
            region_code: ISO 3166-1 alpha-2 country code (e.g., "US", "UK", "CA")
            hl: Language code for category names (e.g., "en_US", "es_ES")
            
        Returns:
            Dict containing categories list and metadata
        """
        cache_key = f"{region_code}_{hl}"
        
        # Check cache first
        if cache_key in self._categories_cache:
            logger.info(f"Returning cached categories for {cache_key}")
            return {
                "success": True,
                "region_code": region_code,
                "language": hl,
                "categories": self._categories_cache[cache_key],
                "from_cache": True
            }
        
        try:
            # Check if API key is available
            if not self.youtube:
                return {
                    "success": False,
                    "error": "YouTube API key not configured. Set GOOGLE_API_KEY or YOUTUBE_API_KEY environment variable."
                }
            
            # Make API request
            request = self.youtube.videoCategories().list(
                part="snippet",
                regionCode=region_code,
                hl=hl
            )
            response = request.execute()
            
            # Process categories
            categories = []
            for item in response.get("items", []):
                category = {
                    "id": item["id"],
                    "title": item["snippet"]["title"],
                    "channel_id": item["snippet"]["channelId"],
                    "assignable": item["snippet"].get("assignable", True)
                }
                categories.append(category)
            
            # Sort by title for consistency
            categories.sort(key=lambda x: x["title"])
            
            # Cache the results
            self._categories_cache[cache_key] = categories
            
            return {
                "success": True,
                "region_code": region_code,
                "language": hl,
                "categories": categories,
                "total_count": len(categories),
                "from_cache": False
            }
            
        except HttpError as e:
            error_message = f"YouTube API error: {e.content.decode('utf-8')}"
            logger.error(error_message)
            
            # Check for specific error types
            if e.resp.status == 403:
                error_message = "API quota exceeded or invalid API key"
            elif e.resp.status == 404:
                error_message = f"No categories found for region: {region_code}"
            
            return {
                "success": False,
                "error": error_message,
                "error_code": e.resp.status
            }
            
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logger.error(error_message)
            return {
                "success": False,
                "error": error_message
            }
    
    def clear_cache(self):
        """Clear the categories cache."""
        self._categories_cache.clear()
        logger.info("YouTube categories cache cleared")
    
    async def search_videos(
        self,
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
        """Search for YouTube videos based on query and filters.
        
        Args:
            query: Search query string
            max_results: Maximum number of results (1-50, default: 10)
            order: Sort order (relevance, date, rating, title, viewCount, default: relevance)
            published_after: RFC 3339 datetime string for minimum publish date
            published_before: RFC 3339 datetime string for maximum publish date
            region_code: ISO 3166-1 alpha-2 country code
            video_duration: Duration filter (short: <4min, medium: 4-20min, long: >20min)
            video_category_id: YouTube category ID
            channel_id: Filter by specific channel
            next_page_token: Token for pagination
            
        Returns:
            Dictionary containing videos list and pagination info
        """
        try:
            # Check if API key is available
            if not self.youtube:
                return {
                    "success": False,
                    "error": "YouTube API key not configured. Set GOOGLE_API_KEY or YOUTUBE_API_KEY environment variable."
                }
            
            search_params = {
                "q": query,
                "part": "snippet",
                "type": "video",
                "maxResults": min(max_results, 50),
                "order": order
            }
            
            if published_after:
                search_params["publishedAfter"] = published_after
            if published_before:
                search_params["publishedBefore"] = published_before
            if region_code:
                search_params["regionCode"] = region_code
            if video_duration:
                search_params["videoDuration"] = video_duration
            if video_category_id:
                search_params["videoCategoryId"] = video_category_id
            if channel_id:
                search_params["channelId"] = channel_id
            if next_page_token:
                search_params["pageToken"] = next_page_token
            
            search_response = self.youtube.search().list(**search_params).execute()
            
            video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
            
            videos = []
            if video_ids:
                videos = await self._get_video_details(video_ids)
            
            return {
                "success": True,
                "videos": videos,
                "total_results": search_response.get("pageInfo", {}).get("totalResults", 0),
                "results_per_page": search_response.get("pageInfo", {}).get("resultsPerPage", 0),
                "next_page_token": search_response.get("nextPageToken"),
                "prev_page_token": search_response.get("prevPageToken")
            }
            
        except HttpError as e:
            error_details = e.error_details[0] if e.error_details else {}
            logger.error(f"YouTube API error: {error_details.get('message', str(e))}")
            return {
                "success": False,
                "error": f"YouTube API error: {error_details.get('message', str(e))}",
                "error_code": e.resp.status
            }
        except Exception as e:
            logger.error(f"Unexpected error in search_videos: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def get_video_by_id(self, video_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary with video data or error info
        """
        try:
            videos = await self._get_video_details([video_id])
            if videos:
                return {
                    "success": True,
                    "video": videos[0]
                }
            else:
                return {
                    "success": False,
                    "error": "Video not found"
                }
        except Exception as e:
            logger.error(f"Error getting video by ID: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_trending_videos(
        self,
        region_code: str = "US",
        category_id: Optional[str] = "42",
        max_results: int = 10,
        locale: Optional[str] = "en_US"
    ) -> Dict[str, Any]:
        """Get trending videos for a specific region.
        
        Args:
            region_code: ISO 3166-1 alpha-2 country code (default: US)
            category_id: YouTube category ID (default: 42 for Shorts)
            max_results: Maximum number of results (1-50, default: 10)
            locale: The locale for the API response (default: en_US)
            
        Returns:
            Dictionary with trending videos or error info
        """
        try:
            # Check if API key is available
            if not self.youtube:
                return {
                    "success": False,
                    "error": "YouTube API key not configured. Set GOOGLE_API_KEY or YOUTUBE_API_KEY environment variable."
                }
            
            params = {
                "part": "snippet,contentDetails,statistics",
                "chart": "mostPopular",
                "regionCode": region_code,
                "maxResults": min(max_results, 50)
            }
            
            if locale:
                params["hl"] = locale
            
            if category_id:
                params["videoCategoryId"] = category_id
            
            response = self.youtube.videos().list(**params).execute()
            
            videos = []
            for item in response.get("items", []):
                video = self._parse_video_response(item)
                if video:
                    videos.append(video)
            
            return {
                "success": True,
                "videos": videos,
                "region_code": region_code,
                "category_id": category_id,
                "total_count": len(videos)
            }
            
        except HttpError as e:
            error_details = e.error_details[0] if e.error_details else {}
            logger.error(f"YouTube API error: {error_details.get('message', str(e))}")
            return {
                "success": False,
                "error": f"YouTube API error: {error_details.get('message', str(e))}",
                "error_code": e.resp.status
            }
        except Exception as e:
            logger.error(f"Error getting trending videos: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_video_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed information for multiple videos.
        
        Args:
            video_ids: List of YouTube video IDs
            
        Returns:
            List of video dictionaries
        """
        if not video_ids:
            return []
        
        try:
            # Check if API key is available
            if not self.youtube:
                raise ValueError("YouTube API key not configured")
            
            videos_response = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=",".join(video_ids)
            ).execute()
            
            videos = []
            for item in videos_response.get("items", []):
                video = self._parse_video_response(item)
                if video:
                    videos.append(video)
            
            return videos
            
        except HttpError as e:
            error_details = e.error_details[0] if e.error_details else {}
            logger.error(f"YouTube API error in _get_video_details: {error_details.get('message', str(e))}")
            raise
    
    def _parse_video_response(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse YouTube API response into video dictionary.
        
        Args:
            item: Single video item from YouTube API response
            
        Returns:
            Video dictionary or None if parsing fails
        """
        try:
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})
            
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = None
            if "maxres" in thumbnails:
                thumbnail_url = thumbnails["maxres"]["url"]
            elif "high" in thumbnails:
                thumbnail_url = thumbnails["high"]["url"]
            elif "medium" in thumbnails:
                thumbnail_url = thumbnails["medium"]["url"]
            
            return {
                "video_id": item["id"],
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel_id": snippet.get("channelId", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt", ""),
                "duration": content_details.get("duration"),
                "view_count": int(statistics.get("viewCount", 0)),
                "like_count": int(statistics.get("likeCount", 0)),
                "comment_count": int(statistics.get("commentCount", 0)),
                "thumbnail_url": thumbnail_url,
                "tags": snippet.get("tags", [])
            }
        except Exception as e:
            logger.error(f"Error parsing video response: {str(e)}")
            return None
    
    def get_authenticated_service_for_upload(self) -> Any:
        """Get authenticated YouTube service for upload operations.
        
        Returns:
            Authenticated YouTube API service object
        """
        credentials = None
        token_path = 'token.json'
        
        if os.path.exists(token_path):
            credentials = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # Check if credentials are invalid or do not exist
        if not credentials or not credentials.valid:
            # If the credentials are invalid, refresh them
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                if not os.path.exists(CLIENT_SECRETS_FILE):
                    raise FileNotFoundError(f"Client secrets file '{CLIENT_SECRETS_FILE}' not found")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRETS_FILE, SCOPES)
                credentials = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(credentials.to_json())
        
        return build('youtube', 'v3', credentials=credentials)
    
    async def upload_video(
        self,
        file_path: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        category_id: str = "22",
        privacy_status: str = "private",
        notify_subscribers: bool = True
    ) -> Dict[str, Any]:
        """Upload a video to YouTube.
        
        Args:
            file_path: Path to the video file
            title: Video title
            description: Video description
            tags: List of video tags
            category_id: YouTube category ID (default: 22 - People & Blogs)
            privacy_status: Privacy status (public, private, unlisted)
            notify_subscribers: Whether to notify channel subscribers
            
        Returns:
            Dictionary with upload result
        """
        if privacy_status not in VALID_PRIVACY_STATUSES:
            return {
                "success": False,
                "error": f"Invalid privacy status. Must be one of: {', '.join(VALID_PRIVACY_STATUSES)}"
            }
        
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"Video file not found: {file_path}"
            }
        
        try:
            youtube = self.get_authenticated_service_for_upload()
            
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags or [],
                    "categoryId": category_id
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False,
                    "notifySubscribers": notify_subscribers
                }
            }
            
            # Create media upload object
            media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
            
            # Create the insert request
            insert_request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media
            )
            
            # Execute the upload
            response = self._resumable_upload(insert_request)
            
            if response and 'id' in response:
                video_url = f"https://www.youtube.com/watch?v={response['id']}"
                logger.info(f"Video uploaded successfully: {video_url}")
                return {
                    "success": True,
                    "video_id": response['id'],
                    "video_url": video_url,
                    "title": title,
                    "privacy_status": privacy_status
                }
            else:
                return {
                    "success": False,
                    "error": "Upload failed: No video ID in response"
                }
                
        except HttpError as e:
            error_message = f"YouTube API error: {e.content.decode('utf-8')}"
            logger.error(error_message)
            
            if e.resp.status == 403:
                error_message = "Upload quota exceeded or insufficient permissions"
            elif e.resp.status == 400:
                error_message = "Invalid request parameters"
            
            return {
                "success": False,
                "error": error_message,
                "error_code": e.resp.status
            }
            
        except Exception as e:
            error_message = f"Upload error: {str(e)}"
            logger.error(error_message)
            return {
                "success": False,
                "error": error_message
            }
    
    def _resumable_upload(self, request) -> Optional[Dict[str, Any]]:
        """Handle resumable upload with retry logic.
        
        Args:
            request: YouTube API upload request
            
        Returns:
            Response dict or None if failed
        """
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                logger.info("Uploading video...")
                status, response = request.next_chunk()
                
                if response is not None:
                    if 'id' in response:
                        logger.info(f"Video uploaded successfully with ID: {response['id']}")
                        return response
                    else:
                        logger.error(f"Unexpected response: {response}")
                        return None
                        
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = f"Retriable HTTP error {e.resp.status}: {e.content}"
                else:
                    raise
                    
            except RETRIABLE_EXCEPTIONS as e:
                error = f"Retriable error: {e}"
            
            if error is not None:
                logger.warning(error)
                retry += 1
                
                if retry > MAX_RETRIES:
                    logger.error("Max retries exceeded")
                    return None
                
                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                logger.info(f"Sleeping {sleep_seconds:.2f} seconds before retry...")
                time.sleep(sleep_seconds)
                error = None
        
        return response


# Singleton instance
_youtube_service: Optional[YouTubeService] = None


def get_youtube_service() -> YouTubeService:
    """Get or create the YouTube service singleton."""
    global _youtube_service
    if _youtube_service is None:
        _youtube_service = YouTubeService()
    return _youtube_service