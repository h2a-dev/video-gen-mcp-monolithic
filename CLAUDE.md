# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Video Agent MCP (Model Context Protocol) server that provides AI-powered video creation capabilities through FastMCP 2.0. The server integrates with FAL AI services to generate images, videos, music, and speech, then assembles them into complete videos optimized for various platforms.

## Key Commands

### Development
- **Run server**: `uv run python main.py`
- **Install dependencies**: `uv sync` or `uv pip install -r requirements.txt`
- **Install package in dev mode**: `uv pip install -e .`
- **Run via script entry**: `uv run video-agent-mcp` (after installing package)
- **Install dev dependencies**: `uv sync --dev` or `uv pip install -e ".[dev]"`

### Testing
- **Test queue system**: `python test_queue.py`
- **Test audio sync**: `python test_audio_duration_fix.py`
- **Test end video**: `python test_end_video.py`
- **Run pytest suite**: `uv run pytest` (if tests exist)

### Code Quality
- **Lint code**: `uv run ruff check .`
- **Format code**: `uv run ruff format .`
- **Type checking**: `uv run mypy .` (optional)

### Environment Setup
Required environment variables:
- `FALAI_API_KEY` - FAL AI API key (check with `echo $FALAI_API_KEY`)

Optional environment variables:
- `VIDEO_AGENT_STORAGE` - Storage directory (default: ./storage)
- `DEFAULT_IMAGE_MODEL` - Default image model (default: imagen4)
- `DEFAULT_VIDEO_MODEL` - Default video model (default: kling_2.1, options: hailuo_02)
- `YOUTUBE_API_KEY` or `GOOGLE_API_KEY` - YouTube Data API v3 key for search functionality only

For API keys, check `.env` or `.mcp.json` files.

### YouTube Integration Setup

The server supports two types of YouTube functionality:

1. **YouTube Search/Analysis** (requires `GOOGLE_API_KEY`):
   - Search videos
   - Get video categories
   - Analyze videos with Gemini

2. **YouTube Upload** (requires OAuth2 setup):
   - Upload videos to YouTube
   - Requires `client_secrets.json` file in project root
   - Uses OAuth2 flow for authentication

#### Setting up YouTube Upload:

1. **Create OAuth2 Credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing one
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials (Desktop application type)
   - Download credentials as `client_secrets.json`
   - Place in project root directory

2. **First-time Authentication**:
   - When using `youtube_publish` tool for the first time
   - Browser will open for Google account authorization
   - Grant permissions to upload videos
   - Token saved as `token.json` for future use

3. **Required OAuth Scopes**:
   - `https://www.googleapis.com/auth/youtube.upload`

**Note**: YouTube upload functionality works independently of search functionality. You don't need `GOOGLE_API_KEY` for uploading videos.

## Architecture

The codebase follows a modular architecture under `video-gen-mcp-monolithic/`:

```
main.py                     # Entry point that loads dotenv and runs the MCP server
src/mcp_server/
├── server.py              # FastMCP server with tool/resource/prompt registration
├── config/                # Configuration modules
│   ├── settings.py        # Core settings, paths, and model defaults
│   ├── platforms.py       # Platform specifications (YouTube, TikTok, etc.)
│   └── pricing.py         # Cost tracking for AI services
├── models/                # Pydantic data models
│   ├── schemas.py         # Core data models for project, scene, generation
│   └── queue_status.py    # Queue system models
├── services/              # External service integrations
│   ├── fal_client.py      # FAL AI API client wrapper
│   ├── ffmpeg_wrapper.py  # FFmpeg operations
│   ├── youtube_service.py # YouTube API integration
│   └── asset_storage.py   # File management service
├── tools/                 # MCP tool implementations (20+ tools)
│   ├── project/           # Project management tools
│   ├── generation/        # Content generation tools
│   ├── assembly/          # Video assembly tools
│   ├── utility/           # Helper tools including YouTube tools
│   └── queue/             # Queue management tools
├── resources/             # Dynamic resource handlers (5 resources)
├── prompts/               # Interactive workflow prompts (4 prompts)
└── utils/                 # Utility functions and helpers
```

## Key Implementation Details

### Tool Registration Pattern
Tools are registered using the FastMCP decorator pattern:
```python
from mcp_server.server import mcp

@mcp.tool()
def tool_name(param: type) -> dict:
    """Tool description"""
    # Implementation
```

