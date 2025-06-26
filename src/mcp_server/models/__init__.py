"""Models module for Video Agent MCP server."""

from .schemas import (
    AssetType,
    AssetSource,
    ProjectStatus,
    GenerationStatus,
    Asset,
    Scene,
    VideoProject,
    GenerationTask,
    ProjectManager,
    PROJECTS,
    CURRENT_PROJECT_ID,
    GENERATION_TASKS
)

from .queue_status import (
    QueueStatus,
    QueuedTask,
    QueueManager,
    queue_manager
)

__all__ = [
    "AssetType",
    "AssetSource",
    "ProjectStatus",
    "GenerationStatus",
    "Asset",
    "Scene",
    "VideoProject",
    "GenerationTask",
    "ProjectManager",
    "PROJECTS",
    "CURRENT_PROJECT_ID",
    "GENERATION_TASKS",
    "QueueStatus",
    "QueuedTask",
    "QueueManager",
    "queue_manager"
]