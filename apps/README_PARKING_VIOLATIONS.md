# Parking Violations Checker for Frame AR Glasses

A comprehensive AI-powered parking violations checking system that combines Frame AR glasses with computer vision and natural language processing to help users make informed parking decisions.

## 🚗 Overview

The Parking Violations Checker captures images through Frame AR glasses, uses Moondream's vision-language model to extract parking zone numbers from street signs, checks violation counts for that zone, and displays helpful feedback directly on the glasses.

### Key Features

- **🔍 Smart Zone Detection**: Uses Moondream VLM via `/query` API to extract zone numbers from street signs
- **📊 Violation Analysis**: Checks parking violation counts and compares against safety thresholds  
- **🥽 AR Feedback**: Displays contextual recommendations directly on Frame glasses
- **🛡️ Robust Error Handling**: Graceful handling of connection, capture, and analysis failures
- **⚡ Real-time Processing**: Complete workflow typically completes in 2-5 seconds
- **🧪 Comprehensive Testing**: Full test suite with mocking for hardware-free development

## 🏗️ Architecture

```mermaid
graph TD
    A[Frame AR Glasses] -->|Bluetooth| B[Frame SDK]
    B --> C[Image Capture]
    C --> D[Moondream VLM API]
    D -->|Zone Number| E[Violation Database]
    E -->|Count| F[Decision Logic]
    F -->|Message| G[Frame Display]
    
    subgraph "AI Processing"
        D1[/query endpoint]
        D2[Vision-Language Model]
        D3[Text Extraction]
    end
    
    D --> D1 --> D2 --> D3
```

### Technical Stack

- **Hardware**: Frame AR Glasses with Bluetooth connectivity
- **AI/ML**: Moondream Vision-Language Model for OCR and text extraction
- **Backend**: FastAPI with async processing
- **Communication**: Frame SDK (FrameMsg) for hardware interaction
- **Testing**: pytest with comprehensive mocking

## 🚀 Quick Start

### Prerequisites

1. **Frame AR Glasses** paired with your computer via Bluetooth
2. **API Server** running the analysis endpoints (see main README)
3. **Python Dependencies** installed via `uv` or `pip`

### Installation

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd frame-ble-connect

# Install dependencies
uv sync  # or pip install -r requirements.txt

# Verify API server is running
curl http://localhost:8000/analysis/query --help
```

### Basic Usage

```python
import asyncio
from apps.parking_violations import ParkingViolationsChecker

async def main():
    # Initialize checker with custom settings
    checker = ParkingViolationsChecker(
        api_base_url="http://localhost:8000",
        violation_threshold=5  # Warn if more than 5 violations
    )
    
    # Run complete workflow
    result = await checker.run_parking_check(resolution=1080)
    
    # Display results
    if result['success']:
        print(f"Zone: {result['zone_number']}")
        print(f"Violations: {result['num_violations']}")
        print(f"Recommendation: {result['recommendation']}")
    else:
        print(f"Error: {result['error']}")

# Run the demo
asyncio.run(main())
```

### Command Line Usage

```bash
# Run the complete demo
python apps/parking_violations.py

# Run tests
python -m pytest test_parking_violations.py -v
```

## 📋 Detailed Workflow

### 1. Connection Phase
- Establishes Bluetooth connection to Frame glasses
- Uploads Lua libraries and custom tap handler app
- Initializes camera and display systems
- Checks battery and memory status

### 2. Image Capture Phase  
- Displays "Capturing..." message on glasses
- Captures high-resolution image of parking area/street sign
- Handles capture failures with informative error messages

### 3. AI Analysis Phase
- Sends captured image to `/analysis/query` endpoint
- Uses optimized prompt for parking zone extraction:
  ```
  "Extract the text from within the street sign in the image. 
   Look specifically for zone numbers, parking zone identifiers, 
   or area numbers. If you find a zone number, return just the number. 
   If you cannot decipher it or there is no zone number visible, return 'NONE'"
  ```
- Parses VLM response using multiple regex patterns
- Handles various response formats ("Zone 5", "Area 12A", "NONE", etc.)

### 4. Violation Lookup Phase
- Queries violation database/API for the identified zone
- Currently uses mock data for demonstration:
  - Zone 1: 12 violations (high-traffic downtown)
  - Zone 2: 3 violations (residential)  
  - Zone 5: 15 violations (tourist area with heavy enforcement)
  - Unknown zones: 4 violations (moderate default)

### 5. Decision & Display Phase
- Compares violation count against threshold
- **Low violations** (< threshold): `"don' worry abahht it 👍"`
- **High violations** (≥ threshold): `"fuhgedaboutit 👎"`
- **No zone found**: `"No zone found"`
- **Analysis failed**: `"Analysis failed"`

### 6. Cleanup Phase
- Always disconnects from Frame glasses cleanly
- Logs comprehensive results and timing information

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
PARKING_API_BASE_URL=http://localhost:8000
PARKING_VIOLATION_THRESHOLD=5

# Frame Configuration  
FRAME_CAPTURE_RESOLUTION=1080
FRAME_AUTO_EXPOSURE_DELAY=3.0

# Logging
PARKING_LOG_LEVEL=INFO
```

### Custom Configuration

