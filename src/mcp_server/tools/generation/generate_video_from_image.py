"""Generate video from image tool implementation."""

from typing import Dict, Any, Optional
import asyncio
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
from ...constants import VIDEO_MODELS, ASPECT_RATIOS


async def _parallel_asset_processing(
    asset: Asset,
    project_id: str,
    result_url: str,
    scene_update_func=None
) -> Dict[str, Any]:
    """
    Process asset-related tasks in parallel where possible.
    
    Args:
        asset: The asset to process
        project_id: Project ID for association
        result_url: URL of the generated asset
        scene_update_func: Optional function to update scene
    
    Returns:
        Dict with processing results
    """
    tasks = []
    
    # Task 1: Download asset
    download_task = asset_storage.download_asset(
        url=result_url,
        project_id=project_id,
        asset_id=asset.id,
        asset_type="video"
    )
    tasks.append(("download", download_task))
    
    # Task 2: Update scene if function provided
    if scene_update_func:
        scene_task = scene_update_func()
        tasks.append(("scene_update", scene_task))
    
    # Run tasks in parallel
    results = {}
    if tasks:
        task_results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )
        
        for i, (task_name, _) in enumerate(tasks):
            result = task_results[i]
            if isinstance(result, Exception):
                results[task_name] = {"success": False, "error": str(result)}
            else:
                results[task_name] = result
    
    return results


