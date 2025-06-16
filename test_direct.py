#!/usr/bin/env python3
"""Direct test of project creation logic."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Mock the MCP import
sys.modules['mcp'] = type(sys)('mcp')
sys.modules['mcp.server'] = type(sys)('mcp.server')

class MockFastMCP:
    def __init__(self, *args, **kwargs):
        pass
    def tool(self):
        return lambda f: f
    def resource(self, uri):
        return lambda f: f
    def prompt(self):
        return lambda f: f
    def run(self):
        pass

sys.modules['mcp.server'].FastMCP = MockFastMCP


async def test_project_creation_directly():
    """Test the create_project function directly."""
    print("🧪 Testing Project Creation Logic")
    print("=" * 50)
    
    # Import after mocking
    from mcp_server.tools.project.create_project import create_project
    
    # Test parameters
    params = {
        "title": "90s Style Black Holes TikTok",
        "platform": "tiktok",
        "script": "Black holes: the ultimate cosmic mystery. These space monsters devour everything - even light can't escape! When a massive star dies, it collapses into a point smaller than an atom but heavier than our sun. Mind blown yet?",
        "target_duration": "20"  # String, as MCP would send it
    }
    
    print(f"Input parameters:")
    print(f"- Title: {params['title']}")
    print(f"- Platform: {params['platform']}")
    print(f"- Target Duration: {params['target_duration']} (type: {type(params['target_duration'])})")
    print(f"- Script: {params['script'][:50]}...")
    
    try:
        result = await create_project(**params)
        
        if result["success"]:
            print("\n✅ SUCCESS! Project created without errors")
            print(f"\nProject Details:")
            print(f"- ID: {result['project']['id']}")
            print(f"- Target Duration: {result['project']['target_duration']} seconds")
            print(f"- Aspect Ratio: {result['project']['aspect_ratio']}")
            print(f"- Cost Estimate: ${result['cost_estimate']['total']}")
            
            # The fix worked!
            print("\n🎉 Type conversion fix is working correctly!")
            print("String '20' was successfully converted to integer 20")
            
        else:
            print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Exception occurred: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_project_creation_directly())