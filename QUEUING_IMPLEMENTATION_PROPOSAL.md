# Queuing System Implementation Proposal

## Overview

This proposal outlines the implementation of a comprehensive queuing system for the Video Agent MCP server, enabling real-time queue status tracking and improved user experience for long-running generation tasks.

## Current State

The system currently has basic queue handling in `fal_client.py`:
- Uses `submit_async` for long videos (10s+)
- Basic polling without exposing queue position
- No persistent queue tracking
- No user-visible queue status

## Proposed Architecture

### 1. Queue Status Model (`src/mcp_server/models/queue_status.py`)

```python
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

class QueueStatus(str, Enum):
    """Status of a queued task."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class QueuedTask(BaseModel):
    """Represents a queued generation task with real-time status."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str  # FAL request ID
    project_id: Optional[str] = None
    scene_id: Optional[str] = None
    task_type: str  # "video", "image", "audio", etc.
    model: str
    status: QueueStatus = QueueStatus.QUEUED
    queue_position: Optional[int] = None
    estimated_wait_time: Optional[int] = None  # seconds
    progress_percentage: Optional[float] = None
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class QueueManager:
    """Manages all queued tasks."""
    def __init__(self):
        self._tasks: Dict[str, QueuedTask] = {}
        self._active_tasks: Dict[str, asyncio.Task] = {}
    
    async def submit_task(
        self,
        task_type: str,
        model: str,
        arguments: Dict[str, Any],
        project_id: Optional[str] = None,
        scene_id: Optional[str] = None
    ) -> QueuedTask:
        """Submit a new task to the queue."""
        task = QueuedTask(
            request_id="",  # Will be set after submission
            project_id=project_id,
            scene_id=scene_id,
            task_type=task_type,
            model=model,
            metadata={"arguments": arguments}
        )
        self._tasks[task.id] = task
        
        # Start async processing
        asyncio_task = asyncio.create_task(
            self._process_task(task, model, arguments)
        )
        self._active_tasks[task.id] = asyncio_task
        
        return task
    
    async def get_task_status(self, task_id: str) -> Optional[QueuedTask]:
        """Get current status of a task."""
        return self._tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a queued task."""
        if task_id in self._active_tasks:
            self._active_tasks[task_id].cancel()
            task = self._tasks.get(task_id)
            if task:
                task.status = QueueStatus.CANCELLED
                task.completed_at = datetime.now()
            return True
        return False
```

### 2. Enhanced FAL Client (`src/mcp_server/services/fal_client_queued.py`)

```python
from typing import AsyncIterator
import fal_client

class QueuedFALClient(FALClient):
    """Enhanced FAL client with queue status tracking."""
    
    def __init__(self):
        super().__init__()
        self.queue_manager = QueueManager()
    
    async def submit_generation(
        self,
        model_id: str,
        arguments: Dict[str, Any],
        task_type: str,
        project_id: Optional[str] = None,
        scene_id: Optional[str] = None
    ) -> QueuedTask:
        """Submit a generation task and return queue tracking object."""
        task = await self.queue_manager.submit_task(
            task_type=task_type,
            model=model_id,
            arguments=arguments,
            project_id=project_id,
            scene_id=scene_id
        )
        return task
    
    async def iter_task_updates(
        self,
        task_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Iterate over real-time task updates."""
        task = await self.queue_manager.get_task_status(task_id)
        if not task:
            yield {"error": "Task not found"}
            return
        
        # Subscribe to FAL updates
        handler = await fal_client.submit_async(
            task.model,
            arguments=task.metadata["arguments"]
        )
        task.request_id = handler.request_id
        
        # Stream updates
        async for event in handler.iter_events(with_logs=True):
            update = await self._process_fal_event(event, task)
            yield update
    
    async def _process_fal_event(
        self,
        event: Any,
        task: QueuedTask
    ) -> Dict[str, Any]:
        """Process FAL event and update task status."""
        update = {
            "task_id": task.id,
            "timestamp": datetime.now().isoformat()
        }
        
        if isinstance(event, fal_client.Queued):
            task.status = QueueStatus.QUEUED
            task.queue_position = event.position
            update.update({
                "status": "queued",
                "queue_position": event.position,
                "message": f"Queued at position {event.position}"
            })
        
        elif isinstance(event, fal_client.InProgress):
            task.status = QueueStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            # Extract progress if available
            if hasattr(event, 'progress'):
                task.progress_percentage = event.progress
            
            # Process logs
            if hasattr(event, 'logs'):
                new_logs = event.logs[len(task.logs):]
                task.logs.extend(new_logs)
                
                # Extract progress from logs if available
                for log in new_logs:
                    if isinstance(log, dict) and 'progress' in log:
                        task.progress_percentage = log['progress']
            
            update.update({
                "status": "in_progress",
                "progress": task.progress_percentage,
                "logs": new_logs if 'new_logs' in locals() else []
            })
        
        elif isinstance(event, fal_client.Completed):
            task.status = QueueStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = event.result
            task.progress_percentage = 100.0
            
            update.update({
                "status": "completed",
                "result": event.result,
                "duration": (task.completed_at - task.created_at).total_seconds()
            })
        
        return update
```

### 3. New Queue Status Tool (`src/mcp_server/tools/queue/get_queue_status.py`)