### Queue System
The server implements a task queue for long-running operations:
- Queue service manages task lifecycle (queued → in_progress → completed/failed)
- Generation tools can use `use_queue=True` for better tracking
- Queue status available via tool and resource
- Supports cancellation and progress tracking

### Platform Support
The server supports 9 platforms with optimized settings:
- YouTube (16:9, up to 12 hours), YouTube Shorts (9:16, max 60s)
- TikTok (9:16, up to 10 minutes), Instagram Reel/Post (9:16/1:1)
- Twitter/X (16:9, max 140s), LinkedIn (16:9, up to 10 minutes)
- Facebook (flexible, up to 4 hours), Custom (flexible settings)

Each platform has specific aspect ratios, durations, and quality settings defined in `config/platforms.py`.

### Cost Tracking
All AI operations track costs in `services/fal_client.py` using pricing from `config/pricing.py`. Projects maintain cumulative cost tracking with detailed breakdowns.

### Storage Organization
Files are organized under the storage directory:
- `storage/projects/{project_id}/` - Project files and final videos
- `storage/projects/{project_id}/assets/` - Generated assets
- `storage/assets/logos/` - Branding assets (h2a.png, h2a_end.mp4)
- `storage/temp/` - Temporary files

## Working with the Codebase

### Adding New Tools
1. Create tool file in `src/mcp_server/tools/{category}/`
2. Implement tool function with FastMCP decorator
3. Import in `src/mcp_server/server.py`
4. Tools should follow the `_impl` suffix pattern for implementation functions
5. **Parameter Flexibility**: When accepting list parameters, consider accepting both native lists and JSON strings to handle different agent serialization approaches:
   ```python
   from typing import Union
   
   async def tool_name(
       items: Optional[Union[List[str], str]] = None
   ) -> Dict[str, Any]:
       # Handle both formats
       if items is not None:
           if isinstance(items, str):
               try:
                   items = json.loads(items)
               except json.JSONDecodeError:
                   items = [items]  # Single item
   ```

### Error Handling
- Use `utils/error_helpers.py` for consistent error formatting
- All tools should handle exceptions gracefully
- Return structured error responses with helpful messages
- Implement retry logic with exponential backoff for API calls

### Async Operations
- Most operations are async (use `async def`)
- File operations use `aiofiles`
- HTTP requests use `httpx` async client
- FFmpeg operations run in thread pool executor to avoid blocking

### Testing Changes
When modifying generation or queue functionality:
1. Run `python test_queue.py` to verify queue system
2. Test individual tools through the MCP interface
3. Check cost calculations are accurate
4. Verify audio/video sync with `test_audio_duration_fix.py`
5. For complex video assembly, test with `test_end_video.py`

### Common Development Workflows

#### Running the server in Claude Desktop
1. Update `claude_desktop_config.json` with absolute path to project
2. Ensure FALAI_API_KEY is set in the env section
3. Restart Claude Desktop to load the MCP server
4. Check server status with `get_server_info` tool

#### Adding a new generation model
1. Update `config/pricing.py` with model pricing
2. Add model to appropriate constants in `config/settings.py`
3. Update relevant generation tool in `tools/generation/`
4. Test with queue system enabled (`use_queue=True`)

### YouTube Integration
The server includes comprehensive YouTube support:
- OAuth 2.0 authentication flow for publishing
- Video search and analysis using Gemini API
- Category fetching for proper metadata
- Requires `client_secrets.json` for OAuth

## Dependencies and Prerequisites

- **Python 3.11+** (specified in `.python-version`)
- **FFmpeg** installed on the system for video assembly
- **uv** package manager (recommended) or pip
- **FAL AI API key** for all generation operations

## Important Notes

- The server requires FFmpeg installed on the system for video assembly
- All generation operations require valid FAL AI API key
- The codebase uses FastMCP 2.0 (migrated from MCP 1.x, no backward compatibility)
- Queue system provides better visibility into long-running tasks
- Platform specifications ensure videos meet platform requirements
- YouTube features require additional API keys and OAuth setup (see YOUTUBE_SETUP.md)
- Cost tracking is automatic for all AI operations
- The project uses Ruff for linting/formatting (configured in pyproject.toml)
- Test files are in the root directory (test_*.py) rather than a tests/ folder
- The pyproject.toml includes `[tool.hatch.build.targets.wheel]` section to specify package location
- When working with YouTube tools, check both `youtube_search.py` and tools in `utility/` folder