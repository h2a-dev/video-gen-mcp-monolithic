"""List projects tool implementation."""

from typing import Dict, Any
from ...models import ProjectManager, CURRENT_PROJECT_ID


async def list_projects() -> Dict[str, Any]:
    """List all video projects with their current status."""
    try:
        projects = ProjectManager.list_projects()
        
        project_list = []
        for project in projects:
            project_data = {
                "id": project.id,
                "title": project.title,
                "platform": project.platform,
                "status": project.status,
                "scenes": len(project.scenes),
                "duration": project.calculate_duration(),
                "target_duration": project.target_duration,
                "cost": project.calculate_cost(),
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()
            }
            
            # Mark current project
            if project.id == CURRENT_PROJECT_ID:
                project_data["is_current"] = True
                
            project_list.append(project_data)
        
        # Sort by updated_at descending
        project_list.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return {
            "success": True,
            "projects": project_list,
            "total": len(project_list),
            "current_project_id": CURRENT_PROJECT_ID
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }