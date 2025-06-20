# Video Agent MCP Server

A comprehensive Model Context Protocol (MCP) server for AI-powered video creation. This server provides tools, resources, and prompts to guide AI agents through complete video production workflows.

## Features

- **Unified Interface**: Single MCP server with all video creation capabilities
- **Multi-Service Integration**: Supports FAL AI services for image, video, audio, and speech generation
- **Intelligent Workflows**: Guided prompts that adapt to your project context
- **Platform Optimization**: Pre-configured settings for YouTube, TikTok, Instagram, and more
- **Cost Tracking**: Real-time cost estimation and tracking for all operations
- **Modular Architecture**: Clean separation of tools, resources, and prompts

## Quick Start

### Prerequisites

- Python 3.11+
- FFmpeg installed on your system
- FAL AI API key
- uv (recommended for dependency management)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd video-agent-mcp
```

2. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Create virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

4. Set up environment variables:
```bash
export FALAI_API_KEY="your-fal-api-key"
```

### Running the Server

```bash
uv run python main.py
```

### Configuring Claude Desktop

Add the following to your Claude Desktop configuration (`.mcp.json`):

```json
{
  "mcpServers": {
    "video-agent": {
      "command": "uv",
      "args": ["--directory", "./video-agent-mcp", "run", "python", "main.py"],
      "env": {
        "FALAI_API_KEY": "your-fal-api-key"
      }
    }
  }
}
```

Note: The `--directory` flag ensures uv runs in the correct project directory.

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
- `generate_video_from_image` - Animate still images with AI-generated motion
- `generate_music` - Create background music from text descriptions
- `generate_speech` - Generate voiceovers with multiple voice options

### Video Assembly
- `download_assets` - Download generated assets from FAL or other sources
- `add_audio_track` - Add audio tracks to video with volume control
- `assemble_video` - Combine scenes into final video with quality presets

### Utility
- `analyze_script` - Analyze scripts for video production insights
- `suggest_scenes` - Generate scene suggestions based on project script
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
- `DEFAULT_VIDEO_MODEL` - Default video model (default: kling-2.1)

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

To add new capabilities:

1. **New Tool**: Create a file in `src/mcp_server/tools/` and register in `server.py`
2. **New Resource**: Create handler in `resources/` and register with decorator
3. **New Prompt**: Add to `prompts/` for guided workflows

## License

[License information]

## Contributing

[Contributing guidelines]