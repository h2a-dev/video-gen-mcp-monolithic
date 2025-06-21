"""Batch generate images from images tool implementation."""

import asyncio
from typing import Dict, Any, List, Optional
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


async def process_single_image(request: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Process a single image transformation request."""
    try:
        # Extract parameters with defaults
        image_url = request.get("image_url")
        prompt = request.get("prompt")
        guidance_scale = request.get("guidance_scale", 3.5)
        safety_tolerance = request.get("safety_tolerance", 5)
        project_id = request.get("project_id")
        scene_id = request.get("scene_id")
        
        # Validate required parameters
        if not image_url:
            return {
                "success": False,
                "index": index,
                "error": "image_url is required",
                "request": request
            }
        
        if not prompt:
            return {
                "success": False,
                "index": index,
                "error": "prompt is required",
                "request": request
            }
        
        # Validate and process image input
        image_validation = await process_image_input(image_url, fal_service)
        if not image_validation["valid"]:
            return {
                "success": False,
                "index": index,
                "error": image_validation["error_response"]["message"],
                "request": request
            }
        
        processed_image_url = image_validation["data"]
        
        # Validate guidance scale
        if not (1.0 <= guidance_scale <= 10.0):
            return {
                "success": False,
                "index": index,
                "error": f"Guidance scale must be between 1.0 and 10.0",
                "request": request
            }
        
        # Validate safety tolerance
        if not (1 <= safety_tolerance <= 6):
            return {
                "success": False,
                "index": index,
                "error": f"Safety tolerance must be between 1 and 6",
                "request": request
            }
        
        # Generate the transformed image
        result = await fal_service.generate_image_from_image(
            image_url=processed_image_url,
            prompt=prompt,
            model="flux_kontext",
            guidance_scale=guidance_scale,
            safety_tolerance=str(safety_tolerance)
        )
        
        if not result["success"]:
            return {
                "success": False,
                "index": index,
                "error": result.get("error", "Generation failed"),
                "request": request
            }
        
        # Calculate cost
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
                "safety_tolerance": safety_tolerance,
                "batch_index": index
            },
            generation_params={
                "image_url": processed_image_url,
                "prompt": prompt,
                "guidance_scale": guidance_scale,
                "safety_tolerance": str(safety_tolerance)
            }
        )
        
        # Handle project/scene association
        local_path = None
        if project_id and scene_id:
            project_validation = validate_project_exists(project_id, ProjectManager)
            if project_validation["valid"]:
                project = project_validation["project"]
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
                        local_path = download_result["local_path"]
                        asset.local_path = local_path
        
        return {
            "success": True,
            "index": index,
            "asset": {
                "id": asset.id,
                "url": asset.url,
                "type": asset.type,
                "cost": asset.cost,
                "local_path": local_path
            },
            "transformation_details": {
                "model": "flux_kontext",
                "source_image": image_url,
                "prompt": prompt,
                "guidance_scale": guidance_scale,
                "safety_tolerance": safety_tolerance
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "index": index,
            "error": str(e),
            "request": request
        }


async def generate_image_from_image_batch(
    requests: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Transform multiple images in parallel using AI.
    
    Args:
        requests: List of image transformation requests, each containing:
            - image_url: Source image URL or path (required)
            - prompt: Transformation description (required)
            - guidance_scale: How closely to follow prompt (default: 3.5)
            - safety_tolerance: Safety filter level (default: 5)
            - project_id: Optional project ID
            - scene_id: Optional scene ID
    
    Returns:
        Dict with results for all images
    """
    try:
        # Validate input
        if not requests or not isinstance(requests, list):
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "requests must be a non-empty list",
                details={"parameter": "requests"},
                suggestion="Provide a list of image transformation requests",
                example='generate_image_from_image_batch([{"image_url": "...", "prompt": "make it cinematic"}, ...])'
            )
        
        if len(requests) > 20:
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Maximum 20 images can be transformed in a single batch",
                details={"requested": len(requests), "maximum": 20},
                suggestion="Split your requests into smaller batches",
                example="Process in batches of 20 or fewer images"
            )
        
        # Process all images in parallel
        tasks = [
            process_single_image(request, index)
            for index, request in enumerate(requests)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Aggregate results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        total_cost = sum(
            r["asset"]["cost"] for r in successful
        )
        
        return {
            "success": True,
            "summary": {
                "total_requests": len(requests),
                "successful": len(successful),
                "failed": len(failed),
                "total_cost": round(total_cost, 3)
            },
            "results": results,
            "next_steps": [
                "Use the transformed images for video generation",
                "Download assets if needed",
                "Apply additional transformations if desired"
            ] if successful else [
                "Fix errors in failed requests",
                "Retry with corrected parameters"
            ]
        }
        
    except Exception as e:
        return create_error_response(
            ErrorType.SYSTEM_ERROR,
            f"Failed to process batch: {str(e)}",
            details={"error": str(e)},
            suggestion="Check your requests and try again",
            example='generate_image_from_image_batch([{"image_url": "...", "prompt": "..."}])'
        )