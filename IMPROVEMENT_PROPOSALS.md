# Video Generation Service Improvement Proposals

## Executive Summary

This document outlines architectural improvements for the video generation service, focusing on the interconnected relationship between `fal_client.py` (low-level API wrapper) and `generate_video_from_image.py` (high-level business logic).

## Current Architecture Issues

### 1. **Tight Coupling & Mixed Responsibilities**
- `fal_client.py` handles both API communication AND file uploads
- `generate_video_from_image.py` mixes validation, generation, and project management
- No clear separation between infrastructure and domain logic

### 2. **Error Handling Inconsistency**
- Different error patterns between layers
- No unified error recovery strategy
- Limited context for debugging failures

### 3. **Performance Bottlenecks**
- No connection pooling or request caching
- Synchronous file operations blocking the event loop
- Sequential processing without parallelization opportunities

### 4. **Limited Extensibility**
- Adding new models requires modifying core files
- No plugin architecture for custom processors
- Hardcoded configurations throughout

## Proposed Architecture

### Layer 1: Core Infrastructure (`fal_client.py` improvements)

#### 1.1 **Implement Retry Strategy Pattern**

```python
# src/mcp_server/services/retry_strategy.py
from abc import ABC, abstractmethod
import asyncio
from typing import Optional, Callable, TypeVar, Generic

T = TypeVar('T')

class RetryStrategy(ABC, Generic[T]):
    @abstractmethod
    async def execute(self, operation: Callable[[], T]) -> T:
        pass

class ExponentialBackoffRetry(RetryStrategy[T]):
    def __init__(
        self, 
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    async def execute(self, operation: Callable[[], T]) -> T:
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return await operation()
            except Exception as e:
                last_exception = e
                if attempt < self.max_attempts - 1:
                    delay = min(
                        self.initial_delay * (self.exponential_base ** attempt),
                        self.max_delay
                    )
                    if self.jitter:
                        delay *= (0.5 + random.random())
                    await asyncio.sleep(delay)
        
        raise last_exception

class CircuitBreaker:
    """Prevents cascading failures by tracking error rates"""
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
```

#### 1.2 **Separate File Upload Service**

```python
# src/mcp_server/services/file_upload_service.py
from pathlib import Path
import aiofiles
import hashlib

class FileUploadService:
    def __init__(self, fal_client):
        self.fal_client = fal_client
        self._upload_cache = {}  # hash -> url mapping
    
    async def upload_file(self, file_path: str) -> Dict[str, Any]:
        """Upload file with caching based on content hash"""
        path = Path(file_path)
        
        # Calculate file hash asynchronously
        file_hash = await self._calculate_file_hash(path)
        
        # Check cache
        if file_hash in self._upload_cache:
            return {
                "success": True,
                "url": self._upload_cache[file_hash],
                "cached": True,
                "original_path": file_path
            }
        
        # Upload new file
        url = await self.fal_client.upload_file_async(str(path))
        self._upload_cache[file_hash] = url
        
        return {
            "success": True,
            "url": url,
            "cached": False,
            "original_path": file_path
        }
    
    async def _calculate_file_hash(self, path: Path) -> str:
        """Calculate SHA256 hash of file content asynchronously"""
        sha256_hash = hashlib.sha256()
        async with aiofiles.open(path, 'rb') as f:
            while chunk := await f.read(8192):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
```

#### 1.3 **Implement Connection Pooling**

```python
# Updated FALClient with connection pooling
class FALClient:
    def __init__(self):
        self.api_key = settings.fal_api_key
        self._client = None
        self._retry_strategy = ExponentialBackoffRetry()
        self._circuit_breakers = {}  # model_id -> CircuitBreaker
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        return self._client
    
    async def close(self):
        """Clean up resources"""
        if self._client:
            await self._client.aclose()
```

### Layer 2: Domain Logic (`generate_video_from_image.py` improvements)

#### 2.1 **Implement Strategy Pattern for Video Models**

