#!/usr/bin/env python3
"""Test script for project creation with string parameters."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_server.tools.project import create_project


async def test_project_creation():
    """Test creating a project with string parameters (as MCP would send them)."""
    print("🧪 Testing Project Creation with String Parameters")
    print("=" * 50)
    
    # Test with parameters as MCP would send them (strings)
    result = await create_project(
        title="90s Style Black Holes TikTok",
        platform="tiktok",
        script="Black holes: the ultimate cosmic mystery. These space monsters devour everything - even light can't escape! When a massive star dies, it collapses into a point smaller than an atom but heavier than our sun. Mind blown yet?",
        target_duration="20"  # String, as MCP sends it
    )
    
    if result["success"]:
        print("✅ Project created successfully!")
        print(f"\nProject Details:")
        print(f"- ID: {result['project']['id']}")
        print(f"- Title: {result['project']['title']}")
        print(f"- Platform: {result['project']['platform']}")
        print(f"- Aspect Ratio: {result['project']['aspect_ratio']}")
        print(f"- Target Duration: {result['project']['target_duration']}s")
        print(f"- Status: {result['project']['status']}")
        
        print(f"\nPlatform Info:")
        print(f"- Max Duration: {result['platform_info']['max_duration']}s")
        print(f"- Formats: {', '.join(result['platform_info']['formats'])}")
        
        print(f"\nCost Estimate:")
        print(f"- Total: ${result['cost_estimate']['total']}")
        if 'breakdown' in result['cost_estimate']:
            for category, details in result['cost_estimate']['breakdown'].items():
                if details:
                    print(f"  - {category.title()}: ${details['cost']}")
        
        print(f"\nNext Steps:")
        for step in result['next_steps']:
            print(f"- {step}")
            
        # Test script analysis
        print("\n" + "=" * 50)
        print("Testing Script Analysis...")
        
        from mcp_server.tools.utility import analyze_script
        
        analysis = await analyze_script(
            script=result['project']['script'],
            target_duration="20",  # String parameter
            platform="tiktok"
        )
        
        if analysis["success"]:
            print("✅ Script analysis successful!")
            print(f"\nText Stats:")
            print(f"- Words: {analysis['analysis']['text_stats']['word_count']}")
            print(f"- Estimated speaking time: {analysis['analysis']['text_stats']['estimated_speaking_seconds']}s")
            print(f"\nScene Recommendations:")
            print(f"- Recommended scenes: {analysis['analysis']['scene_analysis']['recommended_scenes']}")
            print(f"- Scene duration mix: {analysis['analysis']['scene_analysis']['scene_duration_mix']}")
            
    else:
        print(f"❌ Project creation failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    # Check if FAL API key is set
    import os
    if not os.getenv("FALAI_API_KEY"):
        print("⚠️  Warning: FALAI_API_KEY not set. Set it with:")
        print("export FALAI_API_KEY='your-key-here'")
        print("\nContinuing with test anyway...\n")
    
    asyncio.run(test_project_creation())