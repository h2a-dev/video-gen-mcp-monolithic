"""Generate video from image tool implementation."""

from typing import Dict, Any, Optional
from ...services import fal_client, asset_storage
from ...models import ProjectManager, Asset, AssetType, AssetSource
from ...config import calculate_video_cost


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
        # Convert duration to int if it's passed as string
        if isinstance(duration, str):
            duration = int(duration)
        
        # Convert motion_strength to float if it's passed as string
        if isinstance(motion_strength, str):
            motion_strength = float(motion_strength)
        
        # Validate duration
        if duration not in [5, 10]:
            return {
                "success": False,
                "error": "Duration must be 5 or 10 seconds"
            }
        
        # Generate the video
        result = await fal_client.generate_video_from_image(
            image_url=image_url,
            motion_prompt=motion_prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            motion_strength=motion_strength
        )
        
        if not result["success"]:
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
        
        # If associated with a project/scene, add to it
        if project_id and scene_id:
            project = ProjectManager.get_project(project_id)
            scene = next((s for s in project.scenes if s.id == scene_id), None)
            if scene:
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
        return {
            "success": False,
            "error": str(e),
            "model": "kling_2.1"
        }