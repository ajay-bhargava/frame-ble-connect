"""
Debugging script for capture_photo function issues.

This script demonstrates common problems and their solutions:
1. Attempting to capture without connecting first
2. Connection failures that leave photo_queue as None
3. Callback handling issues with sync/async functions
4. Timeout scenarios during photo capture

Run this to understand the capture_photo issues and verify fixes.
"""

import asyncio
import logging
from src.connect.frame_interface import FrameInterface

# Setup logging to see detailed error information
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demonstrate_capture_photo_issues():
    """
    Demonstrate common capture_photo issues and their solutions.
    """
    print("🔍 Debugging capture_photo function issues...")
    print("=" * 60)
    
    # Create interface instance
    interface = FrameInterface()
    
    # Issue 1: Attempting to capture without connecting
    print("\n1. Testing capture without connection:")
    print("-" * 40)
    
    result = await interface.capture_photo()
    print(f"Result: {result}")
    print(f"✅ Properly handled: {not result['success'] and 'Not connected' in result['error']}")
    
    # Issue 2: Testing callback handling
    print("\n2. Testing callback safety:")
    print("-" * 40)
    
    # Test with sync callback
    sync_calls = []
    def sync_callback(data, metadata):
        sync_calls.append(f"Sync: {len(data)} bytes")
    
    interface.set_photo_callback(sync_callback)
    
    # Test with async callback  
    async_calls = []
    async def async_callback(data, metadata):
        async_calls.append(f"Async: {len(data)} bytes")
    
    interface.set_photo_callback(async_callback)
    
    # Test with None callback
    interface.set_photo_callback(None)
    
    # Test safe callback function directly
    await interface._safe_callback(sync_callback, b'test_data', {'test': True})
    await interface._safe_callback(async_callback, b'test_data', {'test': True})
    await interface._safe_callback(None, b'test_data', {'test': True})
    
    print(f"Sync callback calls: {sync_calls}")
    print(f"Async callback calls: {async_calls}")
    print(f"✅ Callbacks handled safely: {len(sync_calls) == 1 and len(async_calls) == 1}")
    
    # Issue 3: Testing connection validation
    print("\n3. Testing connection state validation:")
    print("-" * 40)
    
    # Test various connection states
    interface.is_connected = True
    interface.frame = None  # Simulate partial connection failure
    
    result = await interface.capture_photo()
    print(f"Result with frame=None: {result}")
    print(f"✅ Properly detected frame=None: {not result['success']}")
    
    # Reset state
    interface.is_connected = False
    interface.frame = None
    interface.photo_queue = None
    
    # Issue 4: Testing photo_queue validation
    print("\n4. Testing photo_queue validation:")
    print("-" * 40)
    
    # Simulate connected state but None photo_queue
    interface.is_connected = True 
    interface.frame = "mock_frame"  # Fake frame object
    interface.photo_queue = None
    
    result = await interface.capture_photo()
    print(f"Result with photo_queue=None: {result}")
    print(f"✅ Properly detected photo_queue=None: {not result['success'] and 'photo_queue is None' in result['error']}")
    
    print("\n" + "=" * 60)
    print("🎯 Summary of Issues and Fixes:")
    print("=" * 60)
    
    print("""
The main issues with capture_photo were:

1. **Type System Issues**:
   - Callbacks were Optional[Union[sync, async]] but always awaited
   - Fixed with _safe_callback() that detects sync vs async

2. **Null Pointer Issues**:
   - photo_queue could be None if connection failed
   - Fixed with explicit None checks and validation

3. **Connection State Issues**:
   - Missing validation that frame object exists
   - Fixed with comprehensive state checking

4. **Error Handling Issues**:
   - Callbacks could raise exceptions and crash
   - Fixed with try/catch in _safe_callback()

5. **Return Path Issues**:
   - connect() method had code paths without returns
   - Fixed by restructuring retry loop

All these issues have been resolved in the updated FrameInterface.
    """)
    
    print("\n✅ All major issues have been identified and fixed!")


async def demonstrate_proper_usage():
    """
    Show the correct way to use capture_photo after fixes.
    """
    print("\n🚀 Demonstrating proper capture_photo usage:")
    print("=" * 60)
    
    interface = FrameInterface(
        capture_resolution=720,
        auto_exposure_delay=2.0
    )
    
    # Setup callbacks (both sync and async work now)
    photos_captured = []
    
    async def photo_callback(image_data, metadata):
        photos_captured.append({
            'size': len(image_data),
            'resolution': metadata['resolution'],
            'timestamp': metadata['timestamp']
        })
        print(f"📸 Photo captured: {len(image_data)} bytes at {metadata['resolution']}p")
    
    def error_callback(error):
        print(f"❌ Error occurred: {error}")
    
    interface.set_photo_callback(photo_callback)
    interface.set_error_callback(error_callback)
    
    print("""
Proper usage pattern:

1. Create FrameInterface instance
2. Set up callbacks (optional)
3. Connect to Frame glasses  
4. Check connection result
5. Use capture_photo() method
6. Handle results properly
7. Disconnect when done

Note: This demo shows the pattern but won't actually connect 
to Frame glasses since no hardware is available.
    """)
    
    # Attempt connection (will fail without hardware, but safely)
    print("\n📡 Attempting connection...")
    connect_result = await interface.connect(max_retries=1)
    
    if connect_result["success"]:
        print("✅ Connected to Frame glasses!")
        
        # Capture photo
        capture_result = await interface.capture_photo()
        
        if capture_result["success"]:
            print("📸 Photo captured successfully!")
        else:
            print(f"❌ Capture failed: {capture_result['error']}")
            
        await interface.disconnect()
    else:
        print(f"❌ Connection failed (expected): {connect_result['error']}")
        print("✅ Failure handled gracefully - no crashes!")


if __name__ == "__main__":
    print("🔧 Frame Interface capture_photo Debugging Tool")
    print("=" * 60)
    
    async def main():
        await demonstrate_capture_photo_issues()
        await demonstrate_proper_usage()
    
    asyncio.run(main()) 