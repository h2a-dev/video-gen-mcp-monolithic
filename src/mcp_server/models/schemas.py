"""Core data structures for the Video Agent MCP server."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4
from pydantic import BaseModel, Field


class AssetType(str, Enum):
    """Types of assets in a video project."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MUSIC = "music"
    SPEECH = "speech"
    SUBTITLE = "subtitle"


class AssetSource(str, Enum):
    """Source of an asset."""
    GENERATED = "generated"
    UPLOADED = "uploaded"
    STOCK = "stock"
    TEMPLATE = "template"


class ProjectStatus(str, Enum):
    """Status of a video project."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationStatus(str, Enum):
    """Status of an asset generation task."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Asset(BaseModel):
    """Represents a media asset in the project."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: AssetType
    source: AssetSource
    url: Optional[str] = None
    local_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    generation_params: Optional[Dict[str, Any]] = None
    cost: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class Scene(BaseModel):
    """Represents a scene in the video timeline."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    order: int
    duration: int  # in seconds
    description: str
    assets: List[Asset] = Field(default_factory=list)
    transitions: Dict[str, Any] = Field(default_factory=dict)
    motion_params: Dict[str, Any] = Field(default_factory=dict)
    audio_tracks: List[str] = Field(default_factory=list)  # Asset IDs
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class VideoProject(BaseModel):
    """Represents a complete video project."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str = ""
    platform: str
    target_duration: Optional[int] = None  # in seconds
    actual_duration: int = 0  # calculated from scenes
    aspect_ratio: str = "16:9"
    scenes: List[Scene] = Field(default_factory=list)
    global_audio_tracks: List[Asset] = Field(default_factory=list)  # Background music, etc.
    script: Optional[str] = None
    total_cost: float = 0.0
    status: ProjectStatus = ProjectStatus.DRAFT
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True
    
    def calculate_duration(self) -> int:
        """Calculate total duration from scenes."""
        return sum(scene.duration for scene in self.scenes)
    
    def calculate_cost(self) -> float:
        """Calculate total cost from all assets."""
        cost = 0.0
        # Cost from scene assets
        for scene in self.scenes:
            cost += sum(asset.cost for asset in scene.assets)
        # Cost from global audio tracks
        cost += sum(track.cost for track in self.global_audio_tracks)
        return round(cost, 3)


class GenerationTask(BaseModel):
    """Represents an asset generation task."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    scene_id: Optional[str] = None
    asset_type: AssetType
    params: Dict[str, Any]
    status: GenerationStatus = GenerationStatus.PENDING
    result: Optional[Asset] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


# Global storage for projects (in-memory for MVP)
PROJECTS: Dict[str, VideoProject] = {}
CURRENT_PROJECT_ID: Optional[str] = None
GENERATION_TASKS: Dict[str, GenerationTask] = {}


class ProjectManager:
    """Static methods for project management."""
    
    @staticmethod
    def create_project(**kwargs) -> VideoProject:
        """Create a new project."""
        project = VideoProject(**kwargs)
        PROJECTS[project.id] = project
        global CURRENT_PROJECT_ID
        CURRENT_PROJECT_ID = project.id
        return project
    
    @staticmethod
    def get_project(project_id: str) -> VideoProject:
        """Get a project by ID."""
        if project_id not in PROJECTS:
            raise ValueError(f"Project {project_id} not found")
        return PROJECTS[project_id]
    
    @staticmethod
    def get_current_project() -> Optional[VideoProject]:
        """Get the current active project."""
        if CURRENT_PROJECT_ID and CURRENT_PROJECT_ID in PROJECTS:
            return PROJECTS[CURRENT_PROJECT_ID]
        return None
    
    @staticmethod
    def list_projects() -> List[VideoProject]:
        """List all projects."""
        return list(PROJECTS.values())
    
    @staticmethod
    def update_project(project_id: str, **updates) -> VideoProject:
        """Update a project."""
        project = ProjectManager.get_project(project_id)
        for key, value in updates.items():
            if hasattr(project, key):
                setattr(project, key, value)
        project.updated_at = datetime.now()
        return project
    
    @staticmethod
    def add_scene(project_id: str, scene: Scene) -> Scene:
        """Add a scene to a project."""
        project = ProjectManager.get_project(project_id)
        scene.order = len(project.scenes)
        project.scenes.append(scene)
        project.actual_duration = project.calculate_duration()
        project.updated_at = datetime.now()
        return scene
    
    @staticmethod
    def clear_all_projects():
        """Clear all projects from memory."""
        global CURRENT_PROJECT_ID
        PROJECTS.clear()
        GENERATION_TASKS.clear()
        CURRENT_PROJECT_ID = None
        return {"message": "All projects cleared"}