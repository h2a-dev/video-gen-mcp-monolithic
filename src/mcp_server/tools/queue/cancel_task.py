"""Cancel a queued task tool."""

from typing import Dict, Any
from ...models import queue_manager
from ...utils import create_error_response, ErrorType


async def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    Cancel a queued or running task.
    
    Args:
        task_id: Task ID to cancel
    
    Returns:
        Cancellation result
    """
    
    # Get task to check if it exists
    task = await queue_manager.get_task(task_id)
    if not task:
        return create_error_response(
            ErrorType.NOT_FOUND,
            f"Task {task_id} not found"
        )
    
    # Check if task is already completed
    if task.status in ["completed", "failed", "cancelled"]:
        return create_error_response(
            ErrorType.INVALID_OPERATION,
            f"Cannot cancel task in {task.status} status",
            details={"current_status": task.status}
        )
    
    # Cancel the task
    success = await queue_manager.cancel_task(task_id)
    
    if success:
        return {
            "success": True,
            "message": f"Task {task_id} cancelled successfully",
            "task_id": task_id,
            "previous_status": task.status
        }
    else:
        return create_error_response(
            ErrorType.INTERNAL_ERROR,
            f"Failed to cancel task {task_id}"
        )


# Tool metadata for MCP
tool_definition = {
    "name": "cancel_task",
    "description": "Cancel a queued or running generation task",
    "inputSchema": {
        "type": "object",
        "required": ["task_id"],
        "properties": {
            "task_id": {
                "type": "string",
                "description": "Task ID to cancel"
            }
        }
    }
}