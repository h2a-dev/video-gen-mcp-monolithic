#!/usr/bin/env python3
"""Main entry point for the Video Agent MCP server."""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_server.server import mcp

if __name__ == "__main__":
    mcp.run()