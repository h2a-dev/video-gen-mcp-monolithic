"""Generate image from text tool implementation."""

from typing import Dict, Any, Optional, List
from ...services import fal_service, asset_storage
from ...models import ProjectManager, Asset, AssetType, AssetSource
from ...config import calculate_image_cost
from ...utils import (
    create_error_response,
    ErrorType,
    validate_aspect_ratio,
    validate_enum,
    validate_project_exists,
    handle_fal_api_error
)
from ...utils.cinematic_prompts import create_cinematic_image_prompt


# Valid models and aspect ratios
VALID_MODELS = {
    "imagen4": "Google Imagen 4 - High quality, fast generation",
    "flux_pro": "FLUX Pro - Creative and artistic styles"
}

VALID_ASPECT_RATIOS = {
    "16:9": "Widescreen (YouTube, monitors)",
    "9:16": "Vertical (TikTok, Reels, mobile)",
    "1:1": "Square (Instagram posts)",
    "4:5": "Portrait (Instagram posts)",
    "3:2": "Classic photo format",
    "2:3": "Vertical photo format"
}


async def generate_image_from_text(
    prompt: str,
    model: str = "imagen4",
    aspect_ratio: str = "16:9",
    style_modifiers: Optional[List[str]] = None,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None
) -> Dict[str, Any]:
    """Generate an image from a text prompt.
    
    Args:
        prompt: Text description of the image to generate
        model: AI model to use (imagen4 or flux_pro)
        aspect_ratio: Image aspect ratio (16:9, 9:16, 1:1, etc.)
        style_modifiers: Optional style keywords to enhance the prompt
        project_id: Optional project to associate the image with
        scene_id: Optional scene within the project
    """
    try:
        # Validate prompt
        if not prompt or not prompt.strip():
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Prompt cannot be empty",
                details={"parameter": "prompt"},
                suggestion="Provide a descriptive text prompt for the image",
                example="generate_image_from_text(prompt='A serene mountain landscape at sunset')"
            )
        
        # Validate model
        model_validation = validate_enum(model, "model", list(VALID_MODELS.keys()), "image model")
        if not model_validation["valid"]:
            model_validation["error_response"]["valid_options"] = VALID_MODELS
            return model_validation["error_response"]
        
        # Validate aspect ratio
        ratio_validation = validate_aspect_ratio(aspect_ratio, VALID_ASPECT_RATIOS)
        if not ratio_validation["valid"]:
            return ratio_validation["error_response"]
        
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
        # Check if we should apply cinematic enhancement
        if project_id and scene_id and project:
            # Get scene position for cinematic enhancement
            scene_index = next((i for i, s in enumerate(project.scenes) if s.id == scene_id), 0)
            total_scenes = len(project.scenes)
            
            # Apply cinematic enhancement
            enhanced_prompt = create_cinematic_image_prompt(
                prompt,
                scene_number=scene_index + 1,
                total_scenes=total_scenes,
                platform=project.platform
            )
            
            # Add style modifiers if provided
            if style_modifiers:
                enhanced_prompt = f"{enhanced_prompt}, {', '.join(style_modifiers)}"
        else:
            # Standard enhancement for non-project images
            enhanced_prompt = prompt
            if style_modifiers:
                enhanced_prompt = f"{prompt}, {', '.join(style_modifiers)}"
        
        # Generate the image
        result = await fal_service.generate_image_from_text(
            prompt=enhanced_prompt,
            model=model,
            aspect_ratio=aspect_ratio
        )
        
        if not result["success"]:
            # If it's an API error, provide helpful context
            if "error" in result:
                return handle_fal_api_error(Exception(result["error"]), "image generation")
            return result
        
        # Calculate cost
        cost = calculate_image_cost(model)
        
        # Create asset record
        asset = Asset(
            type=AssetType.IMAGE,
            source=AssetSource.GENERATED,
            url=result["url"],
            cost=cost,
            metadata={
                "model": model,
                "prompt": enhanced_prompt,
                "aspect_ratio": aspect_ratio,
                "original_prompt": prompt,
                "style_modifiers": style_modifiers
            },
            generation_params={
                "prompt": enhanced_prompt,
                "model": model,
                "aspect_ratio": aspect_ratio
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
            "generation_details": {
                "model": model,
                "prompt": enhanced_prompt,
                "aspect_ratio": aspect_ratio
            },
            "project_association": {
                "project_id": project_id,
                "scene_id": scene_id
            } if project_id else None,
            "next_steps": [
                f"Animate this image: generate_video_from_image('{asset.url}', 'your motion prompt')",
                "Edit the image: generate_image_from_image() with modifications",
                "Use in multi-image composition: generate_image_from_images()"
            ]
        }
        
    except Exception as e:
        # Check if it's an API error
        if "fal" in str(e).lower() or "api" in str(e).lower():
            return handle_fal_api_error(e, "image generation")
        
        # Generic error with helpful context
        return create_error_response(
            ErrorType.SYSTEM_ERROR,
            f"Failed to generate image: {str(e)}",
            details={"model": model, "error": str(e)},
            suggestion="Check your prompt and try again with simpler parameters",
            example="generate_image_from_text(prompt='Simple landscape', model='imagen4')"
        )