"""Generate image from image tool implementation."""

from typing import Dict, Any, Optional
from ...services import fal_service, asset_storage
from ...models import ProjectManager, Asset, AssetType, AssetSource
from ...config import calculate_image_cost
from ...utils import (
    create_error_response,
    ErrorType,
    validate_range,
    validate_project_exists,
    handle_fal_api_error,
    process_image_input
)


async def generate_image_from_image(
    image_url: str,
    prompt: str,
    safety_tolerance: int = 3,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transform an image based on a text prompt using AI.
    Uses Flux Kontext with fixed guidance scale of 3.5 for optimal results.
    
    Args:
        image_url: Source image - can be a URL or local file path
        prompt: Text description of the transformation to apply
        guidance_scale: How closely to follow the prompt (1.0-10.0, default 3.5)
        safety_tolerance: Safety filter level (1-6, default 3. 1=strictest, 6=most permissive)
        project_id: Optional project to associate the image with
        scene_id: Optional scene within the project
        
    Returns:
        Dict with transformed image results
    """
    try:
        # Validate and process image input (URL or file path)
        image_validation = await process_image_input(image_url, fal_service)
        if not image_validation["valid"]:
            return image_validation["error_response"]
        
        # Use the processed image URL (original or uploaded)
        processed_image_url = image_validation["data"]
        
        # Validate prompt
        if not prompt or not prompt.strip():
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Prompt cannot be empty",
                details={"parameter": "prompt"},
                suggestion="Describe the transformation you want to apply to the image",
                example="prompt='Make it more vibrant and colorful'"
            )
        
        # Fixed guidance scale for optimal results
        guidance_scale = 3.5
        
        # Validate safety tolerance
        safety_validation = validate_range(
            safety_tolerance, "safety_tolerance", 1, 6, "Safety tolerance"
        )
        if not safety_validation["valid"]:
            return safety_validation["error_response"]
        safety_tolerance = safety_validation["value"]
        
        # Validate project exists if provided
        if project_id:
            project_validation = validate_project_exists(project_id, ProjectManager)
            if not project_validation["valid"]:
                return project_validation["error_response"]
            
            # Validate scene exists if provided
            if scene_id:
                project = project_validation["project"]
                scene = next((s for s in project.scenes if s.id == scene_id), None)
                if not scene:
                    return create_error_response(
                        ErrorType.RESOURCE_NOT_FOUND,
                        f"Scene not found in project: {scene_id}",
                        details={"project_id": project_id, "scene_id": scene_id},
                        suggestion="Use add_scene() to create a scene first",
                        example=f"add_scene(project_id='{project_id}', description='Scene description', duration=10)"
                    )
        
        # Generate the transformed image
        result = await fal_service.generate_image_from_image(
            image_url=processed_image_url,
            prompt=prompt,
            model="flux_kontext",
            guidance_scale=guidance_scale,
            safety_tolerance=str(safety_tolerance)  # API expects string
        )
        
        if not result["success"]:
            # If it's an API error, provide helpful context
            if "error" in result:
                return handle_fal_api_error(Exception(result["error"]), "image transformation")
            return result
        
        # Calculate cost (using flux_pro pricing as flux_kontext is similar)
        cost = calculate_image_cost("flux_pro")
        
        # Create asset record
        asset = Asset(
            type=AssetType.IMAGE,
            source=AssetSource.GENERATED,
            url=result["url"],
            cost=cost,
            metadata={
                "model": "flux_kontext",
                "source_image": image_url,
                "prompt": prompt,
                "guidance_scale": guidance_scale,
                "safety_tolerance": safety_tolerance
            },
            generation_params={
                "image_url": processed_image_url,
                "prompt": prompt,
                "guidance_scale": guidance_scale,
                "safety_tolerance": str(safety_tolerance)
            }
        )
        
        # If associated with a project/scene, add to it
        if project_id and scene_id:
            project = ProjectManager.get_project(project_id)
            scene = next((s for s in project.scenes if s.id == scene_id), None)
            if scene:
                scene.assets.append(asset)
                project.total_cost = project.calculate_cost()
                project.updated_at = asset.created_at
                
                # Download the asset
                download_result = await asset_storage.download_asset(
                    url=result["url"],
                    project_id=project_id,
                    asset_id=asset.id,
                    asset_type="image"
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
                "local_path": asset.local_path
            },
            "transformation_details": {
                "model": "flux_kontext",
                "source_image": image_url,
                "prompt": prompt,
                "guidance_scale": guidance_scale,
                "safety_tolerance": safety_tolerance
            },
            "project_association": {
                "project_id": project_id,
                "scene_id": scene_id
            } if project_id else None,
            "next_steps": [
                f"Animate this image: generate_video_from_image('{asset.url}', 'motion prompt', return_queue_id=True)",
                "For character consistency: Use this tool for ALL scenes with the same character",
                "Batch transform multiple scenes: Use the same reference image with different prompts",
                "Monitor all transformations: get_queue_status(project_id=project_id)"
            ]
        }
        
    except Exception as e:
        # Check if it's an API error
        if "fal" in str(e).lower() or "api" in str(e).lower():
            return handle_fal_api_error(e, "image transformation")
        
        # Generic error with helpful context
        return create_error_response(
            ErrorType.SYSTEM_ERROR,
            f"Failed to transform image: {str(e)}",
            details={"model": "flux_kontext", "error": str(e)},
            suggestion="Check your image URL and prompt, then try again",
            example="generate_image_from_image(image_url='...', prompt='Make it more artistic')"
        )