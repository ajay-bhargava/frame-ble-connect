# Frame Glasses AI API

A FastAPI server that provides AI-powered vision analysis for Frame glasses using Moondream AI. This API enables real-time food analysis, object detection, and scene understanding through the Frame glasses camera.

## 🚀 Features

- **Food Analysis**: Analyze food items, estimate calories, and identify nutrients
- **Real-time Capture**: Capture images directly from Frame glasses
- **AI Integration**: Powered by Moondream AI for advanced vision processing
- **Device Management**: Connect, disconnect, and monitor Frame glasses status
- **RESTful API**: Clean, documented API endpoints with automatic OpenAPI docs

## 📋 Prerequisites

- Python 3.12+
- Frame glasses with Bluetooth connectivity
- Moondream AI API key (get from [Moondream Playground](https://moondream.ai/c/playground))

## 🛠️ Installation

1. **Clone and setup the project**:
   ```bash
   git clone <your-repo>
   cd frame-ble-connect
   git checkout feature/init
   ```

2. **Install dependencies**:
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env and add your MOONDREAM_API_KEY
   ```

## 🔧 Configuration

Create a `.env` file with the following variables:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true

# Moondream AI API Key
MOONDREAM_API_KEY=your_actual_api_key_here

# Optional: Logging
LOG_LEVEL=info
```

## 🚀 Running the API

### Option 1: Using the startup script
```bash
python start_api.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using uv
```bash
uv run python start_api.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Endpoints

### Device Management

#### `GET /api/v1/device/status`
Get current Frame glasses device status.

**Response**:
```json
{
  "connected": true,
  "battery_level": 85,
  "memory_usage": "1024KB",
  "last_capture": "2024-01-15T10:30:00"
}
```

#### `POST /api/v1/device/connect`
Connect to Frame glasses.

#### `POST /api/v1/device/disconnect`
Disconnect from Frame glasses.

#### `POST /api/v1/device/capture`
Capture an image from Frame glasses.

**Request**:
```json
{
  "resolution": 720,
  "auto_exposure": true
}
```

#### `POST /api/v1/device/display`
Display text on Frame glasses.

### AI Analysis

#### `POST /api/v1/analysis/food`
Analyze food items in an uploaded image.

**Request**: Multipart form with image file and optional custom prompt.

**Response**:
```json
{
  "success": true,
  "analysis_type": "food_analysis",
  "timestamp": "2024-01-15T10:30:00",
  "processing_time_ms": 1250,
  "result": {
    "food_items": [
      {
        "name": "Apple",
        "confidence": 0.95,
        "calories": 95,
        "nutrients": {
          "protein": "0.5g",
          "carbs": "25g",
          "fiber": "4g"
        }
      }
    ],
    "total_calories": 95,
    "dietary_restrictions": []
  },
  "food_items": [],
  "total_calories": 95,
  "dietary_restrictions": []
}
```

#### `POST /api/v1/analysis/general`
Perform general image analysis with custom prompt.

#### `POST /api/v1/analysis/capture-and-analyze`
Capture image from glasses and analyze for food items in one request.

## 🍽️ Food Analysis Workflow

1. **Connect to glasses**: `POST /api/v1/device/connect`
2. **Capture image**: `POST /api/v1/device/capture` or use combined endpoint
3. **Analyze food**: `POST /api/v1/analysis/food` with image data
4. **Display results**: Results are automatically displayed on glasses
5. **Disconnect**: `POST /api/v1/device/disconnect`

## 🔍 Example Usage

### Using curl for food analysis:

```bash
# 1. Connect to glasses
curl -X POST http://localhost:8000/api/v1/device/connect

# 2. Capture and analyze food
curl -X POST http://localhost:8000/api/v1/analysis/capture-and-analyze \
  -F "resolution=720"

# 3. Check device status
curl http://localhost:8000/api/v1/device/status
```

### Using Python requests:

```python
import requests

# Connect to API
base_url = "http://localhost:8000/api/v1"

# Connect to glasses
response = requests.post(f"{base_url}/device/connect")
print("Connected:", response.json())

# Capture and analyze food
response = requests.post(
    f"{base_url}/analysis/capture-and-analyze",
    data={"resolution": 720}
)
result = response.json()
print("Food analysis:", result)

# Display custom message
requests.post(f"{base_url}/device/display", json={"text": "Analysis complete!"})
```

## 🏗️ Project Structure

```
frame-ble-connect/
├── src/
│   ├── api/                    # FastAPI server
│   │   ├── main.py            # Main FastAPI app
│   │   ├── routes/            # API endpoints
│   │   │   ├── analysis.py    # AI analysis routes
│   │   │   └── device.py      # Device management routes
│   │   ├── models/            # Pydantic models
│   │   │   ├── requests.py    # Request models
│   │   │   └── responses.py   # Response models
│   │   └── services/          # Business logic
│   │       └── frame_service.py # Frame glasses service
│   ├── ai/                    # AI processing
│   │   └── processors/
│   │       └── moondream_processor.py # Moondream AI integration
│   ├── connect/               # Existing Frame connection code
│   └── utils/                 # Shared utilities
├── start_api.py              # API startup script
├── env.example               # Environment configuration example
└── README_API.md            # This file
```

## 🔧 Development

### Running tests:
```bash
pytest
```

### Code formatting:
```bash
ruff format src/
```

### Linting:
```bash
ruff check src/
```

## 🚨 Troubleshooting

### Common Issues:

1. **Import errors**: Make sure you're running from the project root
2. **Frame connection fails**: Ensure glasses are powered on and Bluetooth is enabled
3. **Moondream API errors**: Verify your API key is correct and has sufficient credits
4. **Port already in use**: Change the PORT in your .env file

### Debug Mode:
```bash
LOG_LEVEL=debug python start_api.py
```

## 📝 TODO

- [ ] Add WebSocket support for real-time streaming
- [ ] Implement image caching and optimization
- [ ] Add authentication and rate limiting
- [ ] Improve food analysis parsing
- [ ] Add support for multiple AI providers
- [ ] Implement batch processing
- [ ] Add metrics and monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 