```python
# src/mcp_server/services/video_generation/models.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class VideoGenerationModel(ABC):
    """Abstract base class for video generation models"""
    
    @abstractmethod
    def get_valid_durations(self) -> List[int]:
        """Return list of valid durations for this model"""
        pass
    
    @abstractmethod
    def get_model_id(self) -> str:
        """Return the FAL model ID"""
        pass
    
    @abstractmethod
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        """Prepare model-specific parameters"""
        pass
    
    @abstractmethod
    def calculate_cost(self, duration: int) -> float:
        """Calculate generation cost"""
        pass

class KlingVideoModel(VideoGenerationModel):
    def get_valid_durations(self) -> List[int]:
        return [5, 10]
    
    def get_model_id(self) -> str:
        return "kling_2.1"
    
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        params = {
            "image_url": kwargs["image_url"],
            "motion_prompt": kwargs["motion_prompt"],
            "duration": kwargs["duration"],
            "aspect_ratio": kwargs["aspect_ratio"],
        }
        if "motion_strength" in kwargs:
            params["motion_strength"] = kwargs["motion_strength"]
        return params
    
    def calculate_cost(self, duration: int) -> float:
        return duration * 0.05  # $0.05 per second

class HailuoVideoModel(VideoGenerationModel):
    def get_valid_durations(self) -> List[int]:
        return [6, 10]
    
    def get_model_id(self) -> str:
        return "hailuo_02"
    
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        params = {
            "image_url": kwargs["image_url"],
            "motion_prompt": kwargs["motion_prompt"],
            "duration": kwargs["duration"],
            "aspect_ratio": kwargs.get("aspect_ratio", "16:9"),
            "prompt_optimizer": kwargs.get("prompt_optimizer", True)
        }
        return params
    
    def calculate_cost(self, duration: int) -> float:
        return duration * 0.045  # $0.045 per second (10% cheaper)

class VideoModelFactory:
    _models = {
        "kling_2.1": KlingVideoModel,
        "hailuo_02": HailuoVideoModel,
    }
    
    @classmethod
    def create(cls, model_name: str) -> VideoGenerationModel:
        if model_name not in cls._models:
            raise ValueError(f"Unknown model: {model_name}")
        return cls._models[model_name]()
    
    @classmethod
    def register_model(cls, name: str, model_class: type[VideoGenerationModel]):
        """Allow registration of custom models"""
        cls._models[name] = model_class
```

#### 2.2 **Separate Validation Logic**

```python
# src/mcp_server/services/video_generation/validators.py
from typing import Dict, Any, Optional
import validators

class VideoGenerationValidator:
    def __init__(self, model: VideoGenerationModel):
        self.model = model
    
    async def validate_request(
        self,
        image_url: str,
        motion_prompt: str,
        duration: int,
        aspect_ratio: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Validate all parameters for video generation"""
        errors = []
        
        # Validate image URL
        if not await self._is_valid_image_url(image_url):
            errors.append({
                "field": "image_url",
                "message": "Invalid or inaccessible image URL"
            })
        
        # Validate motion prompt
        if not motion_prompt or len(motion_prompt.strip()) < 10:
            errors.append({
                "field": "motion_prompt",
                "message": "Motion prompt must be at least 10 characters"
            })
        
        # Validate duration
        valid_durations = self.model.get_valid_durations()
        if duration not in valid_durations:
            errors.append({
                "field": "duration",
                "message": f"Duration must be one of: {valid_durations}"
            })
        
        # Validate aspect ratio
        valid_ratios = ["16:9", "9:16", "1:1", "4:5"]
        if aspect_ratio not in valid_ratios:
            errors.append({
                "field": "aspect_ratio",
                "message": f"Aspect ratio must be one of: {valid_ratios}"
            })
        
        if errors:
            return {"valid": False, "errors": errors}
        
        return {"valid": True}
    
    async def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL is valid and accessible"""
        if url.startswith(('http://', 'https://')):
            # Could add actual HTTP HEAD request here
            return validators.url(url)
        elif url.startswith('/'):
            # Local file path
            return Path(url).exists()
        return False
```

#### 2.3 **Implement Service Layer**

```python
# src/mcp_server/services/video_generation/service.py
class VideoGenerationService:
    def __init__(
        self,
        fal_client: FALClient,
        asset_storage: AssetStorage,
        project_manager: ProjectManager,
        model_factory: VideoModelFactory = VideoModelFactory()
    ):
        self.fal_client = fal_client
        self.asset_storage = asset_storage
        self.project_manager = project_manager
        self.model_factory = model_factory
    
    async def generate_video(
        self,
        image_url: str,
        motion_prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        model_name: Optional[str] = None,
        project_id: Optional[str] = None,
        scene_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate video with proper separation of concerns"""
        
        # 1. Model selection
        model_name = model_name or settings.default_video_model
        model = self.model_factory.create(model_name)
        
        # 2. Validation
        validator = VideoGenerationValidator(model)
        validation_result = await validator.validate_request(
            image_url, motion_prompt, duration, aspect_ratio, **kwargs
        )
        if not validation_result["valid"]:
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Validation failed",
                details=validation_result["errors"]
            )
        
        # 3. Image processing
        processed_image_url = await self._process_image_input(image_url)
        
        # 4. Generate video
        generation_params = model.prepare_parameters(
            image_url=processed_image_url,
            motion_prompt=motion_prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            **kwargs
        )
        
        result = await self.fal_client.generate_video_from_image(
            model=model.get_model_id(),
            **generation_params
        )
        
        if not result["success"]:
            return result
        
        # 5. Create asset
        asset = await self._create_asset(
            result, model, image_url, motion_prompt, 
            duration, aspect_ratio, generation_params
        )
        
        # 6. Project integration (if applicable)
        if project_id:
            await self._integrate_with_project(
                asset, project_id, scene_id, duration
            )
        
        return self._format_response(asset, model_name, project_id, scene_id)
```

### Layer 3: Cross-Cutting Concerns

#### 3.1 **Implement Observability**

