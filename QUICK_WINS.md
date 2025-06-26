# Quick Win Improvements for Video Generation Service

## Priority 1: Immediate Fixes (1-2 hours each)

### 1. Fix Connection Leaks in `fal_client.py`
**Problem**: No connection pooling, creating new connections for each request
**Solution**: Add a simple HTTP client with connection reuse

```python
# In FALClient.__init__
self._http_client = None

async def _get_http_client(self):
    if not self._http_client:
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=5)
        )
    return self._http_client

# Add cleanup method
async def cleanup(self):
    if self._http_client:
        await self._http_client.aclose()
```

### 2. Extract Constants and Configuration
**Problem**: Hardcoded values scattered throughout
**Solution**: Create a constants file

```python
# src/mcp_server/constants.py
VIDEO_MODELS = {
    "kling_2.1": {
        "valid_durations": [5, 10],
        "cost_per_second": 0.05,
        "supports": ["motion_strength"]
    },
    "hailuo_02": {
        "valid_durations": [6, 10],
        "cost_per_second": 0.045,
        "supports": ["prompt_optimizer"]
    }
}

ASPECT_RATIOS = {
    "16:9": "Widescreen (YouTube, monitors)",
    "9:16": "Vertical (TikTok, Reels)",
    "1:1": "Square (Instagram posts)",
    "4:5": "Portrait (Instagram posts)"
}
```

### 3. Improve Error Messages
**Problem**: Generic error messages without recovery suggestions
**Solution**: Add error context helper

```python
# src/mcp_server/utils/error_helpers.py
def enhance_fal_error(error: Exception, operation: str) -> Dict[str, Any]:
    error_str = str(error).lower()
    
    if "rate limit" in error_str:
        return create_error_response(
            ErrorType.RATE_LIMIT,
            f"Rate limit exceeded during {operation}",
            suggestion="Wait a few seconds and try again",
            retry_after=5
        )
    
    if "invalid url" in error_str:
        return create_error_response(
            ErrorType.VALIDATION_ERROR,
            "The provided image URL is not accessible",
            suggestion="Ensure the URL points to a valid image file",
            example="https://example.com/image.jpg"
        )
    
    # Add more specific error patterns...
```

## Priority 2: Performance Improvements (2-4 hours)

### 4. Add Simple Request Caching
**Problem**: Duplicate requests for same content
**Solution**: LRU cache for file uploads

```python
from functools import lru_cache
import hashlib

class FileUploadCache:
    def __init__(self, max_size=100):
        self._cache = {}  # file_hash -> url
        self._max_size = max_size
    
    async def get_or_upload(self, file_path: str, upload_func):
        file_hash = await self._hash_file(file_path)
        
        if file_hash in self._cache:
            return self._cache[file_hash]
        
        url = await upload_func(file_path)
        
        if len(self._cache) >= self._max_size:
            # Remove oldest entry
            self._cache.pop(next(iter(self._cache)))
        
        self._cache[file_hash] = url
        return url
```

### 5. Parallelize Independent Operations
**Problem**: Sequential processing when operations could be parallel
**Solution**: Use asyncio.gather for independent tasks

```python
# In generate_video_from_image.py
async def _parallel_asset_processing(asset, project_id, result_url):
    """Download asset and update project in parallel"""
    download_task = asset_storage.download_asset(
        url=result_url,
        project_id=project_id,
        asset_id=asset.id,
        asset_type="video"
    )
    
    # Can do other independent operations here
    results = await asyncio.gather(
        download_task,
        # other_task,
        return_exceptions=True
    )
    
    return results[0]  # download result
```

## Priority 3: Code Organization (4-6 hours)

### 6. Split Large Functions
**Problem**: 268-line function in generate_video_from_image.py
**Solution**: Extract logical chunks

```python
class VideoGenerationHandler:
    async def generate(self, **kwargs):
        # 1. Validate inputs
        validation_result = await self._validate_inputs(**kwargs)
        if not validation_result["valid"]:
            return validation_result["error"]
        
        # 2. Process image
        processed_image = await self._process_image(
            kwargs["image_url"]
        )
        
        # 3. Generate video
        video_result = await self._generate_video(
            processed_image, 
            kwargs
        )
        
        # 4. Create asset record
        asset = await self._create_asset(video_result, kwargs)
        
        # 5. Handle project integration
        if kwargs.get("project_id"):
            await self._integrate_with_project(asset, kwargs)
        
        return self._format_response(asset, kwargs)
```

### 7. Create Model Registry
**Problem**: If/else chains for model selection
**Solution**: Simple registry pattern

```python
class ModelRegistry:
    _models = {}
    
    @classmethod
    def register(cls, name: str, config: dict):
        cls._models[name] = config
    
    @classmethod
    def get(cls, name: str) -> dict:
        if name not in cls._models:
            raise ValueError(f"Unknown model: {name}")
        return cls._models[name]
    
    @classmethod
    def get_all(cls) -> dict:
        return cls._models.copy()

# Register models at startup
ModelRegistry.register("kling_2.1", VIDEO_MODELS["kling_2.1"])
ModelRegistry.register("hailuo_02", VIDEO_MODELS["hailuo_02"])
```

## Priority 4: Robustness (2-3 hours)

### 8. Add Basic Circuit Breaker
**Problem**: Cascading failures when FAL API is down
**Solution**: Simple failure tracking

```python
class SimpleCircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = None
        self.is_open = False
    
    async def call(self, func, *args, **kwargs):
        if self.is_open:
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.is_open = False
                self.failures = 0
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.failure_threshold:
                self.is_open = True
            
            raise
```

### 9. Add Request Timeout Handling
**Problem**: Indefinite waits on failed requests
**Solution**: Proper timeout configuration

```python
# In fal_client.py
async def _run_with_timeout(self, coro, timeout_seconds=None):
    timeout = timeout_seconds or self.timeout
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(
            f"Operation timed out after {timeout} seconds. "
            f"This might be due to high load or a large request. "
            f"Try again with a shorter duration or simpler prompt."
        )
```

## Implementation Order

1. **Day 1**: Implement Priority 1 fixes (1-3)
   - These provide immediate user-facing improvements
   - Low risk, high impact

2. **Day 2**: Add Priority 2 performance improvements (4-5)
   - Noticeable performance gains
   - Foundation for future optimizations

3. **Day 3-4**: Code organization (6-7)
   - Makes future changes easier
   - Improves maintainability

4. **Day 5**: Robustness improvements (8-9)
   - Prevents cascading failures
   - Better error handling

## Testing Strategy

For each improvement:
1. Write unit tests for new components
2. Add integration tests for critical paths
3. Manual testing with various error scenarios
4. Load testing for performance improvements

## Rollback Plan

Each improvement should be:
- Feature-flagged where possible
- Implemented in backward-compatible way
- Easily revertible via git

## Monitoring

Add basic metrics for:
- Request success/failure rates
- Response times
- Cache hit rates
- Circuit breaker activations