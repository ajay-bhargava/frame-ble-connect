# Frame Glasses AI API

A FastAPI server that provides AI-powered vision analysis for Frame glasses using Moondream AI. This API enables real-time food analysis, restaurant discovery, and maps integration for a complete food-to-restaurant experience.

## 🚀 Features

- **Food Analysis**: Analyze food items, estimate calories, and identify nutrients
- **Restaurant Discovery**: Find restaurants in NYC based on food items
- **Maps Integration**: Get Google Maps links for restaurant locations
- **Real-time Capture**: Capture images directly from Frame glasses
- **AI Integration**: Powered by Moondream AI for advanced vision processing
- **Device Management**: Connect, disconnect, and monitor Frame glasses status
- **RESTful API**: Clean, documented API endpoints with automatic OpenAPI docs

## 🍽️ Complete Workflow

1. **User takes photo** of food with Frame glasses
2. **AI analyzes** the food item using Moondream
3. **System finds** a restaurant in NYC serving that food
4. **Maps link** is generated for easy navigation
5. **Results displayed** on glasses and returned via API

## 📋 Prerequisites

- Python 3.12+
- Frame glasses with Bluetooth connectivity
- Moondream AI API key (get from [Moondream Playground](https://moondream.ai/c/playground))
- Google API key (optional, for enhanced restaurant search)

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
   # Edit .env and add your API keys
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

# Google API Key (optional - for restaurant search)
GOOGLE_API_KEY=your_google_api_key_here

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

#### `POST /api/v1/device/connect`
Connect to Frame glasses.

#### `POST /api/v1/device/disconnect`
Disconnect from Frame glasses.

#### `POST /api/v1/device/capture`
Capture an image from Frame glasses.

#### `POST /api/v1/device/display`
Display text on Frame glasses.

### AI Analysis

#### `POST /api/v1/analysis/food`
Analyze food items in an uploaded image.

#### `POST /api/v1/analysis/general`
Perform general image analysis with custom prompt.

#### `POST /api/v1/analysis/food-to-restaurant` ⭐ **NEW**
Complete workflow: Analyze food → Find restaurant → Return maps link.

**Request**: Multipart form with image file.

**Response**:
```json
{
  "success": true,
  "food_analysis": {
    "primary_food_item": "pizza",
    "structured_data": { ... }
  },
  "restaurant_found": true,
  "restaurant": {
    "name": "Joe's Pizza",
    "address": "123 Bleecker St, New York, NY 10012",
    "rating": 4.5,
    "price_level": "$$",
    "maps_link": "https://maps.google.com/?q=Joe's+Pizza+123+Bleecker+St+New+York+NY"
  },
  "maps_link": "https://maps.google.com/?q=Joe's+Pizza+123+Bleecker+St+New+York+NY",
  "primary_food_item": "pizza",
  "processing_time_ms": 1250
}
```

#### `POST /api/v1/analysis/capture-and-analyze`
Capture image from glasses and analyze for food items.

#### `POST /api/v1/analysis/capture-and-find-restaurant` ⭐ **NEW**
Complete workflow: Capture from glasses → Analyze food → Find restaurant → Display on glasses.

## 🍽️ Food-to-Restaurant Workflow

### Option 1: Upload Image
1. **Upload food image**: `POST /api/v1/analysis/food-to-restaurant`
2. **Get restaurant info**: Returns restaurant details + maps link
3. **Navigate**: Use the maps link on your phone

### Option 2: Capture from Glasses
1. **Capture and analyze**: `POST /api/v1/analysis/capture-and-find-restaurant`
2. **Results displayed**: Restaurant name appears on glasses
3. **Get full results**: API returns complete data including maps link

## 🔍 Example Usage

### Complete food-to-restaurant workflow:

```bash
# 1. Connect to glasses
curl -X POST http://localhost:8000/api/v1/device/connect

# 2. Capture, analyze, and find restaurant
curl -X POST http://localhost:8000/api/v1/analysis/capture-and-find-restaurant \
  -F "resolution=720"

# 3. Check the response for restaurant info and maps link
```

### Using Python requests:

```python
import requests

base_url = "http://localhost:8000/api/v1"

# Complete workflow
response = requests.post(
    f"{base_url}/analysis/capture-and-find-restaurant",
    data={"resolution": 720}
)

result = response.json()
print(f"Found: {result['restaurant']['name']}")
print(f"Maps: {result['maps_link']}")
```

## 🏗️ Project Structure

```
frame-ble-connect/
├── src/
│   ├── api/                    # FastAPI server
│   │   ├── main.py            # Main FastAPI app
│   │   ├── routes/            # API endpoints
│   │   │   ├── analysis.py    # AI analysis & restaurant routes
│   │   │   └── device.py      # Device management routes
│   │   ├── models/            # Pydantic models
│   │   │   ├── requests.py    # Request models
│   │   │   └── responses.py   # Response models
│   │   └── services/          # Business logic
│   │       ├── frame_service.py # Frame glasses service
│   │       └── restaurant_service.py # Restaurant search service
│   ├── ai/                    # AI processing
│   │   └── processors/
│   │       └── moondream_processor.py # Moondream AI integration
│   ├── connect/               # Existing Frame connection code
│   └── utils/                 # Shared utilities
├── start_api.py              # API startup script
├── env.example               # Environment configuration example
└── README_API.md            # This file
```

## 🍕 Supported Food Items

The restaurant service includes mock data for common NYC restaurants:

- **Pizza**: Joe's Pizza (Bleecker St)
- **Sushi**: Sushi Nakazawa (Commerce St)
- **Burger**: Shake Shack (Madison Square Park)
- **Pasta**: Carbone (Thompson St)
- **Taco**: Los Tacos No. 1 (43rd St)

For other food items, a generic search is performed.

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
4. **Restaurant search fails**: Check if Google API key is set (optional for MVP)

### Debug Mode:
```bash
LOG_LEVEL=debug python start_api.py
```

## 📝 TODO

- [ ] Integrate real Google Places API for restaurant search
- [ ] Add WebSocket support for real-time streaming
- [ ] Implement image caching and optimization
- [ ] Add authentication and rate limiting
- [ ] Improve food analysis parsing
- [ ] Add support for multiple AI providers
- [ ] Implement batch processing
- [ ] Add metrics and monitoring
- [ ] Add user location detection
- [ ] Implement restaurant ratings and reviews

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 