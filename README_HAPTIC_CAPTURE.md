# Frame Glasses Haptic-Triggered Photo Capture

## 🎯 Overview

This feature enables **touch-triggered photo capture** on Frame glasses using the built-in IMU sensors. Instead of manually running commands, users can simply **touch the glasses** to automatically capture photos.

## 🚀 Key Features

- **Touch Detection**: Uses accelerometer and gyroscope data to detect physical touch events
- **Automatic Capture**: Photos are captured automatically when touch is detected
- **Visual Feedback**: Shows "T" indicator on glasses display when touch is detected
- **Dual Mode**: Supports both haptic-triggered and manual capture
- **Real-time Monitoring**: Continuous monitoring for touch events
- **API Integration**: Full REST API for haptic functionality

## 🔧 How It Works

### Touch Detection Algorithm

The system uses a **multi-sensor approach** to detect touch events:

1. **Accelerometer Data**: Monitors acceleration changes in X, Y, Z axes
2. **Gyroscope Data**: Checks for rotational movement patterns
3. **Time Thresholds**: Prevents spam by enforcing minimum time between touches
4. **Pattern Recognition**: Distinguishes between intentional touches and normal movement

### Technical Implementation

```lua
-- Touch detection logic in haptic_camera_app.lua
function detect_touch()
    local accel = frame.imu.accelerometer()
    local gyro = frame.imu.gyroscope()
    
    -- Calculate acceleration change
    local accel_change = math.abs(accel.x - last_accel.x) + 
                        math.abs(accel.y - last_accel.y) + 
                        math.abs(accel.z - last_accel.z)
    
    -- Check if this looks like a touch event
    if accel_change > accel_threshold and 
       gyro_magnitude < gyro_threshold and 
       time_since_last_touch > touch_threshold then
        return true
    end
    
    return false
end
```

## 📋 API Endpoints

### Haptic Mode Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/haptic/connect` | POST | Connect to glasses in haptic mode |
| `/api/v1/haptic/disconnect` | POST | Disconnect and stop monitoring |
| `/api/v1/haptic/start-monitoring` | POST | Start touch event monitoring |
| `/api/v1/haptic/stop-monitoring` | POST | Stop touch event monitoring |
| `/api/v1/haptic/status` | GET | Get haptic mode status |

### Capture Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/haptic/capture-manual` | POST | Manual capture in haptic mode |
| `/api/v1/haptic/display` | POST | Display text on glasses |

## 🛠️ Usage Examples

### Python with httpx

```python
import httpx

async def haptic_capture_demo():
    async with httpx.AsyncClient() as client:
        # 1. Connect in haptic mode
        response = await client.post("http://localhost:8000/api/v1/haptic/connect")
        print("Connected:", response.json())
        
        # 2. Start monitoring
        response = await client.post("http://localhost:8000/api/v1/haptic/start-monitoring")
        print("Monitoring started:", response.json())
        
        # 3. Touch the glasses to capture photos!
        print("Touch the glasses to capture photos...")
        
        # 4. Check status
        response = await client.get("http://localhost:8000/api/v1/haptic/status")
        status = response.json()
        print("Status:", status)
        
        # 5. Stop and disconnect
        await client.post("http://localhost:8000/api/v1/haptic/stop-monitoring")
        await client.post("http://localhost:8000/api/v1/haptic/disconnect")
```

### cURL Commands

```bash
# Connect in haptic mode
curl -X POST http://localhost:8000/api/v1/haptic/connect

# Start monitoring
curl -X POST http://localhost:8000/api/v1/haptic/start-monitoring

# Check status
curl -X GET http://localhost:8000/api/v1/haptic/status

# Manual capture (while in haptic mode)
curl -X POST http://localhost:8000/api/v1/haptic/capture-manual \
  -H "Content-Type: application/json" \
  -d '{"resolution": 720}'

# Stop monitoring
curl -X POST http://localhost:8000/api/v1/haptic/stop-monitoring

# Disconnect
curl -X POST http://localhost:8000/api/v1/haptic/disconnect
```

## 🎮 Complete Workflow Demo

Run the complete demo script:

```bash
python test_haptic_capture.py
```

