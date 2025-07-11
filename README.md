# Video Agent MCP Server

A comprehensive Model Context Protocol (MCP) server for AI-powered video creation. This server provides tools, resources, and prompts to guide AI agents through complete video production workflows.

## Features

- **Unified Interface**: Single MCP server with all video creation capabilities
- **Multi-Service Integration**: Supports FAL AI services for image, video, audio, and speech generation
- **Intelligent Workflows**: Guided prompts that adapt to your project context
- **Platform Optimization**: Pre-configured settings for YouTube, TikTok, Instagram, and more
- **Cost Tracking**: Real-time cost estimation and tracking for all operations
- **YouTube Integration**: Direct upload to YouTube with OAuth2 authentication
- **Modular Architecture**: Clean separation of tools, resources, and prompts

## Quick Start

### Prerequisites

- Python 3.11+
- FFmpeg installed on your system
- FAL AI API key
- uv (Python package manager)

### Installation with uv

1. Clone the repository:
```bash
git clone <repository-url>
cd video-gen-mcp-monolithic
```

2. Install uv (if not already installed):
```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. Set up the project with uv:
```bash
# uv will automatically:
# - Detect Python 3.11 from .python-version
# - Create a virtual environment
# - Install all dependencies from pyproject.toml
uv sync

# Or if you want to install from requirements.txt:
uv pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create a .env file in the project root
cat > .env << EOF
FALAI_API_KEY=your-fal-api-key
# Optional: For YouTube search features
GOOGLE_API_KEY=your-google-api-key
EOF
```

### Running the Server

```bash
# Run directly with uv (recommended)
uv run python main.py

# Or activate venv and run
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python main.py
```

### Configuring Claude Desktop

Add the following to your Claude Desktop configuration:

**On macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**On Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "video-agent": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/video-gen-mcp-monolithic",
        "run",
        "python",
        "main.py"
      ],
      "env": {
        "FALAI_API_KEY": "your-fal-api-key"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/video-gen-mcp-monolithic` with the actual path to your project directory.

### Alternative: Using pyproject.toml script

Since we've defined a script entry point in pyproject.toml, you can also run:

```bash
# Install the package in development mode
uv pip install -e .

# Run using the script entry point
uv run video-agent-mcp
```

## Usage Example

Once configured in Claude Desktop, you can start creating videos:

```
User: Create a 30-second TikTok video about climate change

Claude: I'll help you create a TikTok video about climate change. Let me start by 
creating a project and planning the scenes...

[Claude uses the video_creation_wizard prompt and various tools to create the video]
```

## Available Tools

### Project Management
- `create_project` - Initialize a new video project with smart defaults based on platform
- `add_scene` - Add scenes to your timeline with description and duration
- `list_projects` - View all projects with their current status

### Content Generation
- `generate_image_from_text` - Create images from text prompts with style modifiers
- `generate_image_from_image` - Transform existing images with AI-powered editing
- `generate_video_from_image` - Animate still images with AI-generated motion (supports Kling 2.1 and Hailuo 02 models)
- `generate_music` - Create background music from text descriptions
- `generate_speech` - Generate voiceovers with multiple voice options

### Generation Tools
Call generation tools sequentially for clear progress tracking and easier debugging.

### Video Assembly
- `download_assets` - Download generated assets from FAL or other sources
- `add_audio_track` - Add audio tracks to video with volume control
- `assemble_video` - Combine scenes into final video with quality presets

### Utility
- `analyze_script` - Analyze scripts for video production insights
- `suggest_scenes` - Generate scene suggestions based on project script
- `upload_image_file` - Upload local image files to FAL for use in generation tools
- `get_server_info` - Get information about the Video Agent server

## Resources

The server provides dynamic resources for context awareness:
- `project://current` - Current project details
- `project://{id}/timeline` - Scene timeline
- `project://{id}/costs` - Cost breakdown
- `platform://{name}/specs` - Platform specifications

## Prompts

Interactive prompts guide complex workflows:
- `video_creation_wizard` - Complete video creation workflow with platform optimization
- `script_to_scenes` - Convert scripts to scene plans with timing recommendations
- `list_video_agent_capabilities` - Comprehensive guide of all server capabilities
- `cinematic_photography_guide` - Professional cinematography techniques for AI visuals

## Configuration

Environment variables:
- `FALAI_API_KEY` - Your FAL AI API key (required)
- `VIDEO_AGENT_STORAGE` - Storage directory (default: ./storage)
- `DEFAULT_IMAGE_MODEL` - Default image model (default: imagen4)
- `DEFAULT_VIDEO_MODEL` - Default video model (default: kling_2.1, options: hailuo_02)

## Project Structure

```
video-agent-mcp/
├── src/mcp_server/
│   ├── config/      # Configuration and settings
│   ├── models/      # Data models
│   ├── tools/       # Tool implementations
│   ├── resources/   # Resource handlers
│   ├── prompts/     # Prompt templates
│   └── services/    # External service integrations
├── templates/       # Video templates
└── tests/          # Test suite
```

## Development

### Setting up Development Environment

```bash
# Clone and enter the project
git clone <repository-url>
cd video-gen-mcp-monolithic

# Install with development dependencies
uv sync --dev

# Or install dev dependencies separately
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Format code
uv run ruff format .
```

### Adding New Capabilities

1. **New Tool**: Create a file in `src/mcp_server/tools/` and register in `server.py`
2. **New Resource**: Create handler in `resources/` and register with decorator
3. **New Prompt**: Add to `prompts/` for guided workflows

### Troubleshooting uv

#### "No Python interpreter found"
```bash
# uv will use the Python version from .python-version (3.11)
# If you need a specific Python version:
uv python install 3.11
uv venv --python 3.11
```

#### "Permission denied" on macOS/Linux
```bash
# Ensure uv is in PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### "Module not found" errors
```bash
# Ensure you're using uv run or have activated the venv
uv run python main.py
# OR
source .venv/bin/activate
python main.py
```

#### Claude Desktop can't find the server
1. Use absolute paths in the configuration
2. Ensure FAL_API_KEY is set in the env section
3. Check Claude Desktop logs for errors
4. Test the server standalone first: `uv run python main.py`

### YouTube Integration

For YouTube upload functionality, see [YOUTUBE_SETUP.md](YOUTUBE_SETUP.md) for detailed OAuth2 setup instructions.

## Environment Variables

Create a `.env` file in the project root:

```bash
# Required
FALAI_API_KEY=your-fal-api-key

# Optional
VIDEO_AGENT_STORAGE=/path/to/storage  # Default: ./storage
DEFAULT_IMAGE_MODEL=imagen4           # Options: imagen4, flux_pro, flux_kontext
DEFAULT_VIDEO_MODEL=kling_2.1         # Options: kling_2.1, hailuo_02
GOOGLE_API_KEY=your-google-api-key    # For YouTube search features
```

## License

[License information]

## Contributing

[Contributing guidelines]