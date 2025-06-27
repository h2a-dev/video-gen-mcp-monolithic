"""FAL AI API client service."""

import os
import asyncio
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import fal_client
from pathlib import Path
from ..config import settings
from .file_upload_cache import FileUploadCache


class FALClient:
    """Unified FAL AI client for all generation services."""
    
    def __init__(self):
        self.api_key = settings.fal_api_key
        if not self.api_key:
            raise ValueError("FALAI_API_KEY environment variable is required")
        
        # Configure fal_client
        os.environ["FAL_KEY"] = self.api_key
        
        # HTTP client for connection pooling
        self._http_client = None
        
        # File upload cache
        self._upload_cache = FileUploadCache(max_size=100, ttl_hours=24)
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.timeout = settings.generation_timeout
        
    async def generate_image_from_text(
        self,
        prompt: str,
        model: str = "imagen4",
        aspect_ratio: str = "16:9",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate image from text using specified model."""
        try:
            if model == "imagen4":
                result = await self._run_imagen4(prompt, aspect_ratio, **kwargs)
            elif model == "flux_pro":
                result = await self._run_flux_pro(prompt, aspect_ratio, **kwargs)
            else:
                raise ValueError(f"Unsupported image model: {model}")
            
            return {
                "success": True,
                "url": result.get("images", [{}])[0].get("url"),
                "model": model,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "metadata": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": model
            }
    
    async def generate_image_from_image(
        self,
        image_url: str,
        prompt: str,
        model: str = "flux_kontext",
        guidance_scale: float = 3.5,  # Fixed at 3.5 for optimal results
        safety_tolerance: str = "3",
        **kwargs
    ) -> Dict[str, Any]:
        """Transform image based on prompt. Guidance scale is fixed at 3.5."""
        try:
            result = await self._run_flux_kontext(image_url, prompt, 3.5, safety_tolerance, **kwargs)
            
            return {
                "success": True,
                "url": result.get("images", [{}])[0].get("url"),
                "model": model,
                "source_image": image_url,
                "prompt": prompt,
                "metadata": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": model
            }
    
    async def generate_video_from_image(
        self,
        image_url: str,
        motion_prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        model: str = "kling_2.1",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate video from single image with motion."""
        try:
            if model == "kling_2.1":
                result = await self._run_kling_video(
                    image_url, motion_prompt, duration, aspect_ratio, **kwargs
                )
            elif model == "hailuo_02":
                result = await self._run_hailuo_video(
                    image_url, motion_prompt, duration, aspect_ratio, **kwargs
                )
            else:
                raise ValueError(f"Unsupported video model: {model}")
            
            # Handle different result formats from different models
            video_url = None
            if isinstance(result, dict):
                # Try different possible formats
                video_url = result.get("video", {}).get("url") or result.get("url") or result.get("output_url")
            
            if not video_url:
                print(f"WARNING: Could not find video URL in result: {result}")
                raise ValueError(f"No video URL found in result")
            
            return {
                "success": True,
                "url": video_url,
                "model": model,
                "duration": duration,
                "source_image": image_url,
                "motion_prompt": motion_prompt,
                "metadata": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": model
            }
    
    async def generate_music(
        self,
        prompt: str,
        duration: int = 95,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate background music."""
        try:
            result = await self._run_lyria2(prompt, **kwargs)
            
            return {
                "success": True,
                "url": result.get("audio", {}).get("url"),
                "model": "lyria2",
                "prompt": prompt,
                "duration": duration,
                "metadata": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": "lyria2"
            }
    
    async def generate_speech(
        self,
        text: str,
        voice: str = "Wise_Woman",
        speed: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate speech from text."""
        try:
            result = await self._run_minimax_speech(text, voice, speed, **kwargs)
            
            return {
                "success": True,
                "url": result.get("audio", {}).get("url"),
                "duration_ms": result.get("duration_ms", 0),
                "duration_seconds": result.get("duration_ms", 0) / 1000.0,
                "model": "minimax_speech",
                "text": text,
                "voice": voice,
                "metadata": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": "minimax_speech"
            }
    
    # Private methods for specific model implementations
    
    async def _run_imagen4(self, prompt: str, aspect_ratio: str, **kwargs) -> Dict[str, Any]:
        """Run Google Imagen 4 model with retry logic."""
        return await self._run_with_retry(
            model_id="fal-ai/imagen4/preview",
            arguments={
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "num_images": 1,
                **kwargs
            }
        )
    
    async def _run_flux_pro(self, prompt: str, aspect_ratio: str, **kwargs) -> Dict[str, Any]:
        """Run FLUX Pro model with retry logic."""
        return await self._run_with_retry(
            model_id="fal-ai/flux-pro",
            arguments={
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "num_images": 1,
                **kwargs
            }
        )
    
    async def _run_flux_kontext(self, image_url: str, prompt: str, guidance_scale: float, safety_tolerance: str, **kwargs) -> Dict[str, Any]:
        """Run FLUX Kontext model for image editing with retry logic."""
        return await self._run_with_retry(
            model_id="fal-ai/flux-pro/kontext",
            arguments={
                "prompt": prompt,
                "image_url": image_url,
                "guidance_scale": 3.5,  # Always use 3.5 for optimal results
                "safety_tolerance": safety_tolerance,
                **kwargs
            }
        )
    
    async def _run_kling_video(
        self, image_url: str, prompt: str, duration: int, aspect_ratio: str, **kwargs
    ) -> Dict[str, Any]:
        """Run Kling 2.1 video generation with retry logic."""
        # Remove any hailuo-specific parameters
        kwargs_copy = kwargs.copy()
        kwargs_copy.pop('prompt_optimizer', None)
        
        return await self._run_with_retry(
            model_id="fal-ai/kling-video/v2.1/standard/image-to-video",
            arguments={
                "prompt": prompt,
                "image_url": image_url,
                "duration": str(duration),
                "aspect_ratio": aspect_ratio,
                **kwargs_copy
            }
        )
    
    async def _run_hailuo_video(
        self, image_url: str, prompt: str, duration: int, aspect_ratio: str, **kwargs
    ) -> Dict[str, Any]:
        """Run Hailuo 02 video generation with retry logic."""
        # Remove any kling-specific parameters
        kwargs_copy = kwargs.copy()
        kwargs_copy.pop('motion_strength', None)
        
        # Extract prompt_optimizer with default True
        prompt_optimizer = kwargs_copy.pop('prompt_optimizer', True)
        
        return await self._run_with_retry(
            model_id="fal-ai/minimax/hailuo-02/standard/image-to-video",
            arguments={
                "prompt": prompt,
                "image_url": image_url,
                "duration": str(duration),
                "prompt_optimizer": prompt_optimizer,
                **kwargs_copy
            }
        )
    
    async def _run_lyria2(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Run Lyria 2 music generation with retry logic."""
        return await self._run_with_retry(
            model_id="fal-ai/lyria2",
            arguments={
                "prompt": prompt,
                **kwargs
            }
        )
    
    async def _run_minimax_speech(self, text: str, voice: str, speed: float, **kwargs) -> Dict[str, Any]:
        """Run MiniMax speech generation with retry logic."""
        return await self._run_with_retry(
            model_id="fal-ai/minimax/speech-02-hd",
            arguments={
                "text": text,
                "voice_setting": {
                    "voice_id": voice,
                    "speed": speed
                },
                **kwargs
            }
        )
    
    async def upload_file(self, file_path: str) -> Dict[str, Any]:
        """Upload a file to FAL and get a URL, using cache to avoid duplicates."""
        async def _do_upload(path: str) -> Dict[str, Any]:
            """Inner function that performs the actual upload."""
            try:
                url = await fal_client.upload_file_async(path)
                return {
                    "success": True,
                    "url": url
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        # Use cache for the upload
        return await self._upload_cache.get_or_upload(file_path, _do_upload)

    async def _run_with_queue(self, model_id: str, arguments: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """Run FAL model using queue-based processing with polling."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Use subscribe method for simpler queue handling
                def on_queue_update(update):
                    # Log the update type for debugging
                    print(f"Queue update: {type(update)}")
                    
                    # Try to access logs if available
                    if hasattr(update, 'logs') and update.logs:
                        for log in update.logs:
                            if isinstance(log, dict) and 'message' in log:
                                print(f"[FAL] {log['message']}")
                            elif isinstance(log, str):
                                print(f"[FAL] {log}")
                
                print(f"Submitting job to queue for model: {model_id}")
                
                # For longer videos (10s), use submit/poll pattern to avoid timeouts
                video_duration = arguments.get('duration', '5')
                if isinstance(video_duration, str):
                    video_duration = int(video_duration)
                
                # Use submit/poll for videos 10s or longer, or if explicitly requested
                use_polling = (model_id.endswith('image-to-video') and video_duration >= 10) or arguments.get('use_polling', False)
                
                if use_polling:
                    print(f"Using polling method for long-running job (duration: {video_duration}s)")
                    print(f"Model: {model_id}")
                    # Submit job
                    handler = await fal_client.submit_async(model_id, arguments=arguments)
                    request_id = handler.request_id
                    print(f"Job submitted. Request ID: {request_id}")
                    
                    # Poll for completion
                    poll_interval = 10  # seconds (reduced for faster feedback)
                    # For batch operations, use a shorter timeout to avoid blocking
                    batch_timeout = arguments.get('batch_timeout', self.timeout)
                    max_polls = int(batch_timeout / poll_interval)
                    
                    for poll_count in range(max_polls):
                        await asyncio.sleep(poll_interval)
                        
                        try:
                            # Try to get result
                            result = await fal_client.result_async(model_id, request_id)
                            print(f"Job {request_id} completed successfully after {(poll_count + 1) * poll_interval} seconds!")
                            return result
                        except Exception as e:
                            error_str = str(e).lower()
                            # Check if this is a "not ready" error vs other errors
                            if "not found" in error_str or "pending" in error_str or "in_queue" in error_str or "processing" in error_str:
                                # Job is still processing, check status
                                try:
                                    status = await fal_client.status_async(model_id, request_id, with_logs=True)
                                    if hasattr(status, 'logs') and status.logs:
                                        for log in status.logs[-5:]:  # Show last 5 logs
                                            if isinstance(log, dict) and 'message' in log:
                                                print(f"[FAL] {log['message']}")
                                            elif isinstance(log, str):
                                                print(f"[FAL] {log}")
                                except Exception as status_error:
                                    print(f"Failed to get status for {request_id}: {status_error}")
                                
                                print(f"Job {request_id} still processing... ({(poll_count + 1) * poll_interval}s elapsed)")
                            else:
                                # This is an unexpected error, log it
                                print(f"WARNING: Unexpected error polling {request_id}: {e}")
                                # Don't break the loop - job might still be processing
                    
                    # Final attempt with better error handling
                    try:
                        result = await fal_client.result_async(model_id, request_id)
                        print(f"Job {request_id} completed on final attempt!")
                        return result
                    except Exception as e:
                        # Log the final error clearly
                        elapsed_time = max_polls * poll_interval
                        print(f"ERROR: Job {request_id} failed after {elapsed_time}s: {e}")
                        raise RuntimeError(f"Job {request_id} timed out after {elapsed_time} seconds. Last error: {e}")
                else:
                    # Use subscribe for shorter jobs
                    result = await fal_client.subscribe_async(
                        model_id,
                        arguments=arguments,
                        on_queue_update=on_queue_update,
                    )
                    
                    print(f"Job completed successfully!")
                    return result
                    
            except asyncio.TimeoutError:
                last_error = f"Request timed out after {self.timeout} seconds"
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
            except Exception as e:
                last_error = str(e)
                
                # Check for rate limiting or temporary errors
                error_msg = str(e).lower()
                if any(term in error_msg for term in ["rate limit", "too many requests", "503", "502"]):
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        await asyncio.sleep(wait_time)
                        continue
                
                # For downstream service errors, don't retry (it's a model issue)
                if any(term in error_msg for term in ["downstream", "downstream_service_error"]):
                    break
                
                # For other errors, don't retry
                break
        
        # All retries failed
        raise RuntimeError(f"FAL API call failed after {self.max_retries} attempts: {last_error}")
    
    async def _run_with_retry(self, model_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Run FAL model with retry logic and error handling - now uses queue-based processing."""
        return await self._run_with_queue(model_id, arguments)
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling"""
        if not self._http_client:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._http_client
    
    async def cleanup(self):
        """Clean up resources - call this when shutting down"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get upload cache statistics."""
        return self._upload_cache.get_stats()
    
    # Queue-based submission methods
    
    async def submit_generation(
        self,
        model_id: str,
        arguments: Dict[str, Any],
        task_type: str,
        project_id: Optional[str] = None,
        scene_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Submit a generation task and return queue ID."""
        from ..models import queue_manager
        
        # Create queue task
        task = await queue_manager.create_task(
            task_type=task_type,
            model=model_id,
            arguments=arguments,
            project_id=project_id,
            scene_id=scene_id,
            metadata=metadata
        )
        
        # Start async processing
        asyncio_task = asyncio.create_task(
            self._process_queued_task(task.id, model_id, arguments)
        )
        await queue_manager.register_active_task(task.id, asyncio_task)
        
        return task.id
    
    async def _process_queued_task(
        self,
        task_id: str,
        model_id: str,
        arguments: Dict[str, Any]
    ):
        """Process a queued task with status updates."""
        from ..models import queue_manager, QueueStatus
        
        try:
            # Submit to FAL
            handler = await fal_client.submit_async(model_id, arguments=arguments)
            
            # Update task with request ID
            await queue_manager.update_task(
                task_id,
                request_id=handler.request_id
            )
            
            # Process events
            logs_index = 0
            async for event in handler.iter_events(with_logs=True):
                update_data = {}
                
                if isinstance(event, fal_client.Queued):
                    update_data = {
                        "status": QueueStatus.QUEUED,
                        "queue_position": event.position
                    }
                    print(f"Task {task_id} queued at position {event.position}")
                
                elif isinstance(event, (fal_client.InProgress, fal_client.Completed)):
                    if isinstance(event, fal_client.InProgress):
                        update_data = {
                            "status": QueueStatus.IN_PROGRESS,
                            "started_at": datetime.now()
                        }
                    
                    # Process new logs
                    if hasattr(event, 'logs') and event.logs:
                        new_logs = event.logs[logs_index:]
                        logs_index = len(event.logs)
                        
                        # Extract progress from logs
                        for log in new_logs:
                            if isinstance(log, dict):
                                if 'progress' in log:
                                    update_data['progress_percentage'] = log['progress']
                                if 'message' in log:
                                    print(f"[FAL] {log['message']}")
                        
                        # Add logs to task
                        task = await queue_manager.get_task(task_id)
                        if task:
                            task.logs.extend(new_logs)
                
                # Update task
                if update_data:
                    await queue_manager.update_task(task_id, **update_data)
            
            # Get final result
            result = await handler.get()
            
            # Update task as completed
            await queue_manager.update_task(
                task_id,
                status=QueueStatus.COMPLETED,
                completed_at=datetime.now(),
                result=result,
                progress_percentage=100.0
            )
            
            print(f"Task {task_id} completed successfully!")
            
            # Handle post-processing for video generation tasks
            task = await queue_manager.get_task(task_id)
            if task and task.task_type == "video" and task.project_id:
                await self._process_video_completion(task, result)
            
        except asyncio.CancelledError:
            # Task was cancelled
            await queue_manager.update_task(
                task_id,
                status=QueueStatus.CANCELLED,
                completed_at=datetime.now(),
                error_message="Task cancelled by user"
            )
            raise
            
        except Exception as e:
            # Task failed
            await queue_manager.update_task(
                task_id,
                status=QueueStatus.FAILED,
                completed_at=datetime.now(),
                error_message=str(e)
            )
            print(f"Task {task_id} failed: {e}")
            raise
            
        finally:
            # Unregister active task
            await queue_manager.unregister_active_task(task_id)
    
    async def get_queue_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a queued task."""
        from ..models import queue_manager
        
        task = await queue_manager.get_task(task_id)
        if task:
            return task.dict()
        return None
    
    async def _process_video_completion(self, task, result):
        """Process video completion - create asset and associate with scene."""
        from ..models import ProjectManager, Asset, AssetType, AssetSource
        from ..services import asset_storage
        
        try:
            # Extract video URL from result
            video_url = None
            if isinstance(result, dict):
                video_url = result.get("video", {}).get("url") or result.get("url") or result.get("output_url")
            
            if not video_url:
                print(f"WARNING: No video URL found in result for task {task.id}")
                return
            
            # Get metadata from task
            metadata = task.metadata or {}
            
            # Create asset
            asset = Asset(
                type=AssetType.VIDEO,
                source=AssetSource.GENERATED,
                url=video_url,
                cost=metadata.get("cost", 0.0),
                metadata={
                    "model": metadata.get("model"),
                    "source_image": metadata.get("source_image"),
                    "motion_prompt": metadata.get("motion_prompt"),
                    "duration": metadata.get("duration"),
                    "aspect_ratio": metadata.get("aspect_ratio")
                },
                generation_params=metadata
            )
            
            # Download asset
            if task.project_id:
                download_result = await asset_storage.download_asset(
                    url=video_url,
                    project_id=task.project_id,
                    asset_id=asset.id,
                    asset_type="video"
                )
                
                if download_result.get("success"):
                    asset.local_path = download_result["local_path"]
            
            # Associate with scene if specified
            if task.project_id and task.scene_id:
                project = ProjectManager.get_project(task.project_id)
                scene = next((s for s in project.scenes if s.id == task.scene_id), None)
                
                if scene:
                    scene.assets.append(asset)
                    # Update scene duration if needed
                    if "duration" in metadata and scene.duration != metadata["duration"]:
                        scene.duration = metadata["duration"]
                    
                    # Update project
                    project.total_cost = project.calculate_cost()
                    project.actual_duration = project.calculate_duration()
                    project.updated_at = datetime.now()
                    
                    print(f"Video asset {asset.id} associated with scene {scene.id}")
                else:
                    print(f"WARNING: Scene {task.scene_id} not found for video asset")
            
        except Exception as e:
            print(f"ERROR processing video completion: {e}")
    
    async def wait_for_task(
        self,
        task_id: str,
        timeout: Optional[float] = None,
        poll_interval: float = 2.0
    ) -> Dict[str, Any]:
        """Wait for a queued task to complete."""
        from ..models import queue_manager, QueueStatus
        
        start_time = time.time()
        
        while True:
            task = await queue_manager.get_task(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            if task.status == QueueStatus.COMPLETED:
                return {"success": True, "result": task.result}
            
            if task.status == QueueStatus.FAILED:
                return {"success": False, "error": task.error_message}
            
            if task.status == QueueStatus.CANCELLED:
                return {"success": False, "error": "Task was cancelled"}
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                return {"success": False, "error": f"Timeout after {timeout} seconds"}
            
            # Wait before next check
            await asyncio.sleep(poll_interval)


# Singleton instance
fal_service = FALClient()