"""Queue status resource for MCP monitoring."""

import json
from datetime import datetime
from typing import Dict, Any
from ..models import queue_manager


async def get_queue_status_resource(uri_parts: list[str]) -> Dict[str, Any]:
    """
    Get queue status as MCP resource.
    
    URIs:
    - queue://status - Overall queue status
    - queue://task/{task_id} - Specific task status
    - queue://project/{project_id} - Project queue status
    """
    
    if len(uri_parts) == 1 and uri_parts[0] == "status":
        # Overall queue status
        stats = await queue_manager.get_queue_stats()
        all_tasks = await queue_manager.get_all_tasks()
        
        # Format active tasks
        active_tasks = [
            {
                "id": task.id,
                "type": task.task_type,
                "model": task.model,
                "status": task.status,
                "queue_position": task.queue_position,
                "progress": task.progress_percentage,
                "elapsed_time": task.get_elapsed_time()
            }
            for task in all_tasks
            if task.status in ["queued", "in_progress"]
        ]
        
        content = {
            "statistics": stats,
            "active_tasks": active_tasks,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "name": "Queue Status",
            "mimeType": "application/json",
            "text": json.dumps(content, indent=2)
        }
    
    elif len(uri_parts) == 2 and uri_parts[0] == "task":
        # Specific task status
        task_id = uri_parts[1]
        task = await queue_manager.get_task(task_id)
        
        if not task:
            return {
                "name": f"Task {task_id} Not Found",
                "mimeType": "application/json",
                "text": json.dumps({"error": f"Task {task_id} not found"}, indent=2)
            }
        
        content = {
            "task": task.dict(),
            "summary": task.to_summary(),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "name": f"Task {task_id} Status",
            "mimeType": "application/json",
            "text": json.dumps(content, indent=2, default=str)
        }
    
    elif len(uri_parts) == 2 and uri_parts[0] == "project":
        # Project queue status
        project_id = uri_parts[1]
        project_tasks = await queue_manager.get_all_tasks(project_id=project_id)
        
        # Group by status
        by_status = {}
        for task in project_tasks:
            status = task.status
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(task.to_summary())
        
        content = {
            "project_id": project_id,
            "total_tasks": len(project_tasks),
            "by_status": by_status,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "name": f"Project {project_id} Queue",
            "mimeType": "application/json",
            "text": json.dumps(content, indent=2, default=str)
        }
    
    else:
        return {
            "name": "Invalid Queue URI",
            "mimeType": "text/plain",
            "text": f"Invalid queue URI: queue://{'/'.join(uri_parts)}"
        }