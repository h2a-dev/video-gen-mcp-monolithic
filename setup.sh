#!/bin/bash
# Quick setup script for Video Agent MCP Server

echo "🎬 Video Agent MCP Server Setup"
echo "==============================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Check Python version
echo "🐍 Checking Python version..."
uv python install 3.11

# Set up the project
echo "📚 Installing dependencies..."
uv sync

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating .env file..."
    cat > .env << EOF
# Required
FALAI_API_KEY=your-fal-api-key-here

# Optional
# VIDEO_AGENT_STORAGE=./storage
# DEFAULT_IMAGE_MODEL=imagen4
# DEFAULT_VIDEO_MODEL=kling_2.1
# GOOGLE_API_KEY=your-google-api-key-here
EOF
    echo "⚠️  Please edit .env and add your FALAI_API_KEY"
fi

# Create client_secrets.json template if it doesn't exist
if [ ! -f client_secrets.json ]; then
    echo "📝 Creating client_secrets.json template..."
    cat > client_secrets.json.template << EOF
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "YOUR_PROJECT_ID",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
EOF
    echo "⚠️  For YouTube upload: Download OAuth credentials from Google Cloud Console"
    echo "    and replace client_secrets.json.template → client_secrets.json"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your FALAI_API_KEY"
echo "2. (Optional) Set up YouTube OAuth for upload functionality"
echo "3. Run the server: uv run python main.py"
echo ""
echo "For Claude Desktop integration, add this to your config:"
echo '  "video-agent": {'
echo '    "command": "uv",'
echo '    "args": ["--directory", "'$(pwd)'", "run", "python", "main.py"],'
echo '    "env": { "FALAI_API_KEY": "your-key" }'
echo '  }'