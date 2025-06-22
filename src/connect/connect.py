import asyncio
import os
import sys

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from frame_ble import FrameBle

from api.services.frame_msg_service import FrameService

async def main():
    frame = FrameBle()

    frame_service = FrameService()

    try:
        await frame.connect()

        # Print "Hello, Frame!" on the Frame display
        # wait for a printed string to come back from Frame to ensure the Lua has executed, not just that the command was sent successfully
        await frame.send_lua("frame.display.text('fuhgedaboutit', 1, 1);frame.display.show();print(0)", await_print=True)
        #await frame.display_text("fuhgedaboutit")

        await frame.disconnect()

    except Exception as e:
        print(f"Not connected to Frame: {e}")
        return

if __name__ == "__main__":
    asyncio.run(main())