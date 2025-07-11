#!/usr/bin/env python3
"""Test script to verify end video functionality."""

import asyncio
from pathlib import Path
from src.mcp_server.services.ffmpeg_wrapper import ffmpeg_wrapper
from src.mcp_server.config import settings

async def test_end_video():
    """Test that the end video file exists and is valid."""
    
    print("Testing end video functionality...")
    
    # Check if end video exists
    end_video_path = settings.logos_dir / "h2a_end.mp4"
    print(f"\nChecking for end video at: {end_video_path}")
    
    if end_video_path.exists():
        print("✓ End video file exists")
        
        # Get video info
        video_info = await ffmpeg_wrapper.get_video_info(str(end_video_path))
        
        if not video_info.get("error"):
            print(f"✓ End video is valid")
            print(f"  - Duration: {video_info.get('duration', 0):.2f} seconds")
            print(f"  - Resolution: {video_info.get('width', 0)}x{video_info.get('height', 0)}")
            print(f"  - FPS: {video_info.get('fps', 0)}")
            print(f"  - Has audio: {video_info.get('has_audio', False)}")
        else:
            print(f"✗ Error reading end video: {video_info.get('error')}")
    else:
        print(f"✗ End video file not found at: {end_video_path}")
        print(f"  Please ensure h2a_end.mp4 is placed in: {settings.logos_dir}")
    
    # Check logo file
    logo_path = settings.default_logo_path
    print(f"\nChecking for logo at: {logo_path}")
    if logo_path.exists():
        print("✓ Logo file exists")
    else:
        print(f"✗ Logo file not found")

if __name__ == "__main__":
    asyncio.run(test_end_video())