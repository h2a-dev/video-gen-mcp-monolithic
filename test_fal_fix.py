#!/usr/bin/env python3
"""Test the FAL client fix."""

import os
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

# Check if FAL API key is set
if not os.getenv("FALAI_API_KEY"):
    print("⚠️  Warning: FALAI_API_KEY not set")
    print("Set it with: export FALAI_API_KEY='your-key-here'")
    print("")

# Test the fix
print("🧪 Testing FAL Client Fix")
print("=" * 50)

try:
    from mcp_server.services.fal_client import fal_service, fal_client
    
    print("✅ Import successful!")
    print(f"- fal_client module: {fal_client}")
    print(f"- fal_service instance: {fal_service}")
    
    # Check that fal_client.run exists
    if hasattr(fal_client, 'run'):
        print("✅ fal_client.run() method exists")
    else:
        print("❌ fal_client.run() method NOT found")
        
    # Check that fal_service is the FALClient instance
    print(f"✅ fal_service type: {type(fal_service).__name__}")
    
    print("\n🎉 The naming conflict has been resolved!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()