This will:
1. Connect to glasses in haptic mode
2. Start touch monitoring
3. Wait for touch events
4. Show real-time status updates
5. Demonstrate manual capture
6. Clean disconnection

## 🔍 Configuration Options

### Touch Detection Parameters

You can adjust these parameters in `haptic_camera_app.lua`:

```lua
-- Touch detection sensitivity
local accel_threshold = 2.0    -- Acceleration change threshold
local gyro_threshold = 1.0     -- Gyroscope threshold
local touch_threshold = 0.5    -- Minimum time between touches (seconds)
```

### Monitoring Settings

```python
# In haptic_frame_service.py
async def _monitor_haptic_captures(self):
    # Polling frequency for touch detection
    frame.sleep(0.05)  # 50ms polling interval
    
    # Photo capture timeout
    jpeg_bytes = await asyncio.wait_for(self.photo_queue.get(), timeout=1.0)
```

## 🏗️ Architecture

### Components

1. **Lua App** (`haptic_camera_app.lua`)
   - Runs on Frame glasses
   - Monitors IMU sensors
   - Detects touch events
   - Triggers photo capture

2. **Python Service** (`HapticFrameService`)
   - Manages connection to glasses
   - Handles haptic monitoring
   - Processes captured photos
   - Provides callback system

3. **API Routes** (`haptic.py`)
   - REST endpoints for haptic functionality
   - Status monitoring
   - Manual capture support

4. **Test Script** (`test_haptic_capture.py`)
   - Complete workflow demonstration
   - API testing
   - User interaction simulation

### Data Flow

```
User Touch → IMU Sensors → Lua Detection → Photo Capture → Python Service → API Response
     ↓              ↓              ↓              ↓              ↓              ↓
  Physical    Accelerometer   Touch Event    JPEG Data    Callback      REST API
  Contact     + Gyroscope     Detection      Transfer     Processing    Response
```

## 🎯 Use Cases

### 1. Hands-Free Photography
- Capture photos without using phone or voice commands
- Perfect for activities where hands are occupied
- Quick, intuitive photo capture

### 2. Continuous Monitoring
- Set up glasses to capture photos on any touch
- Useful for documentation or surveillance
- Automatic event recording

### 3. Accessibility
- Easier photo capture for users with limited mobility
- Simple touch interface
- Visual feedback on glasses display

### 4. Integration with AI
- Combine with existing AI analysis pipeline
- Automatic food analysis on touch
- Real-time object recognition

## 🔧 Troubleshooting

### Common Issues

1. **Touch Not Detected**
   - Check accelerometer threshold settings
   - Ensure glasses are properly positioned
   - Verify haptic mode is active

2. **False Positives**
   - Increase `accel_threshold` value
   - Adjust `gyro_threshold` for movement filtering
   - Increase `touch_threshold` for spam prevention

3. **Connection Issues**
   - Verify Bluetooth connection
   - Check battery level
   - Restart haptic monitoring

### Debug Mode

Enable debug output by modifying the Lua app:

```lua
-- Add debug prints
print("Accel change:", accel_change)
print("Gyro magnitude:", gyro_magnitude)
print("Touch detected:", detect_touch())
```

## 🚀 Future Enhancements

### Planned Features

1. **Gesture Recognition**
   - Multiple touch patterns
   - Swipe gestures
   - Double-tap detection

2. **Custom Triggers**
   - Voice activation
   - Motion-based triggers
   - Time-based captures

3. **Advanced Filtering**
   - Machine learning for touch detection
   - Environmental noise reduction
   - User-specific calibration

4. **Integration Features**
   - Direct AI analysis on touch
   - Cloud storage integration
   - Social media sharing

## 📚 Related Documentation

- [Frame SDK Documentation](https://github.com/CitizenOneX/frame_examples_python)
- [API Documentation](README_API.md)
- [Moondream Integration](README_MOONDREAM_ENDPOINTS.md)
- [Parking Violations](PARKING_VIOLATIONS_DATA_NOTES.md)

## 🤝 Contributing

To contribute to haptic capture functionality:

1. Test with different touch patterns
2. Optimize detection algorithms
3. Add new trigger types
4. Improve error handling
5. Enhance documentation

---

**🎉 Ready to capture photos with a simple touch!** 