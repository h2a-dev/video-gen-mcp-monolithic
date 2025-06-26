"""Queue status models and manager for tracking generation tasks."""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4
import asyncio
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
    request_id: str = ""  # FAL request ID, set after submission
    project_id: Optional[str] = None
    scene_id: Optional[str] = None
    task_type: str  # "video", "image", "audio", "music", "speech"
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
    
    class Config:
        use_enum_values = True
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        return (datetime.now() - self.created_at).total_seconds()
    
    def get_processing_time(self) -> Optional[float]:
        """Get processing time in seconds (from start to completion)."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return None
    
    def to_summary(self) -> Dict[str, Any]:
        """Return a summary view of the task."""
        return {
            "id": self.id,
            "task_type": self.task_type,
            "model": self.model,
            "status": self.status,
            "queue_position": self.queue_position,
            "progress": self.progress_percentage,
            "elapsed_time": self.get_elapsed_time(),
            "project_id": self.project_id,
            "scene_id": self.scene_id
        }


class QueueManager:
    """Manages all queued tasks."""
    
    def __init__(self):
        self._tasks: Dict[str, QueuedTask] = {}
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._task_lock = asyncio.Lock()
    
    async def create_task(
        self,
        task_type: str,
        model: str,
        arguments: Dict[str, Any],
        project_id: Optional[str] = None,
        scene_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QueuedTask:
        """Create a new task (doesn't start processing)."""
        task = QueuedTask(
            project_id=project_id,
            scene_id=scene_id,
            task_type=task_type,
            model=model,
            metadata={"arguments": arguments, **(metadata or {})}
        )
        
        async with self._task_lock:
            self._tasks[task.id] = task
        
        return task
    
    async def update_task(self, task_id: str, **updates) -> Optional[QueuedTask]:
        """Update task fields."""
        async with self._task_lock:
            task = self._tasks.get(task_id)
            if task:
                for key, value in updates.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
            return task
    
    async def get_task(self, task_id: str) -> Optional[QueuedTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    async def get_all_tasks(
        self,
        project_id: Optional[str] = None,
        status_filter: Optional[List[QueueStatus]] = None
    ) -> List[QueuedTask]:
        """Get all tasks with optional filters."""
        tasks = list(self._tasks.values())
        
        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]
        
        if status_filter:
            tasks = [t for t in tasks if t.status in status_filter]
        
        # Sort by creation time (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a queued or running task."""
        async with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            # Cancel asyncio task if running
            if task_id in self._active_tasks:
                self._active_tasks[task_id].cancel()
                del self._active_tasks[task_id]
            
            # Update task status
            task.status = QueueStatus.CANCELLED
            task.completed_at = datetime.now()
            task.error_message = "Task cancelled by user"
            
            return True
    
    async def register_active_task(self, task_id: str, asyncio_task: asyncio.Task):
        """Register an asyncio task for cancellation support."""
        async with self._task_lock:
            self._active_tasks[task_id] = asyncio_task
    
    async def unregister_active_task(self, task_id: str):
        """Remove asyncio task registration."""
        async with self._task_lock:
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get overall queue statistics."""
        all_tasks = list(self._tasks.values())
        
        stats = {
            "total_tasks": len(all_tasks),
            "by_status": {},
            "by_type": {},
            "active_count": 0,
            "average_wait_time": 0,
            "average_processing_time": 0
        }
        
        # Count by status
        for status in QueueStatus:
            count = len([t for t in all_tasks if t.status == status])
            stats["by_status"][status] = count
        
        # Count by type
        for task in all_tasks:
            if task.task_type not in stats["by_type"]:
                stats["by_type"][task.task_type] = 0
            stats["by_type"][task.task_type] += 1
        
        # Active count
        stats["active_count"] = len([
            t for t in all_tasks 
            if t.status in [QueueStatus.QUEUED, QueueStatus.IN_PROGRESS]
        ])
        
        # Calculate average times
        completed_tasks = [t for t in all_tasks if t.status == QueueStatus.COMPLETED]
        if completed_tasks:
            total_wait = sum(
                (t.started_at - t.created_at).total_seconds() 
                for t in completed_tasks 
                if t.started_at
            )
            total_processing = sum(
                t.get_processing_time() or 0 
                for t in completed_tasks
            )
            
            stats["average_wait_time"] = total_wait / len(completed_tasks)
            stats["average_processing_time"] = total_processing / len(completed_tasks)
        
        return stats
    
    async def cleanup_old_tasks(self, hours: int = 24):
        """Remove completed/failed tasks older than specified hours."""
        cutoff = datetime.now().timestamp() - (hours * 3600)
        
        async with self._task_lock:
            to_remove = []
            for task_id, task in self._tasks.items():
                if task.status in [QueueStatus.COMPLETED, QueueStatus.FAILED, QueueStatus.CANCELLED]:
                    if task.created_at.timestamp() < cutoff:
                        to_remove.append(task_id)
            
            for task_id in to_remove:
                del self._tasks[task_id]
        
        return len(to_remove)


# Global queue manager instance
queue_manager = QueueManager()