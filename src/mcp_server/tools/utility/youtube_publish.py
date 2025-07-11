"""Tool for publishing videos to YouTube."""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from ...services.youtube_service import get_youtube_service
from ...config.settings import settings
from ...utils.error_helpers import create_error_response, ErrorType
import logging

logger = logging.getLogger(__name__)


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
        tags: List of tags/keywords for the video (optional) - accepts list or JSON array string
        category_id: YouTube category ID (default: 22 - People & Blogs)
                    Common categories:
                    - 1: Film & Animation
                    - 2: Autos & Vehicles
                    - 10: Music
                    - 15: Pets & Animals
                    - 17: Sports
                    - 19: Travel & Events
                    - 20: Gaming
                    - 22: People & Blogs
                    - 23: Comedy
                    - 24: Entertainment
                    - 25: News & Politics
                    - 26: Howto & Style
                    - 27: Education
                    - 28: Science & Technology
        privacy_status: Privacy setting - 'public', 'private', or 'unlisted' (default: private)
        notify_subscribers: Whether to notify channel subscribers (default: true)
        use_hashtag_shorts: Auto-append #Shorts to title/description for short videos (default: true)
    
    Returns:
        Success: { 
            success: true, 
            video_id: str,
            video_url: str,
            title: str,
            privacy_status: str,
            auto_added_shorts: bool
        }
        Error: { success: false, error: message }
    
    Note:
        - Requires YouTube API authentication (will prompt for OAuth on first use)
        - Client secrets must be configured at 'client_secrets.json'
        - Videos under 60 seconds will automatically be tagged as Shorts if use_hashtag_shorts=true
        - Upload quotas apply based on YouTube API limits
    """
    try:
        # Handle tags parameter - accept both list and JSON string
        if tags is not None:
            if isinstance(tags, str):
                try:
                    # Try to parse as JSON string
                    tags = json.loads(tags)
                    if not isinstance(tags, list):
                        return create_error_response(
                            ErrorType.INPUT_ERROR,
                            "Tags must be a list of strings"
                        )
                except json.JSONDecodeError:
                    # If not valid JSON, treat as single tag
                    tags = [tags]
            elif not isinstance(tags, list):
                return create_error_response(
                    ErrorType.INPUT_ERROR,
                    "Tags must be a list of strings or a JSON array string"
                )
        
        # Load project from in-memory storage
        from ...models import ProjectManager
        
        try:
            project = ProjectManager.get_project(project_id)
        except ValueError as e:
            return create_error_response(
                ErrorType.RESOURCE_NOT_FOUND,
                f"Project {project_id} not found"
            )
        except Exception as e:
            return create_error_response(
                ErrorType.SYSTEM_ERROR,
                f"Failed to load project: {str(e)}"
            )
        
        # Get project directory for video file lookup
        project_dir = settings.projects_dir / project_id
        
        # Find the video file using the same naming convention as assemble_video
        video_path = None
        
        # First try the standard naming convention from assemble_video
        standard_filename = f"{project.title.replace(' ', '_')}_{project.platform}.mp4"
        standard_path = project_dir / standard_filename
        if standard_path.exists():
            video_path = str(standard_path)
        else:
            # Check for other video files in the project directory
            video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
            for ext in video_extensions:
                # Try the standard naming pattern with different extensions
                potential_path = project_dir / f"{project.title.replace(' ', '_')}_{project.platform}{ext}"
                if potential_path.exists():
                    video_path = str(potential_path)
                    break
        
        if not video_path:
            return create_error_response(
                ErrorType.RESOURCE_NOT_FOUND,
                "No video file found for project. Please assemble the video first."
            )
        
        # Auto-add #Shorts for short videos
        auto_added_shorts = False
        project_duration = project.calculate_duration()
        if use_hashtag_shorts and project_duration and project_duration <= 60:
            if "#shorts" not in title.lower() and "#short" not in title.lower():
                if len(title) + 8 <= 100:  # YouTube title limit
                    title = f"{title} #Shorts"
                    auto_added_shorts = True
                elif "#shorts" not in description.lower() and "#short" not in description.lower():
                    description = f"{description}\n\n#Shorts" if description else "#Shorts"
                    auto_added_shorts = True
        
        # Get YouTube service and upload
        youtube_service = get_youtube_service()
        
        logger.info(f"Uploading video to YouTube: {video_path}")
        logger.info(f"Title: {title}")
        logger.info(f"Privacy: {privacy_status}")
        
        result = await youtube_service.upload_video(
            file_path=video_path,
            title=title,
            description=description,
            tags=tags,
            category_id=category_id,
            privacy_status=privacy_status,
            notify_subscribers=notify_subscribers
        )
        
        if result["success"]:
            # Update project with YouTube video ID
            if hasattr(project, 'metadata') and project.metadata:
                project.metadata['youtube_video_id'] = result['video_id']
                project.metadata['youtube_url'] = result['video_url']
            else:
                project.metadata = {
                    'youtube_video_id': result['video_id'],
                    'youtube_url': result['video_url']
                }
            
            # Update the in-memory project
            project.updated_at = datetime.now()
            ProjectManager.update_project(project_id, metadata=project.metadata)
            
            return {
                "success": True,
                "video_id": result["video_id"],
                "video_url": result["video_url"],
                "title": title,
                "privacy_status": privacy_status,
                "auto_added_shorts": auto_added_shorts,
                "message": f"Video published successfully to YouTube"
            }
        else:
            return result
            
    except Exception as e:
        logger.error(f"Error publishing to YouTube: {str(e)}")
        return create_error_response(
            ErrorType.SYSTEM_ERROR,
            f"Failed to publish video: {str(e)}"
        )