```python
checker = ParkingViolationsChecker(
    api_base_url="https://your-api-server.com",
    violation_threshold=8  # More conservative threshold
)

# Customize the zone extraction prompt
checker.zone_extraction_prompt = "Your custom prompt here..."

# Run with different settings
result = await checker.run_parking_check(resolution=720)
```

## 📊 API Integration

### `/analysis/query` Endpoint

The application uses the `/query` endpoint which provides Visual Question Answering (VQA):

**Request Format:**
```http
POST /analysis/query
Content-Type: multipart/form-data

image: <image_file>
question: <zone_extraction_prompt>
stream: false
```

**Response Format:**
```json
{
  "success": true,
  "answer": "Zone 5",
  "question": "Extract the text from within...",
  "request_id": "req_123",
  "timestamp": "2024-01-01T12:00:00",
  "processing_time_ms": 1500.0
}
```

### Zone Number Parsing

The system handles various VLM response formats:

| VLM Response                | Extracted Zone | Pattern Used               |
| --------------------------- | -------------- | -------------------------- |
| `"Zone 5"`                  | `"5"`          | `zone\s*([a-zA-Z0-9]+)`    |
| `"Area 12A"`                | `"12A"`        | `area\s*([a-zA-Z0-9]+)`    |
| `"Section B"`               | `"B"`          | `section\s*([a-zA-Z0-9]+)` |
| `"The number 7 is visible"` | `"7"`          | `number\s*([a-zA-Z0-9]+)`  |
| `"42"`                      | `"42"`         | `\b([0-9]+[a-zA-Z]?)\b`    |
| `"NONE"`                    | `None`         | Special case handling      |

## 🧪 Testing

### Run All Tests

```bash
# Run complete test suite
python -m pytest test_parking_violations.py -v

# Run specific test categories
python -m pytest test_parking_violations.py::TestParkingViolationsChecker -v
python -m pytest test_parking_violations.py::TestParkingViolationsIntegration -v

# Run with coverage
python -m pytest test_parking_violations.py --cov=apps.parking_violations
```

### Test Categories

1. **Unit Tests**: Individual method testing with mocks
2. **Integration Tests**: End-to-end workflow simulation
3. **Edge Case Tests**: Various VLM response formats
4. **Error Handling Tests**: Connection failures, API errors, etc.
5. **Mock Hardware Tests**: Frame glasses simulation

### Test Data

Tests use realistic mock data:
- Various VLM response formats
- Different violation counts per zone
- Hardware failure scenarios
- Network connectivity issues

## 🚨 Error Handling

The application provides comprehensive error handling:

### Connection Errors
```python
{
  "success": false,
  "error": "Failed to connect: Bluetooth connection failed",
  "step_failed": "connection"
}
```

### Capture Errors
```python
{
  "success": false, 
  "error": "Image capture failed: Camera hardware error",
  "step_failed": "capture"
}
```

### Analysis Errors
```python
{
  "success": false,
  "error": "API request failed with status 500: Internal Server Error", 
  "step_failed": "analysis"
}
```

### Frame Display Errors
- Automatically retries display operations
- Falls back to simplified messages if display fails
- Logs all display attempts for debugging

## 🔮 Future Enhancements

### Real Parking Data Integration
```python
async def get_num_violations(self, zone_number: str) -> int:
    """Integration with real parking APIs"""
    # Example: City parking management system
    response = await self.parking_api.get_violations(
        zone=zone_number,
        time_window="7d"  # Last 7 days
    )
    return response['violation_count']
```

### Advanced Zone Detection
- Support for multiple zones in single image
- Confidence scoring for zone detection
- Fuzzy matching for partially obscured signs
- Multi-language support for international use

### Enhanced User Experience
- Voice feedback through Frame speakers
- Haptic feedback for notifications
- Historical violation trends
- Personalized risk thresholds

### Real-time Features
- Live parking enforcement alerts
- Dynamic pricing information
- Available spot notifications
- Integration with mapping services

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/parking-enhancements`
3. **Add comprehensive tests** for new functionality
4. **Follow existing code style** and documentation standards
5. **Submit pull request** with detailed description

### Development Guidelines

- All new features must include tests
- Maintain backwards compatibility with existing API
- Document all public methods and classes
- Use type hints for better code clarity
- Follow async/await patterns for I/O operations

## 📄 License

This project is part of the Frame BLE Connect system. See main repository for license details.

## 🆘 Troubleshooting

### Common Issues

**"Not connected to Frame glasses"**
- Ensure Frame glasses are paired via Bluetooth
- Check battery level (should be > 20%)
- Verify Frame SDK installation

**"API request failed"**
- Confirm analysis server is running on correct port
- Check network connectivity
- Verify API endpoint URLs

**"No zone number detected"**
- Ensure clear view of parking sign in image
- Try different capture angle or lighting
- Check image quality and resolution

**"Capture failed"**
- Clean Frame camera lens
- Ensure adequate lighting
- Check for Frame hardware issues

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

checker = ParkingViolationsChecker()
result = await checker.run_parking_check()
```

### Hardware Testing

Test Frame connection without full workflow:
```python
from src.api.services.frame_msg_service import FrameService

frame_service = FrameService()
result = await frame_service.connect()
print(f"Connection: {result}")

await frame_service.display_text("Test message")
await frame_service.disconnect()
``` 