```python
# src/mcp_server/services/observability.py
import structlog
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode
import time

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Create metrics
video_generation_counter = meter.create_counter(
    name="video_generation_total",
    description="Total number of video generation requests",
    unit="1"
)

video_generation_duration = meter.create_histogram(
    name="video_generation_duration_seconds",
    description="Duration of video generation requests",
    unit="s"
)

class ObservabilityMiddleware:
    async def __call__(self, func, *args, **kwargs):
        with tracer.start_as_current_span(func.__name__) as span:
            span.set_attribute("model", kwargs.get("model", "unknown"))
            span.set_attribute("duration", kwargs.get("duration", 0))
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                span.set_status(Status(StatusCode.OK))
                
                video_generation_counter.add(1, {"status": "success"})
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                
                video_generation_counter.add(1, {"status": "error"})
                logger.error(
                    "video_generation_failed",
                    error=str(e),
                    model=kwargs.get("model"),
                    duration=kwargs.get("duration")
                )
                raise
            finally:
                duration = time.time() - start_time
                video_generation_duration.record(duration)
```

#### 3.2 **Add Configuration Management**

```python
# src/mcp_server/config/video_generation.py
from pydantic import BaseSettings, Field
from typing import Dict, List

class VideoGenerationConfig(BaseSettings):
    """Configuration for video generation service"""
    
    # Model configurations
    default_model: str = Field("kling_2.1", env="DEFAULT_VIDEO_MODEL")
    model_configs: Dict[str, Dict] = Field(
        default_factory=lambda: {
            "kling_2.1": {
                "valid_durations": [5, 10],
                "cost_per_second": 0.05,
                "max_motion_strength": 1.0,
                "min_motion_strength": 0.1
            },
            "hailuo_02": {
                "valid_durations": [6, 10],
                "cost_per_second": 0.045,
                "supports_prompt_optimizer": True
            }
        }
    )
    
    # Validation settings
    min_prompt_length: int = Field(10, env="MIN_PROMPT_LENGTH")
    valid_aspect_ratios: List[str] = Field(
        default=["16:9", "9:16", "1:1", "4:5"]
    )
    
    # Performance settings
    max_concurrent_generations: int = Field(5, env="MAX_CONCURRENT_GENERATIONS")
    generation_timeout_seconds: int = Field(300, env="GENERATION_TIMEOUT")
    
    # Retry settings
    max_retry_attempts: int = Field(3, env="MAX_RETRY_ATTEMPTS")
    retry_backoff_base: float = Field(2.0, env="RETRY_BACKOFF_BASE")
    
    class Config:
        env_file = ".env"
        env_prefix = "VIDEO_GEN_"
```

### Implementation Benefits

1. **Improved Maintainability**
   - Clear separation of concerns
   - Single responsibility principle
   - Easy to test individual components

2. **Enhanced Performance**
   - Connection pooling reduces latency
   - Caching prevents duplicate uploads
   - Async operations throughout

3. **Better Extensibility**
   - Plugin architecture for new models
   - Configuration-driven behavior
   - Dependency injection pattern

4. **Robust Error Handling**
   - Circuit breaker prevents cascading failures
   - Exponential backoff with jitter
   - Detailed error context and recovery suggestions

5. **Production Readiness**
   - Comprehensive observability
   - Graceful degradation
   - Resource cleanup and lifecycle management

## Migration Strategy

1. **Phase 1**: Implement infrastructure improvements (retry strategy, connection pooling)
2. **Phase 2**: Extract service layer and validators
3. **Phase 3**: Add observability and monitoring
4. **Phase 4**: Implement configuration management
5. **Phase 5**: Add caching and performance optimizations

Each phase can be implemented independently with backward compatibility maintained throughout.

## Proposed: Queuing System Implementation

### Overview

Add comprehensive queuing system for long-running generation tasks with real-time status tracking.

### Key Features

1. **Queue Status Tracking**
   - Real-time queue position updates
   - Progress percentage tracking
   - Estimated wait times
   - Task cancellation support

2. **Enhanced Models**
   ```python
   class QueuedTask(BaseModel):
       id: str
       request_id: str  # FAL request ID
       status: QueueStatus  # queued, in_progress, completed, failed
       queue_position: Optional[int]
       progress_percentage: Optional[float]
       logs: List[Dict[str, Any]]
   ```

3. **Async Submission API**
   ```python
   # Submit and return immediately
   result = await generate_video_from_image(
       image_url="image.jpg",
       motion_prompt="zoom in",
       return_queue_id=True
   )
   # Returns: {"queued": True, "queue_id": "abc123"}
   ```

4. **Queue Monitoring Tools**
   - `get_queue_status` - Check task/project queue status
   - MCP resources for real-time monitoring
   - Batch task tracking

### Implementation Plan

1. **Phase 1**: Queue models and manager
2. **Phase 2**: Enhanced FAL client with event streaming
3. **Phase 3**: Queue status tools and resources
4. **Phase 4**: Update generation tools
5. **Phase 5**: Batch processing support

See `QUEUING_IMPLEMENTATION_PROPOSAL.md` for full details.