async def generate_video_from_image(
    image_url: str,
    motion_prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    model: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    cfg_scale: Optional[float] = None,
    prompt_optimizer: bool = True,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None,
    use_queue: bool = True,
    return_queue_id: bool = False
) -> Dict[str, Any]:
    """
    Convert a single image to video with AI-generated motion.
    
    Args:
        image_url: Image input - can be a URL or local file path
        motion_prompt: Description of the motion to apply
        duration: Video duration in seconds (5 or 10 for Kling, 6 or 10 for Hailuo)
        aspect_ratio: Video aspect ratio (only used for Hailuo, not Kling)
        model: Video generation model ("kling_2.1" or "hailuo_02"). Defaults to settings
        negative_prompt: Negative prompt for Kling model (default: "blur, distort, and low quality")
        cfg_scale: CFG scale for Kling model (0.0-1.0, default: 0.5)
        prompt_optimizer: Whether to use prompt optimization - only used for Hailuo model
        project_id: Optional project to associate with
        scene_id: Optional scene to associate with
        use_queue: Whether to use queued processing for better tracking (default: True)
        return_queue_id: Return queue ID immediately without waiting for result
    
    Returns:
        Dict with video generation results or queue ID if return_queue_id=True
    """
    try:
        # Validate and process image input (URL or file path)
        image_validation = await process_image_input(image_url, fal_service)
        if not image_validation["valid"]:
            return image_validation["error_response"]
        
        # Use the processed image URL (original or uploaded)
        processed_image_url = image_validation["data"]
        
        # Validate motion prompt
        if not motion_prompt or not motion_prompt.strip():
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Motion prompt cannot be empty",
                details={"parameter": "motion_prompt"},
                suggestion="Describe the motion you want to apply to the image",
                example="motion_prompt='Camera slowly zooms in while panning right'"
            )
        
        # Use default model if not specified
        if model is None:
            model = settings.default_video_model
        
        # Validate model
        if model not in VIDEO_MODELS:
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                f"Invalid model: {model}",
                details={"parameter": "model", "valid_models": list(VIDEO_MODELS.keys())},
                suggestion=f"Choose one of: {', '.join(VIDEO_MODELS.keys())}",
                example=f"model='{list(VIDEO_MODELS.keys())[0]}'"
            )
        
        # Get model configuration
        model_config = VIDEO_MODELS[model]
        valid_durations = model_config["valid_durations"]
        
        duration_validation = validate_duration(duration, valid_durations=valid_durations)
        if not duration_validation["valid"]:
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                f"Invalid duration for {model}: {duration}",
                details={"parameter": "duration", "valid_durations": valid_durations, "model": model},
                suggestion=f"Use duration {' or '.join(map(str, valid_durations))} for {model}",
                example=f"duration={valid_durations[0]}"
            )
        duration = duration_validation["value"]
        
        # Validate aspect ratio (only for Hailuo, not supported by Kling)
        if model == "hailuo_02":
            ratio_validation = validate_aspect_ratio(aspect_ratio, ASPECT_RATIOS)
            if not ratio_validation["valid"]:
                return ratio_validation["error_response"]
        
        # Validate cfg_scale (only for Kling)
        if model == "kling_2.1":
            if cfg_scale is None:
                cfg_scale = model_config.get("default_cfg_scale", 0.5)
            min_cfg = model_config.get("min_cfg_scale", 0.0)
            max_cfg = model_config.get("max_cfg_scale", 1.0)
            cfg_validation = validate_range(
                cfg_scale, "cfg_scale", min_cfg, max_cfg, "CFG scale"
            )
            if not cfg_validation["valid"]:
                return cfg_validation["error_response"]
            cfg_scale = cfg_validation["value"]
            
            if negative_prompt is None:
                negative_prompt = model_config.get("default_negative_prompt", "blur, distort, and low quality")
        
        # Calculate cost early for queue response
        cost = calculate_video_cost(model, duration)
        
        # Use queued processing if requested
        if use_queue:
            # Prepare FAL arguments
            fal_arguments = {
                "prompt": motion_prompt,
                "image_url": processed_image_url,
                "duration": str(duration),  # FAL expects string
            }
            
            # Add model-specific arguments
            if model == "kling_2.1":
                fal_arguments["negative_prompt"] = negative_prompt
                fal_arguments["cfg_scale"] = cfg_scale
            elif model == "hailuo_02":
                fal_arguments["aspect_ratio"] = aspect_ratio
                if "prompt_optimizer" in model_config.get("supports", []):
                    fal_arguments["prompt_optimizer"] = prompt_optimizer
            
            # Submit to queue
            queue_id = await fal_service.submit_generation(
                model_id=model_config["fal_model_id"],
                arguments=fal_arguments,
                task_type="video",
                project_id=project_id,
                scene_id=scene_id,
                metadata={
                    "cost": cost,
                    "source_image": image_url,
                    "motion_prompt": motion_prompt,
                    "duration": duration,
                    "aspect_ratio": aspect_ratio,
                    "model": model
                }
            )
            
            # Return queue ID immediately if requested
            if return_queue_id:
                return {
                    "success": True,
                    "queued": True,
                    "queue_id": queue_id,
                    "message": f"Video generation queued (model: {model})",
                    "estimated_cost": cost,
                    "estimated_duration": duration,
                    "check_status": f"Use get_queue_status(task_id='{queue_id}') to check progress",
                    "next_steps": [
                        f"Check status: get_queue_status(task_id='{queue_id}')",
                        "Submit more videos with return_queue_id=True for batch processing",
                        "Wait for all tasks: get_queue_status(project_id=project_id)",
                        "When complete: assemble_video() to combine all scenes and audio"
                    ]
                }
            
            # Otherwise wait for completion
            result = await fal_service.wait_for_task(queue_id, timeout=settings.generation_timeout)
            
            if not result["success"]:
                return handle_fal_api_error(Exception(result["error"]), "video generation")
            
            # Extract the actual result from queue response
            queue_result = result.get("result", {})
            # Convert to expected format
            video_url = None
            if isinstance(queue_result, dict):
                video_url = queue_result.get("video", {}).get("url") or queue_result.get("url") or queue_result.get("output_url")
            
            if not video_url:
                return create_error_response(
                    ErrorType.GENERATION_ERROR,
                    "No video URL found in generation result",
                    details={"result": queue_result}
                )
            
            result = {
                "success": True,
                "url": video_url,
                "metadata": queue_result
            }
        else:
            # Use direct generation (legacy mode)
            # Generate the video with model-specific parameters
            kwargs = {
                "image_url": processed_image_url,
                "motion_prompt": motion_prompt,
                "duration": duration,
                "model": model
            }
            
            # Add model-specific parameters
            if model == "kling_2.1":
                kwargs["negative_prompt"] = negative_prompt
                kwargs["cfg_scale"] = cfg_scale
            elif model == "hailuo_02":
                kwargs["aspect_ratio"] = aspect_ratio
                if "prompt_optimizer" in model_config.get("supports", []):
                    kwargs["prompt_optimizer"] = prompt_optimizer
            
            result = await fal_service.generate_video_from_image(**kwargs)
        
        if not result["success"]:
            # If it's an API error, provide helpful context
            if "error" in result:
                return handle_fal_api_error(Exception(result["error"]), "video generation")
            return result
        
        # Create asset record
        metadata = {
            "model": model,
            "source_image": image_url,
            "motion_prompt": motion_prompt,
            "duration": duration
        }
        
        generation_params = {
            "image_url": image_url,
            "motion_prompt": motion_prompt,
            "duration": duration,
            "model": model
        }
        
        # Add model-specific metadata
        if model == "kling_2.1":
            metadata["negative_prompt"] = negative_prompt
            metadata["cfg_scale"] = cfg_scale
            generation_params["negative_prompt"] = negative_prompt
            generation_params["cfg_scale"] = cfg_scale
        elif model == "hailuo_02":
            metadata["aspect_ratio"] = aspect_ratio
            generation_params["aspect_ratio"] = aspect_ratio
            if "prompt_optimizer" in model_config.get("supports", []):
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
                
                # Define scene update function
                async def update_scene():
                    project.total_cost = project.calculate_cost()
                    project.actual_duration = project.calculate_duration()
                    project.updated_at = asset.created_at
                    return {"success": True}
                
                # Process asset and update scene in parallel
                parallel_results = await _parallel_asset_processing(
                    asset=asset,
                    project_id=project_id,
                    result_url=result["url"],
                    scene_update_func=update_scene
                )
                
                # Update asset with download result
                download_result = parallel_results.get("download", {})
                if download_result.get("success"):
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
                "model": model,
                "motion_prompt": motion_prompt,
                "duration": duration,
                "source_image": image_url,
                **({
                    "negative_prompt": negative_prompt,
                    "cfg_scale": cfg_scale
                } if model == "kling_2.1" else {
                    "aspect_ratio": aspect_ratio,
                    "prompt_optimizer": prompt_optimizer
                } if model == "hailuo_02" else {})
            },
            "project_association": {
                "project_id": project_id,
                "scene_id": scene_id
            } if project_id else None,
            "next_steps": [
                "For multiple videos: Use return_queue_id=True for non-blocking batch processing",
                "Generate audio: generate_speech() FIRST for narrated videos, then generate_music()",
                "Add more scenes to your project with add_scene()",
                "Check queue status: get_queue_status(task_id=queue_id) if using queuing",
                "When all assets ready: assemble_video() to combine everything (handles all audio mixing)"
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
            details={"model": model, "error": str(e)},
            suggestion="Check your image URL and motion prompt, then try again",
            example="generate_video_from_image(image_url='...', motion_prompt='Simple zoom in', duration=5)"
        )