# Video Agent MCP Server - Setup Guide

## Prerequisites

1. **Python 3.11+**
   ```bash
   python --version  # Should show 3.11 or higher
   ```

2. **FFmpeg** (for video processing)
   - macOS: `brew install ffmpeg`
   - Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

3. **FAL AI API Key**
   - Sign up at [fal.ai](https://fal.ai)
   - Get your API key from [Dashboard](https://fal.ai/dashboard/keys)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd video-agent-mcp
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your FAL API key
   export FALAI_API_KEY="your-fal-api-key-here"
   ```

## Testing the Installation

Run the test script to verify everything is working:

```bash
python test_server.py
```

You should see output like:
```
🧪 Testing Video Agent MCP Server
==================================================

1. Testing server info...
✅ Server Name: video-agent
✅ Version: 0.1.0
✅ FAL API Configured: True

2. Testing capabilities prompt...
✅ Capabilities prompt returned 3842 characters
✅ Contains expected sections: True
...
```

## Configuring Claude Desktop

1. **Find your Claude Desktop configuration**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Add the Video Agent server**
   
   Edit the configuration file and add:
   ```json
   {
     "mcpServers": {
       "video-agent": {
         "command": "python",
         "args": ["/absolute/path/to/video-agent-mcp/main.py"],
         "env": {
           "FALAI_API_KEY": "your-fal-api-key-here"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

## Verifying MCP Connection

In Claude Desktop, type:
```
Use the list_video_agent_capabilities prompt
```

You should see a comprehensive list of all available tools, resources, and prompts.

## Quick Start Examples

### 1. Create a simple video
```
Use the video_creation_wizard prompt for platform "tiktok" and topic "cooking tips"
```

### 2. Create a project manually
```
Use create_project to create a project titled "My First Video" for platform "youtube_shorts"
```

### 3. Generate an image
```
Use generate_image_from_text with prompt "futuristic city skyline at sunset"
```

## Troubleshooting

### FFmpeg not found
- Ensure FFmpeg is in your PATH
- Set FFMPEG_PATH environment variable to the full path

### FAL API errors
- Verify your API key is correct
- Check your FAL account has credits
- Look for rate limiting errors

### MCP connection issues
- Check the path in Claude Desktop config is absolute
- Ensure Python path is correct
- Check for any error messages in Claude Desktop

### Storage issues
- By default, files are stored in `./storage`
- Set VIDEO_AGENT_STORAGE to use a different location
- Ensure the directory has write permissions

## Cost Management

Monitor your costs with:
```
Access the resource project://[project_id]/costs
```

Approximate costs:
- Images: $0.04 each
- Videos: $0.05 per second
- Music: $0.10 per track
- Speech: $0.10 per 1000 characters

## Next Steps

1. **Explore the capabilities**
   - Use `list_video_agent_capabilities()` to see all features
   - Try different prompts and tools

2. **Create your first video**
   - Start with `video_creation_wizard`
   - Follow the guided workflow

3. **Read the documentation**
   - Check README.md for detailed usage
   - Review projectplan_mvp_v2.md for architecture

## Support

- GitHub Issues: [Report bugs or request features]
- Documentation: See README.md
- MCP Protocol: https://modelcontextprotocol.io