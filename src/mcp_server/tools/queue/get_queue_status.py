"""Get queue status tool for monitoring generation tasks."""

from typing import Dict, Any, Optional, List
from ...models import queue_manager, QueueStatus
from ...utils import create_error_response, ErrorType


async def get_queue_status(
    task_id: Optional[str] = None,
    project_id: Optional[str] = None,
    status_filter: Optional[List[str]] = None,
    include_completed: bool = False
) -> Dict[str, Any]:
    """
    Get queue status for generation tasks.
    
    Args:
        task_id: Specific task ID to check
        project_id: Filter by project ID
        status_filter: Filter by status (queued, in_progress, completed, failed, cancelled)
        include_completed: Include completed/failed/cancelled tasks (default: False)
    
    Returns:
        Queue status information with task details
    """
    
    if task_id:
        # Get specific task
        task = await queue_manager.get_task(task_id)
        if not task:
            return create_error_response(
                ErrorType.NOT_FOUND,
                f"Task {task_id} not found"
            )
        
        return {
            "success": True,
            "task": {
                "id": task.id,
                "request_id": task.request_id,
                "task_type": task.task_type,
                "model": task.model,
                "status": task.status,
                "queue_position": task.queue_position,
                "progress": task.progress_percentage,
                "elapsed_time": task.get_elapsed_time(),
                "processing_time": task.get_processing_time(),
                "project_id": task.project_id,
                "scene_id": task.scene_id,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error": task.error_message,
                "logs": task.logs[-10:] if task.logs else []  # Last 10 logs
            }
        }
    
    # Get all tasks with filters
    # Convert string status filter to enums
    status_enums = None
    if status_filter:
        try:
            status_enums = [QueueStatus(s) for s in status_filter]
        except ValueError as e:
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                f"Invalid status filter: {e}",
                details={"valid_statuses": list(QueueStatus)}
            )
    
    # If not including completed, filter to active tasks only
    if not include_completed and not status_enums:
        status_enums = [QueueStatus.QUEUED, QueueStatus.IN_PROGRESS]
    
    all_tasks = await queue_manager.get_all_tasks(
        project_id=project_id,
        status_filter=status_enums
    )
    
    # Get queue statistics
    stats = await queue_manager.get_queue_stats()
    
    # Group tasks by status
    by_status = {}
    for task in all_tasks:
        status = task.status
        if status not in by_status:
            by_status[status] = []
        by_status[status].append({
            "id": task.id,
            "task_type": task.task_type,
            "model": task.model,
            "queue_position": task.queue_position,
            "progress": task.progress_percentage,
            "elapsed_time": task.get_elapsed_time(),
            "project_id": task.project_id,
            "created_at": task.created_at.isoformat()
        })
    
    return {
        "success": True,
        "total_tasks": len(all_tasks),
        "by_status": by_status,
        "statistics": {
            "active_count": stats["active_count"],
            "average_wait_time": round(stats["average_wait_time"], 2),
            "average_processing_time": round(stats["average_processing_time"], 2),
            "by_type": stats["by_type"]
        },
        "filters_applied": {
            "project_id": project_id,
            "status_filter": status_filter,
            "include_completed": include_completed
        }
    }


# Tool metadata for MCP
tool_definition = {
    "name": "get_queue_status",
    "description": "Get status of queued generation tasks",
    "inputSchema": {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "Specific task ID to check"
            },
            "project_id": {
                "type": "string",
                "description": "Filter by project ID"
            },
            "status_filter": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter by status (queued, in_progress, completed, failed, cancelled)"
            },
            "include_completed": {
                "type": "boolean",
                "description": "Include completed/failed/cancelled tasks",
                "default": False
            }
        }
    }
}