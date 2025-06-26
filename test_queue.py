#!/usr/bin/env python3
"""Test script for queue functionality."""

import asyncio
import sys
sys.path.append('src')

from mcp_server.services import fal_service
from mcp_server.models import queue_manager


async def test_queue():
    """Test the queue functionality."""
    print("Testing Queue System")
    print("="*50)
    
    # Test 1: Submit a video generation task
    print("\n1. Submitting video generation task...")
    
    task_id = await fal_service.submit_generation(
        model_id="fal-ai/kling-video/v2.1/standard/image-to-video",
        arguments={
            "prompt": "Camera slowly zooms in",
            "image_url": "https://example.com/test.jpg",  # This will fail but demonstrates the flow
            "duration": "5",
            "aspect_ratio": "16:9"
        },
        task_type="video",
        metadata={"test": True}
    )
    
    print(f"   Task submitted with ID: {task_id}")
    
    # Test 2: Check task status
    print("\n2. Checking task status...")
    await asyncio.sleep(2)
    
    task = await queue_manager.get_task(task_id)
    if task:
        print(f"   Status: {task.status}")
        print(f"   Queue Position: {task.queue_position}")
        print(f"   Progress: {task.progress_percentage}%")
    
    # Test 3: Get queue statistics
    print("\n3. Getting queue statistics...")
    stats = await queue_manager.get_queue_stats()
    print(f"   Total tasks: {stats['total_tasks']}")
    print(f"   Active tasks: {stats['active_count']}")
    print(f"   By status: {stats['by_status']}")
    
    # Test 4: Cancel the task
    print("\n4. Cancelling task...")
    success = await queue_manager.cancel_task(task_id)
    print(f"   Cancellation {'successful' if success else 'failed'}")
    
    # Test 5: Check final status
    print("\n5. Final task status...")
    task = await queue_manager.get_task(task_id)
    if task:
        print(f"   Status: {task.status}")
        print(f"   Error: {task.error_message}")
    
    print("\n" + "="*50)
    print("Queue system test completed!")


if __name__ == "__main__":
    asyncio.run(test_queue())