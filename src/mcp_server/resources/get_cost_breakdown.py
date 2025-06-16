"""Get cost breakdown resource implementation."""

from typing import Dict, Any
from ..models import ProjectManager
from ..config import PRICING


async def get_cost_breakdown(project_id: str) -> Dict[str, Any]:
    """Get detailed cost breakdown for a project."""
    try:
        project = ProjectManager.get_project(project_id)
        
        # Calculate costs by category
        costs = {
            "images": {"count": 0, "total": 0.0, "details": []},
            "videos": {"count": 0, "total": 0.0, "details": []},
            "music": {"count": 0, "total": 0.0, "details": []},
            "speech": {"count": 0, "total": 0.0, "details": []}
        }
        
        # Process scene assets
        for scene_idx, scene in enumerate(project.scenes):
            for asset in scene.assets:
                if asset.type == "image":
                    costs["images"]["count"] += 1
                    costs["images"]["total"] += asset.cost
                    costs["images"]["details"].append({
                        "scene": scene_idx + 1,
                        "prompt": asset.metadata.get("prompt", "")[:50] + "...",
                        "cost": asset.cost
                    })
                elif asset.type == "video":
                    costs["videos"]["count"] += 1
                    costs["videos"]["total"] += asset.cost
                    costs["videos"]["details"].append({
                        "scene": scene_idx + 1,
                        "duration": asset.metadata.get("duration", 0),
                        "cost": asset.cost
                    })
        
        # Process global audio tracks
        for track in project.global_audio_tracks:
            if track.type == "music":
                costs["music"]["count"] += 1
                costs["music"]["total"] += track.cost
                costs["music"]["details"].append({
                    "prompt": track.metadata.get("prompt", "")[:50] + "...",
                    "duration": track.metadata.get("duration", 0),
                    "cost": track.cost
                })
            elif track.type == "speech":
                costs["speech"]["count"] += 1
                costs["speech"]["total"] += track.cost
                costs["speech"]["details"].append({
                    "characters": track.metadata.get("character_count", 0),
                    "cost": track.cost
                })
        
        # Calculate totals
        total_cost = sum(cat["total"] for cat in costs.values())
        
        # Projected costs for completion
        projected_costs = _calculate_projected_costs(project, costs)
        
        return {
            "mimetype": "application/json",
            "data": {
                "project_id": project_id,
                "current_costs": {
                    "breakdown": costs,
                    "total": round(total_cost, 3)
                },
                "projected_costs": projected_costs,
                "pricing_reference": {
                    "images": PRICING["imagen4"]["per_image"],
                    "video_per_second": PRICING["kling_2.1"]["per_second"],
                    "music_per_30s": PRICING["lyria2"]["per_30_seconds"],
                    "speech_per_1000_chars": PRICING["minimax_speech"]["per_1000_chars"]
                },
                "cost_saving_tips": _get_cost_saving_tips(project, costs)
            }
        }
        
    except Exception as e:
        return {
            "mimetype": "application/json",
            "data": {
                "error": str(e)
            }
        }


def _calculate_projected_costs(project, current_costs):
    """Calculate projected costs to complete the project."""
    projected = {}
    
    # Scenes without videos
    scenes_needing_video = sum(
        1 for scene in project.scenes 
        if not any(a.type == "video" for a in scene.assets)
    )
    
    if scenes_needing_video > 0:
        # Assume average 7.5 seconds per scene
        projected["videos_needed"] = {
            "count": scenes_needing_video,
            "estimated_cost": scenes_needing_video * 7.5 * PRICING["kling_2.1"]["per_second"]
        }
    
    # Check if music is needed
    if current_costs["music"]["count"] == 0 and project.target_duration:
        projected["music_needed"] = {
            "duration": project.target_duration,
            "estimated_cost": PRICING["lyria2"]["per_30_seconds"] * ((project.target_duration + 29) // 30)
        }
    
    # Total projected
    projected["total_additional"] = sum(
        item.get("estimated_cost", 0) 
        for item in projected.values() 
        if isinstance(item, dict)
    )
    
    projected["total_project_cost"] = round(
        current_costs["total"] + projected.get("total_additional", 0), 3
    )
    
    return projected


def _get_cost_saving_tips(project, costs):
    """Generate cost-saving recommendations."""
    tips = []
    
    # Video duration optimization
    avg_video_duration = sum(
        asset.metadata.get("duration", 0) 
        for scene in project.scenes 
        for asset in scene.assets 
        if asset.type == "video"
    ) / max(costs["videos"]["count"], 1)
    
    if avg_video_duration > 7:
        tips.append("Consider using 5-second videos instead of 10-second to reduce costs by 50%")
    
    # Image reuse
    if costs["images"]["count"] > len(project.scenes) * 1.5:
        tips.append("Reuse images across scenes with different animations to reduce generation costs")
    
    # Audio optimization
    if project.target_duration and project.target_duration < 60:
        tips.append("For videos under 60 seconds, consider skipping background music")
    
    return tips