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


class FALClient:
    """Unified FAL AI client for all generation services."""
    
    def __init__(self):
        self.api_key = settings.fal_api_key
        if not self.api_key:
            raise ValueError("FALAI_API_KEY environment variable is required")
        
        # Configure fal_client
        os.environ["FAL_KEY"] = self.api_key
        
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
        guidance_scale: float = 3.5,
        **kwargs
    ) -> Dict[str, Any]:
        """Transform image based on prompt."""
        try:
            result = await self._run_flux_kontext(image_url, prompt, guidance_scale, **kwargs)
            
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
        **kwargs
    ) -> Dict[str, Any]:
        """Generate video from single image with motion."""
        try:
            result = await self._run_kling_video(
                image_url, motion_prompt, duration, aspect_ratio, **kwargs
            )
            
            return {
                "success": True,
                "url": result.get("video", {}).get("url"),
                "model": "kling_2.1",
                "duration": duration,
                "source_image": image_url,
                "motion_prompt": motion_prompt,
                "metadata": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": "kling_2.1"
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
    
    async def _run_flux_kontext(self, image_url: str, prompt: str, guidance_scale: float, **kwargs) -> Dict[str, Any]:
        """Run FLUX Kontext model for image editing with retry logic."""
        return await self._run_with_retry(
            model_id="fal-ai/flux-pro/kontext",
            arguments={
                "prompt": prompt,
                "image_url": image_url,
                "guidance_scale": guidance_scale,
                **kwargs
            }
        )
    
    async def _run_kling_video(
        self, image_url: str, prompt: str, duration: int, aspect_ratio: str, **kwargs
    ) -> Dict[str, Any]:
        """Run Kling 2.1 video generation with retry logic."""
        return await self._run_with_retry(
            model_id="fal-ai/kling-video/v2.1/standard/image-to-video",
            arguments={
                "prompt": prompt,
                "image_url": image_url,
                "duration": str(duration),
                "aspect_ratio": aspect_ratio,
                **kwargs
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
        """Upload a file to FAL and get a URL."""
        try:
            path = Path(file_path)
            if not path.exists():
                raise ValueError(f"File not found: {file_path}")
            
            if not path.is_file():
                raise ValueError(f"Path is not a file: {file_path}")
            
            # Upload file and get URL
            url = await fal_client.upload_file_async(str(path))
            
            return {
                "success": True,
                "url": url,
                "original_path": file_path
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

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
                
                # For other errors, don't retry
                break
        
        # All retries failed
        raise RuntimeError(f"FAL API call failed after {self.max_retries} attempts: {last_error}")
    
    async def _run_with_retry(self, model_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Run FAL model with retry logic and error handling - now uses queue-based processing."""
        return await self._run_with_queue(model_id, arguments)


# Singleton instance
fal_service = FALClient()