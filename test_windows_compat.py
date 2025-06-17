#!/usr/bin/env python3
"""Test script to verify Windows compatibility for ffmpeg calls."""

import platform
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.mcp_server.config.settings import settings

print(f"Platform: {platform.system()}")
print(f"FFmpeg path: {settings.ffmpeg_path}")
print(f"Environment FFMPEG_PATH: {os.getenv('FFMPEG_PATH', 'Not set')}")

# Test the ffmpeg wrapper
try:
    from src.mcp_server.services.ffmpeg_wrapper import ffmpeg_wrapper
    print(f"FFmpeg wrapper initialized successfully")
    print(f"FFmpeg command: {ffmpeg_wrapper.ffmpeg_path}")
except Exception as e:
    print(f"Error initializing ffmpeg wrapper: {e}")

# Test ffprobe detection
try:
    ffprobe_cmd = ffmpeg_wrapper._get_ffprobe_command()
    print(f"FFprobe command: {ffprobe_cmd}")
except Exception as e:
    print(f"Error getting ffprobe command: {e}")