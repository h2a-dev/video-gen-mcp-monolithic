"""Generate video from image tool implementation."""

from typing import Dict, Any, Optional
from ...services import fal_service, asset_storage
from ...models import ProjectManager, Asset, AssetType, AssetSource
from ...config import calculate_video_cost
from ...utils import (
    create_error_response,
    ErrorType,
    validate_duration,
    validate_aspect_ratio,
    validate_range,
    validate_project_exists,
    handle_fal_api_error
)

# Valid aspect ratios for video generation
VALID_ASPECT_RATIOS = {
    "16:9": "Widescreen (YouTube, monitors)",
    "9:16": "Vertical (TikTok, Reels, mobile)",
    "1:1": "Square (Instagram posts)",
    "4:5": "Portrait (Instagram posts)"
}


async def generate_video_from_image(
    image_url: str,
    motion_prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    motion_strength: float = 0.7,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None
) -> Dict[str, Any]:
    """Convert a single image to video with AI-generated motion."""
    try:
        # Validate image URL
        if not image_url or not image_url.strip():
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Image URL cannot be empty",
                details={"parameter": "image_url"},
                suggestion="Provide a valid image URL or generate one first",
                example="generate_video_from_image(image_url='https://...', motion_prompt='Camera pans left')"
            )
        
        # Validate motion prompt
        if not motion_prompt or not motion_prompt.strip():
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Motion prompt cannot be empty",
                details={"parameter": "motion_prompt"},
                suggestion="Describe the motion you want to apply to the image",
                example="motion_prompt='Camera slowly zooms in while panning right'"
            )
        
        # Validate duration
        duration_validation = validate_duration(duration, valid_durations=[5, 10])
        if not duration_validation["valid"]:
            return duration_validation["error_response"]
        duration = duration_validation["value"]
        
        # Validate aspect ratio
        ratio_validation = validate_aspect_ratio(aspect_ratio, VALID_ASPECT_RATIOS)
        if not ratio_validation["valid"]:
            return ratio_validation["error_response"]
        
        # Validate motion strength
        strength_validation = validate_range(
            motion_strength, "motion_strength", 0.1, 1.0, "Motion strength"
        )
        if not strength_validation["valid"]:
            return strength_validation["error_response"]
        motion_strength = strength_validation["value"]
        
        # Generate the video
        result = await fal_service.generate_video_from_image(
            image_url=image_url,
            motion_prompt=motion_prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            motion_strength=motion_strength
        )
        
        if not result["success"]:
            # If it's an API error, provide helpful context
            if "error" in result:
                return handle_fal_api_error(Exception(result["error"]), "video generation")
            return result
        
        # Calculate cost
        cost = calculate_video_cost("kling_2.1", duration)
        
        # Create asset record
        asset = Asset(
            type=AssetType.VIDEO,
            source=AssetSource.GENERATED,
            url=result["url"],
            cost=cost,
            metadata={
                "model": "kling_2.1",
                "source_image": image_url,
                "motion_prompt": motion_prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "motion_strength": motion_strength
            },
            generation_params={
                "image_url": image_url,
                "motion_prompt": motion_prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "motion_strength": motion_strength
            }
        )
        
        # If associated with a project/scene, validate and add to it
        if project_id:
            project_validation = validate_project_exists(project_id, ProjectManager)
            if not project_validation["valid"]:
                return project_validation["error_response"]
            
            project = project_validation["project"]
            
            if scene_id:
                scene = next((s for s in project.scenes if s.id == scene_id), None)
                if not scene:
                    return create_error_response(
                        ErrorType.RESOURCE_NOT_FOUND,
                        f"Scene not found in project: {scene_id}",
                        details={"project_id": project_id, "scene_id": scene_id},
                        suggestion="Use add_scene() to create a scene first",
                        example=f"add_scene(project_id='{project_id}', description='Scene description', duration={duration})"
                    )
                # Update scene duration if needed
                if scene.duration != duration:
                    scene.duration = duration
                
                scene.assets.append(asset)
                project.total_cost = project.calculate_cost()
                project.actual_duration = project.calculate_duration()
                project.updated_at = asset.created_at
                
                # Download the asset
                download_result = await asset_storage.download_asset(
                    url=result["url"],
                    project_id=project_id,
                    asset_id=asset.id,
                    asset_type="video"
                )
                if download_result["success"]:
                    asset.local_path = download_result["local_path"]
        
        return {
            "success": True,
            "asset": {
                "id": asset.id,
                "url": asset.url,
                "type": asset.type,
                "cost": asset.cost,
                "duration": duration,
                "local_path": asset.local_path
            },
            "generation_details": {
                "model": "kling_2.1",
                "motion_prompt": motion_prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "source_image": image_url
            },
            "project_association": {
                "project_id": project_id,
                "scene_id": scene_id
            } if project_id else None,
            "next_steps": [
                "Add more scenes to your project",
                "Generate audio: generate_music() or generate_speech()",
                "When ready: assemble_video() to combine all scenes"
            ]
        }
        
    except Exception as e:
        # Check if it's an API error
        if "fal" in str(e).lower() or "api" in str(e).lower():
            return handle_fal_api_error(e, "video generation")
        
        # Check for specific error patterns
        error_str = str(e).lower()
        if "invalid url" in error_str or "url" in error_str:
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Invalid image URL provided",
                details={"image_url": image_url, "error": str(e)},
                suggestion="Ensure the image URL is accessible and points to a valid image file",
                example="Use a direct image URL like: https://example.com/image.jpg"
            )
        
        # Generic error with helpful context
        return create_error_response(
            ErrorType.SYSTEM_ERROR,
            f"Failed to generate video: {str(e)}",
            details={"model": "kling_2.1", "error": str(e)},
            suggestion="Check your image URL and motion prompt, then try again",
            example="generate_video_from_image(image_url='...', motion_prompt='Simple zoom in', duration=5)"
        )