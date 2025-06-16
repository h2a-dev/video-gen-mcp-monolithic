#!/usr/bin/env python3
"""Simple test script for Video Agent MCP server."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_server.server import mcp
from mcp_server.config import settings


async def test_basic_functionality():
    """Test basic server functionality."""
    print("🧪 Testing Video Agent MCP Server")
    print("=" * 50)
    
    # Test 1: Server info
    print("\n1. Testing server info...")
    try:
        # Import the tool directly
        from mcp_server.server import get_server_info
        info = await get_server_info()
        print(f"✅ Server Name: {info['name']}")
        print(f"✅ Version: {info['version']}")
        print(f"✅ FAL API Configured: {info['fal_api_configured']}")
    except Exception as e:
        print(f"❌ Server info test failed: {e}")
    
    # Test 2: List video agent capabilities
    print("\n2. Testing capabilities prompt...")
    try:
        from mcp_server.prompts import list_video_agent_capabilities
        capabilities = await list_video_agent_capabilities()
        print(f"✅ Capabilities prompt returned {len(capabilities)} characters")
        print("✅ Contains expected sections:", all(
            section in capabilities 
            for section in ["## 📝 Prompts", "## 🔧 Tools", "## 📊 Resources"]
        ))
    except Exception as e:
        print(f"❌ Capabilities test failed: {e}")
    
    # Test 3: Create a test project
    print("\n3. Testing project creation...")
    try:
        from mcp_server.tools.project import create_project
        result = await create_project(
            title="Test Video",
            platform="youtube_shorts",
            script="This is a test script for a short video about testing.",
            target_duration=30
        )
        if result["success"]:
            project_id = result["project"]["id"]
            print(f"✅ Created project: {project_id}")
            print(f"✅ Platform: {result['project']['platform']}")
            print(f"✅ Aspect Ratio: {result['project']['aspect_ratio']}")
        else:
            print(f"❌ Project creation failed: {result.get('error')}")
    except Exception as e:
        print(f"❌ Project creation test failed: {e}")
    
    # Test 4: Analyze script
    print("\n4. Testing script analysis...")
    try:
        from mcp_server.tools.utility import analyze_script
        script = """
        Welcome to our cooking tutorial! Today we'll make a delicious pasta dish.
        First, boil the water. Then add the pasta. Cook for 10 minutes.
        Finally, add your favorite sauce and enjoy!
        """
        result = await analyze_script(script, target_duration=30, platform="tiktok")
        if result["success"]:
            print(f"✅ Word count: {result['analysis']['text_stats']['word_count']}")
            print(f"✅ Recommended scenes: {result['analysis']['scene_analysis']['recommended_scenes']}")
            print(f"✅ Estimated cost: ${result['recommendations']['cost_estimate']['total_estimate']}")
        else:
            print(f"❌ Script analysis failed: {result.get('error')}")
    except Exception as e:
        print(f"❌ Script analysis test failed: {e}")
    
    # Test 5: Platform specs
    print("\n5. Testing platform specs resource...")
    try:
        from mcp_server.resources import get_platform_specs
        specs = await get_platform_specs("tiktok")
        data = specs["data"]
        if "specifications" in data:
            print(f"✅ Platform: {data['display_name']}")
            print(f"✅ Max duration: {data['specifications']['duration']['max_seconds']}s")
            print(f"✅ Default aspect ratio: {data['specifications']['aspect_ratios']['default']}")
        else:
            print(f"❌ Platform specs incomplete: {data}")
    except Exception as e:
        print(f"❌ Platform specs test failed: {e}")
    
    print("\n" + "=" * 50)
    print("✨ Basic tests completed!")
    
    # Test configuration
    print("\n📋 Configuration Status:")
    print(f"- Storage Directory: {settings.storage_dir}")
    print(f"- FAL API Key: {'✅ Configured' if settings.fal_api_key else '❌ Not configured'}")
    print(f"- FFmpeg Path: {settings.ffmpeg_path}")
    
    if not settings.fal_api_key:
        print("\n⚠️  Warning: FALAI_API_KEY not set. Generation tools won't work.")
        print("Set it with: export FALAI_API_KEY='your-key-here'")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())