"""Generate image from text tool implementation."""

from typing import Dict, Any, Optional, List
from ...services import fal_service, asset_storage
from ...models import ProjectManager, Asset, AssetType, AssetSource
from ...config import calculate_image_cost


async def generate_image_from_text(
    prompt: str,
    model: str = "imagen4",
    aspect_ratio: str = "16:9",
    style_modifiers: Optional[List[str]] = None,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None
) -> Dict[str, Any]:
    """Generate an image from a text prompt."""
    try:
        # Enhance prompt with style modifiers
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
        return {
            "success": False,
            "error": str(e),
            "model": model
        }