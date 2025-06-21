"""Batch generate videos from images tool implementation."""

import asyncio
import time
from typing import Dict, Any, List, Optional
from ...services import fal_service, asset_storage
from ...models import ProjectManager, Asset, AssetType, AssetSource
from ...config import calculate_video_cost, settings
from ...utils import (
    create_error_response,
    ErrorType,
    validate_duration,
    validate_aspect_ratio,
    validate_range,
    validate_project_exists,
    handle_fal_api_error,
    process_image_input
)

# Valid aspect ratios for video generation
VALID_ASPECT_RATIOS = {
    "16:9": "Widescreen (YouTube, monitors)",
    "9:16": "Vertical (TikTok, Reels, mobile)",
    "1:1": "Square (Instagram posts)",
    "4:5": "Portrait (Instagram posts)"
}


async def process_single_video(request: Dict[str, Any], index: int, retry_count: int = 0) -> Dict[str, Any]:
    """Process a single video generation request with timeout handling."""
    start_time = time.time()
    
    try:
        # Extract parameters with defaults
        image_url = request.get("image_url")
        motion_prompt = request.get("motion_prompt")
        duration = request.get("duration", 6)
        aspect_ratio = request.get("aspect_ratio", "16:9")
        motion_strength = request.get("motion_strength", 0.7)
        model = request.get("model", settings.default_video_model)
        prompt_optimizer = request.get("prompt_optimizer", True)
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
        
        if not motion_prompt:
            return {
                "success": False,
                "index": index,
                "error": "motion_prompt is required",
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
        
        # Validate model
        if model not in ["kling_2.1", "hailuo_02"]:
            return {
                "success": False,
                "index": index,
                "error": f"Invalid model: {model}",
                "request": request
            }
        
        # Validate duration based on model
        if model == "kling_2.1":
            valid_durations = [5, 10]
        else:  # hailuo_02
            valid_durations = [6, 10]
        
        if duration not in valid_durations:
            return {
                "success": False,
                "index": index,
                "error": f"Invalid duration {duration} for model {model}. Valid: {valid_durations}",
                "request": request
            }
        
        # Validate aspect ratio
        if aspect_ratio not in VALID_ASPECT_RATIOS:
            return {
                "success": False,
                "index": index,
                "error": f"Invalid aspect ratio: {aspect_ratio}",
                "request": request
            }
        
        # Validate motion strength for Kling
        if model == "kling_2.1" and not (0.1 <= motion_strength <= 1.0):
            return {
                "success": False,
                "index": index,
                "error": f"Motion strength must be between 0.1 and 1.0",
                "request": request
            }
        
        # Generate the video
        kwargs = {
            "image_url": processed_image_url,
            "motion_prompt": motion_prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "model": model
        }
        
        if model == "kling_2.1":
            kwargs["motion_strength"] = motion_strength
        else:  # hailuo_02
            kwargs["prompt_optimizer"] = prompt_optimizer
        
        # Log start of video generation
        print(f"[Batch {index}] Starting video generation for {duration}s video")
        
        # Force polling for better queue management without webhooks
        kwargs['use_polling'] = True
        
        # Generate the video
        print(f"[Batch {index}] Submitting video generation request...")
        result = await fal_service.generate_video_from_image(**kwargs)
        
        if not result["success"]:
            elapsed = time.time() - start_time
            error_msg = result.get("error", "Generation failed")
            print(f"[Batch {index}] Failed after {elapsed:.1f}s: {error_msg}")
            
            # Retry once for failures
            if retry_count < 1 and "timeout" in error_msg.lower():
                print(f"[Batch {index}] Retrying video generation...")
                return await process_single_video(request, index, retry_count + 1)
            
            return {
                "success": False,
                "index": index,
                "error": error_msg,
                "request": request,
                "elapsed_time": elapsed
            }
        
        # Calculate cost
        cost = calculate_video_cost(model, duration)
        
        # Create asset record
        metadata = {
            "model": model,
            "source_image": image_url,
            "motion_prompt": motion_prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "batch_index": index
        }
        
        generation_params = {
            "image_url": image_url,
            "motion_prompt": motion_prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "model": model
        }
        
        if model == "kling_2.1":
            metadata["motion_strength"] = motion_strength
            generation_params["motion_strength"] = motion_strength
        else:
            metadata["prompt_optimizer"] = prompt_optimizer
            generation_params["prompt_optimizer"] = prompt_optimizer
        
        asset = Asset(
            type=AssetType.VIDEO,
            source=AssetSource.GENERATED,
            url=result["url"],
            cost=cost,
            metadata=metadata,
            generation_params=generation_params
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
                        local_path = download_result["local_path"]
                        asset.local_path = local_path
        
        elapsed = time.time() - start_time
        print(f"[Batch {index}] Video generation completed in {elapsed:.1f}s")
        
        return {
            "success": True,
            "index": index,
            "asset": {
                "id": asset.id,
                "url": asset.url,
                "type": asset.type,
                "cost": asset.cost,
                "duration": duration,
                "local_path": local_path
            },
            "generation_details": {
                "model": model,
                "motion_prompt": motion_prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "source_image": image_url
            },
            "elapsed_time": elapsed
        }
        
    except Exception as e:
        return {
            "success": False,
            "index": index,
            "error": str(e),
            "request": request
        }


async def generate_video_from_image_batch(
    requests: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate multiple videos from images in parallel.
    
    Args:
        requests: List of video generation requests, each containing:
            - image_url: Source image URL or path (required)
            - motion_prompt: Motion description (required)
            - duration: Video duration (default: 6)
            - aspect_ratio: Video aspect ratio (default: "16:9")
            - motion_strength: Motion intensity for Kling (default: 0.7)
            - model: Video model (default: from settings)
            - prompt_optimizer: For Hailuo model (default: True)
            - project_id: Optional project ID
            - scene_id: Optional scene ID
    
    Returns:
        Dict with results for all videos
    """
    try:
        # Validate input
        if not requests or not isinstance(requests, list):
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "requests must be a non-empty list",
                details={"parameter": "requests"},
                suggestion="Provide a list of video generation requests",
                example='generate_video_from_image_batch([{"image_url": "...", "motion_prompt": "..."}, ...])'
            )
        
        if len(requests) > 10:
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Maximum 10 videos can be generated in a single batch",
                details={"requested": len(requests), "maximum": 10},
                suggestion="Split your requests into smaller batches",
                example="Process in batches of 10 or fewer videos"
            )
        
        print(f"\n=== Starting batch video generation for {len(requests)} videos ===")
        
        # Process videos in smaller groups to avoid overwhelming the API
        batch_size = 5  # Process 5 videos at a time
        all_results = []
        
        for i in range(0, len(requests), batch_size):
            batch_end = min(i + batch_size, len(requests))
            batch = requests[i:batch_end]
            
            print(f"\nProcessing batch {i//batch_size + 1}/{(len(requests) + batch_size - 1)//batch_size} (videos {i}-{batch_end-1})")
            print(f"Submitting {len(batch)} videos to FAL queue...")
            
            # Create tasks for this batch
            tasks = [
                process_single_video(request, index)
                for index, request in enumerate(batch, start=i)
            ]
            
            # Process this batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    all_results.append({
                        "success": False,
                        "index": i + j,
                        "error": str(result),
                        "request": requests[i + j]
                    })
                else:
                    all_results.append(result)
            
            # Log batch completion
            print(f"Batch {i//batch_size + 1} completed. {len([r for r in batch_results if r.get('success')])} succeeded, {len([r for r in batch_results if not r.get('success')])} failed.")
            
            # Small delay between batches to avoid rate limiting
            if batch_end < len(requests):
                print("Waiting 2 seconds before next batch...")
                await asyncio.sleep(2)
        
        results = all_results
        
        # Aggregate results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        total_cost = sum(
            r["asset"]["cost"] for r in successful
        )
        
        total_duration = sum(
            r["asset"]["duration"] for r in successful
        )
        
        return {
            "success": True,
            "summary": {
                "total_requests": len(requests),
                "successful": len(successful),
                "failed": len(failed),
                "total_cost": round(total_cost, 3),
                "total_duration": total_duration
            },
            "results": results,
            "next_steps": [
                "Download assets if needed",
                "Use assemble_video() to combine all scenes",
                "Add audio tracks as needed"
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
            example='generate_video_from_image_batch([{"image_url": "...", "motion_prompt": "..."}])'
        )