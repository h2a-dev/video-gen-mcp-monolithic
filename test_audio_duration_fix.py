#!/usr/bin/env python3
"""Test script to verify audio duration fix."""

import asyncio
import sys
from pathlib import Path
from src.mcp_server.services.ffmpeg_wrapper import ffmpeg_wrapper
from src.mcp_server.config import settings

async def test_audio_duration_fix():
    """Test that videos maintain their full duration when audio is added."""
    
    print("Testing audio duration fix...")
    print("=" * 50)
    
    # Find a test video and audio file
    test_video = None
    test_audio = None
    
    # Look for existing video files in storage
    storage_dir = settings.storage_dir
    for project_dir in storage_dir.glob("projects/*"):
        if project_dir.is_dir():
            # Look for video files
            for video_file in project_dir.glob("*.mp4"):
                if "temp" not in video_file.name.lower():
                    test_video = video_file
                    break
            
            # Look for audio files
            for audio_file in project_dir.glob("*.mp3"):
                test_audio = audio_file
                break
        
        if test_video and test_audio:
            break
    
    if not test_video:
        print("❌ No test video found in storage")
        print("Please create a project and generate some videos first")
        return
    
    if not test_audio:
        print("❌ No test audio found in storage")
        print("Please create a project and generate some audio first")
        return
    
    print(f"✓ Found test video: {test_video.name}")
    print(f"✓ Found test audio: {test_audio.name}")
    
    # Get original video info
    print("\nOriginal video info:")
    original_info = await ffmpeg_wrapper.get_video_info(str(test_video))
    if original_info.get("error"):
        print(f"❌ Error reading video: {original_info['error']}")
        return
    
    original_duration = original_info.get("duration", 0)
    print(f"  - Duration: {original_duration:.2f} seconds")
    print(f"  - Resolution: {original_info.get('width', 0)}x{original_info.get('height', 0)}")
    print(f"  - Has audio: {original_info.get('has_audio', False)}")
    
    # Get audio info
    print("\nAudio file info:")
    audio_info = await ffmpeg_wrapper.get_video_info(str(test_audio))
    audio_duration = audio_info.get("duration", 0)
    print(f"  - Duration: {audio_duration:.2f} seconds")
    
    # Test adding audio
    output_path = test_video.parent / f"test_output_{test_video.stem}_with_audio.mp4"
    
    print(f"\nAdding audio to video...")
    result = await ffmpeg_wrapper.add_audio_track(
        video_path=str(test_video),
        audio_path=str(test_audio),
        output_path=str(output_path),
        audio_volume=0.5
    )
    
    if not result.get("success"):
        print(f"❌ Failed to add audio: {result.get('error')}")
        return
    
    print("✓ Successfully added audio")
    
    # Check output video
    print("\nOutput video info:")
    output_info = await ffmpeg_wrapper.get_video_info(str(output_path))
    if output_info.get("error"):
        print(f"❌ Error reading output: {output_info['error']}")
        return
    
    output_duration = output_info.get("duration", 0)
    print(f"  - Duration: {output_duration:.2f} seconds")
    print(f"  - Has audio: {output_info.get('has_audio', False)}")
    
    # Check if duration was preserved
    duration_diff = abs(original_duration - output_duration)
    print(f"\nDuration comparison:")
    print(f"  - Original: {original_duration:.2f}s")
    print(f"  - Output: {output_duration:.2f}s")
    print(f"  - Difference: {duration_diff:.2f}s")
    
    if duration_diff < 0.1:  # Allow small rounding differences
        print("✅ SUCCESS: Video duration preserved!")
    else:
        print(f"❌ FAIL: Video was trimmed by {duration_diff:.2f} seconds")
        if audio_duration < original_duration:
            print(f"   Audio was shorter ({audio_duration:.2f}s) than video ({original_duration:.2f}s)")
            print("   This suggests the -shortest flag or duration=first is still active")
    
    # Clean up
    try:
        output_path.unlink()
        print("\n✓ Cleaned up test output file")
    except:
        pass
    
    print("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(test_audio_duration_fix())