```python
from typing import Dict, Any, Optional, List

async def get_queue_status(
    task_id: Optional[str] = None,
    project_id: Optional[str] = None,
    status_filter: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get queue status for tasks.
    
    Args:
        task_id: Specific task ID to check
        project_id: Filter by project ID
        status_filter: Filter by status (queued, in_progress, etc.)
    
    Returns:
        Queue status information
    """
    queue_manager = fal_service.queue_manager
    
    if task_id:
        # Get specific task
        task = await queue_manager.get_task_status(task_id)
        if not task:
            return create_error_response(
                ErrorType.NOT_FOUND,
                f"Task {task_id} not found"
            )
        
        return {
            "success": True,
            "task": task.dict()
        }
    
    # Get all tasks with filters
    all_tasks = await queue_manager.get_all_tasks()
    
    # Apply filters
    if project_id:
        all_tasks = [t for t in all_tasks if t.project_id == project_id]
    
    if status_filter:
        all_tasks = [t for t in all_tasks if t.status in status_filter]
    
    # Group by status
    by_status = {}
    for task in all_tasks:
        status = task.status
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(task.dict())
    
    return {
        "success": True,
        "total_tasks": len(all_tasks),
        "by_status": by_status,
        "active_count": len([t for t in all_tasks if t.status in [QueueStatus.QUEUED, QueueStatus.IN_PROGRESS]])
    }
```

### 4. Update Video Generation Tool

```python
# In generate_video_from_image.py

async def generate_video_from_image(
    image_url: str,
    motion_prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    model: Optional[str] = None,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None,
    use_queue: bool = True,  # New parameter
    return_queue_id: bool = False,  # New parameter
    **kwargs
) -> Dict[str, Any]:
    """
    Generate video with optional queue tracking.
    
    Additional Args:
        use_queue: Whether to use queued processing (default: True)
        return_queue_id: Return queue ID instead of waiting for result
    """
    
    # ... validation code ...
    
    if use_queue:
        # Submit to queue
        task = await fal_service.submit_generation(
            model_id=model_config["fal_model_id"],
            arguments={
                "image_url": processed_image_url,
                "prompt": motion_prompt,
                "duration": str(duration),
                "aspect_ratio": aspect_ratio,
                **model_specific_params
            },
            task_type="video",
            project_id=project_id,
            scene_id=scene_id
        )
        
        if return_queue_id:
            # Return immediately with queue ID
            return {
                "success": True,
                "queued": True,
                "queue_id": task.id,
                "message": "Video generation queued",
                "estimated_cost": cost
            }
        
        # Wait for completion with progress updates
        async for update in fal_service.iter_task_updates(task.id):
            if update.get("status") == "completed":
                result = update.get("result", {})
                # Process result as before...
                break
            elif update.get("status") == "failed":
                return create_error_response(
                    ErrorType.GENERATION_ERROR,
                    update.get("error", "Generation failed")
                )
    else:
        # Use existing synchronous method
        result = await fal_service.generate_video_from_image(
            image_url=processed_image_url,
            motion_prompt=motion_prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            model=model,
            **kwargs
        )
```

### 5. MCP Resource for Queue Monitoring

```python
# In src/mcp_server/resources/get_queue_status.py

async def get_queue_status_resource(uri: str) -> Dict[str, Any]:
    """
    Get queue status as MCP resource.
    
    URIs:
    - queue://status - Overall queue status
    - queue://task/{task_id} - Specific task status
    - queue://project/{project_id} - Project queue status
    """
    parts = uri.split("/")
    
    if len(parts) == 2 and parts[1] == "status":
        # Overall status
        status = await get_queue_status()
        return {
            "name": "Queue Status",
            "mimeType": "application/json",
            "text": json.dumps(status, indent=2)
        }
    
    elif len(parts) == 3 and parts[1] == "task":
        # Specific task
        task_id = parts[2]
        status = await get_queue_status(task_id=task_id)
        return {
            "name": f"Task {task_id} Status",
            "mimeType": "application/json",
            "text": json.dumps(status, indent=2)
        }
    
    elif len(parts) == 3 and parts[1] == "project":
        # Project tasks
        project_id = parts[2]
        status = await get_queue_status(project_id=project_id)
        return {
            "name": f"Project {project_id} Queue",
            "mimeType": "application/json",
            "text": json.dumps(status, indent=2)
        }
```

## Implementation Benefits

1. **Real-time Updates**: Users can track queue position and progress
2. **Better UX**: No more waiting without feedback
3. **Cancellation**: Ability to cancel long-running tasks
4. **Resource Management**: Better tracking of active tasks
5. **Error Recovery**: Clear status for failed tasks
6. **Batch Processing**: Submit multiple tasks and track them

## Usage Examples

### Async Queue Submission
```python
# Submit and get queue ID immediately
result = await mcp__video-agent__generate_video_from_image({
    "image_url": "image.jpg",
    "motion_prompt": "zoom in slowly",
    "duration": 10,
    "return_queue_id": True
})
# Returns: {"queued": True, "queue_id": "abc123"}

# Check status
status = await mcp__video-agent__get_queue_status({
    "task_id": "abc123"
})
# Returns: {"status": "in_progress", "queue_position": 2, "progress": 45}
```

### Batch Processing
```python
# Submit multiple videos
queue_ids = []
for scene in scenes:
    result = await generate_video({
        "image_url": scene.image,
        "motion_prompt": scene.motion,
        "return_queue_id": True
    })
    queue_ids.append(result["queue_id"])

# Monitor all
status = await get_queue_status({
    "project_id": project.id
})
# Returns status of all project tasks
```

## Migration Strategy

1. **Phase 1**: Implement queue models and manager
2. **Phase 2**: Enhance FAL client with queue tracking
3. **Phase 3**: Add queue status tools and resources
4. **Phase 4**: Update existing tools to use queue system
5. **Phase 5**: Add batch processing capabilities

Each phase maintains backward compatibility.