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
import fal_client

# Valid aspect ratios for video generation
VALID_ASPECT_RATIOS = {
    "16:9": "Widescreen (YouTube, monitors)",
    "9:16": "Vertical (TikTok, Reels, mobile)",
    "1:1": "Square (Instagram posts)",
    "4:5": "Portrait (Instagram posts)"
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
        
        # Step 1: Submit all jobs to FAL queue
        print("\nStep 1: Submitting all jobs to FAL queue...")
        submissions = []
        
        for index, request in enumerate(requests):
            try:
                # Validate and process request
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
                    submissions.append({
                        "success": False,
                        "index": index,
                        "error": "image_url is required",
                        "request": request
                    })
                    continue
                
                if not motion_prompt:
                    submissions.append({
                        "success": False,
                        "index": index,
                        "error": "motion_prompt is required",
                        "request": request
                    })
                    continue
                
                # Validate and process image input
                image_validation = await process_image_input(image_url, fal_service)
                if not image_validation["valid"]:
                    submissions.append({
                        "success": False,
                        "index": index,
                        "error": image_validation["error_response"]["message"],
                        "request": request
                    })
                    continue
                
                processed_image_url = image_validation["data"]
                
                # Prepare arguments based on model
                if model == "kling_2.1":
                    model_id = "fal-ai/kling-video/v2.1/standard/image-to-video"
                    arguments = {
                        "prompt": motion_prompt,
                        "image_url": processed_image_url,
                        "duration": str(duration),
                        "aspect_ratio": aspect_ratio,
                        "motion_strength": motion_strength
                    }
                else:  # hailuo_02
                    model_id = "fal-ai/minimax/hailuo-02/standard/image-to-video"
                    arguments = {
                        "prompt": motion_prompt,
                        "image_url": processed_image_url,
                        "duration": str(duration),
                        "prompt_optimizer": prompt_optimizer
                    }
                
                # Submit job
                print(f"[Job {index}] Submitting {duration}s video...")
                handler = await fal_client.submit_async(model_id, arguments=arguments)
                
                submissions.append({
                    "success": True,
                    "index": index,
                    "request_id": handler.request_id,
                    "model_id": model_id,
                    "model": model,
                    "duration": duration,
                    "request": request,
                    "image_url": image_url,
                    "processed_image_url": processed_image_url,
                    "project_id": project_id,
                    "scene_id": scene_id,
                    "motion_prompt": motion_prompt,
                    "aspect_ratio": aspect_ratio
                })
                print(f"[Job {index}] Submitted with ID: {handler.request_id}")
                
            except Exception as e:
                submissions.append({
                    "success": False,
                    "index": index,
                    "error": str(e),
                    "request": request
                })
        
        successful_submissions = [s for s in submissions if s.get("success", False)]
        print(f"\nSuccessfully submitted {len(successful_submissions)} out of {len(requests)} jobs")
        
        # Step 2: Poll for results
        print("\nStep 2: Polling for results...")
        results = []
        start_time = time.time()
        max_wait_time = 300  # 5 minutes max
        poll_interval = 10  # Check every 10 seconds
        
        # Track which jobs are still pending
        pending_jobs = {s["index"]: s for s in successful_submissions}
        completed_jobs = {}
        
        while pending_jobs and (time.time() - start_time) < max_wait_time:
            # Check each pending job
            jobs_to_remove = []
            
            for index, submission in list(pending_jobs.items()):
                try:
                    # Try to get result
                    result = await fal_client.result_async(
                        submission["model_id"],
                        submission["request_id"]
                    )
                    
                    print(f"[Job {index}] Completed!")
                    
                    # Extract video URL
                    video_url = None
                    if isinstance(result, dict):
                        video_url = result.get("video", {}).get("url") or result.get("url") or result.get("output_url")
                    
                    if not video_url:
                        completed_jobs[index] = {
                            "success": False,
                            "index": index,
                            "error": f"No video URL in result: {result}",
                            "request": submission["request"]
                        }
                    else:
                        # Calculate cost
                        cost = calculate_video_cost(submission["model"], submission["duration"])
                        
                        # Create result
                        completed_jobs[index] = {
                            "success": True,
                            "index": index,
                            "asset": {
                                "url": video_url,
                                "type": "video",
                                "cost": cost,
                                "duration": submission["duration"]
                            },
                            "generation_details": {
                                "model": submission["model"],
                                "motion_prompt": submission["motion_prompt"],
                                "duration": submission["duration"],
                                "aspect_ratio": submission["aspect_ratio"],
                                "source_image": submission["image_url"]
                            }
                        }
                        
                        # Handle project/scene association if needed
                        if submission["project_id"] and submission["scene_id"]:
                            # Create asset and add to project
                            asset = Asset(
                                type=AssetType.VIDEO,
                                source=AssetSource.GENERATED,
                                url=video_url,
                                cost=cost,
                                metadata={
                                    "model": submission["model"],
                                    "source_image": submission["image_url"],
                                    "motion_prompt": submission["motion_prompt"],
                                    "duration": submission["duration"],
                                    "aspect_ratio": submission["aspect_ratio"],
                                    "batch_index": index
                                }
                            )
                            
                            project_validation = validate_project_exists(submission["project_id"], ProjectManager)
                            if project_validation["valid"]:
                                project = project_validation["project"]
                                scene = next((s for s in project.scenes if s.id == submission["scene_id"]), None)
                                if scene:
                                    scene.assets.append(asset)
                                    project.total_cost = project.calculate_cost()
                                    project.actual_duration = project.calculate_duration()
                                    project.updated_at = asset.created_at
                                    
                                    # Download asset
                                    download_result = await asset_storage.download_asset(
                                        url=video_url,
                                        project_id=submission["project_id"],
                                        asset_id=asset.id,
                                        asset_type="video"
                                    )
                                    if download_result["success"]:
                                        asset.local_path = download_result["local_path"]
                                        completed_jobs[index]["asset"]["local_path"] = download_result["local_path"]
                                    
                                    completed_jobs[index]["asset"]["id"] = asset.id
                    
                    jobs_to_remove.append(index)
                    
                except Exception as e:
                    # Check if it's still processing
                    error_str = str(e).lower()
                    if "not found" not in error_str and "pending" not in error_str and "processing" not in error_str:
                        # This is an actual error
                        print(f"[Job {index}] Failed: {e}")
                        completed_jobs[index] = {
                            "success": False,
                            "index": index,
                            "error": str(e),
                            "request": submission["request"]
                        }
                        jobs_to_remove.append(index)
            
            # Remove completed jobs from pending
            for index in jobs_to_remove:
                del pending_jobs[index]
            
            if pending_jobs:
                elapsed = time.time() - start_time
                print(f"\nStill waiting for {len(pending_jobs)} jobs: {list(pending_jobs.keys())}")
                print(f"Elapsed time: {elapsed:.1f}s")
                await asyncio.sleep(poll_interval)
        
        # Handle timeouts
        for index, submission in pending_jobs.items():
            completed_jobs[index] = {
                "success": False,
                "index": index,
                "error": f"Timed out after {max_wait_time} seconds",
                "request": submission["request"]
            }
        
        # Add failed submissions
        for submission in submissions:
            if not submission.get("success", False):
                completed_jobs[submission["index"]] = submission
        
        # Sort results by index
        results = [completed_jobs.get(i, {"success": False, "index": i, "error": "Unknown error"}) 
                  for i in range(len(requests))]
        
        # Aggregate results
        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False)]
        
        total_cost = sum(
            r.get("asset", {}).get("cost", 0) for r in successful
        )
        
        total_duration = sum(
            r.get("asset", {}).get("duration", 0) for r in successful
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