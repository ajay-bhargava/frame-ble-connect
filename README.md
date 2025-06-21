# Frame Connect

A comprehensive Python library for connecting to Frame smart glasses, capturing photos, and processing images with AI-powered food analysis and restaurant discovery.

## 🚀 Features

### Core Frame Glasses Integration
- **Connect to Frame smart glasses** via Bluetooth Low Energy (BLE)
- **Capture photos** from the Frame's built-in camera
- **Display live camera feed** using OpenCV
- **Control Frame hardware** using Lua scripts

### AI-Powered Food Analysis
- **Food identification** using Moondream AI vision model
- **Restaurant discovery** with NYC restaurant database
- **Google Maps integration** for navigation
- **Real-time analysis** with Frame glasses display

### Deployment Options
- **Local FastAPI server** for development and testing
- **Modal cloud deployment** for production OCR/vision processing

## 🍽️ Complete Workflow

1. **User takes photo** of food with Frame glasses
2. **AI analyzes** the food item using Moondream
3. **System finds** a restaurant in NYC serving that food
4. **Maps link** is generated for easy navigation
5. **Results displayed** on glasses and returned via API

## 📋 Prerequisites

- Python 3.12 or higher
- Frame smart glasses
- Bluetooth capability on your device
- Moondream AI API key (get from [Moondream Playground](https://moondream.ai/c/playground))

## 🛠️ Installation

### 1. Clone and Setup
```bash
git clone <repository-url>
cd frame-ble-connect
git checkout feature/init  # or main if merged
```

### 2. Create and Activate Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp env.example .env
# Edit .env and add your Moondream API key
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

# Google API Key (optional - for enhanced restaurant search)
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Logging
LOG_LEVEL=info
```

## 🚀 Usage

### Option 1: Local FastAPI Server (Recommended for Development)

#### Start the API Server
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

# Start the server (choose one method)
python run.py              # From root directory
# OR
python src/api/main.py     # Direct from source
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Test the Complete Workflow
```bash
# 1. Connect to glasses
curl -X POST http://localhost:8000/api/v1/device/connect

# 2. Capture, analyze, and find restaurant
curl -X POST http://localhost:8000/api/v1/analysis/capture-and-find-restaurant \
  -F "resolution=720"

# 3. Check the response for restaurant info and maps link
```

#### Using Python
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

### Option 2: Modal Cloud Deployment (Production)

#### Deploy to Modal
```bash
# Deploy the Modal-based API (requires Modal account)
modal deploy src/api/modal_app.py
```

#### Use Modal API
```bash
# The Modal API will be available at the provided URL
# Use for cloud-based OCR and vision processing
```

### Option 3: Basic Photo Capture (Original Functionality)

#### Single Photo Capture
```bash
uv run python src/connect/single_capture.py
```

This will:
1. Connect to your Frame glasses via Bluetooth
2. Initialize the camera with autoexposure
3. Display a live camera feed (if display is available)
4. Capture a photo and save it as `captured_frame.jpg`
5. Show the captured image briefly before exiting

#### Live Camera Feed
```bash
uv run python src/connect/main.py
```

## 📚 API Endpoints

### Device Management
- `GET /api/v1/device/status` - Get Frame glasses status
- `POST /api/v1/device/connect` - Connect to glasses
- `POST /api/v1/device/disconnect` - Disconnect from glasses
- `POST /api/v1/device/capture` - Capture image
- `POST /api/v1/device/display` - Display text on glasses

### AI Analysis
- `POST /api/v1/analysis/food` - Analyze food in uploaded image
- `POST /api/v1/analysis/food-to-restaurant` - Complete workflow with uploaded image
- `POST /api/v1/analysis/capture-and-analyze` - Capture and analyze from glasses
- `POST /api/v1/analysis/capture-and-find-restaurant` - Complete workflow from glasses

## 🍕 Supported Food Items

The restaurant service includes data for common NYC restaurants:

- **Pizza**: Joe's Pizza (Bleecker St)
- **Sushi**: Sushi Nakazawa (Commerce St)
- **Burger**: Shake Shack (Madison Square Park)
- **Pasta**: Carbone (Thompson St)
- **Taco**: Los Tacos No. 1 (43rd St)

For other food items, a generic search is performed.

## 📁 Project Structure

```
frame-ble-connect/
├── run.py                    # 🚀 Main entry point
├── src/
│   ├── api/
│   │   ├── main.py          # 🏗️ FastAPI application
│   │   ├── routes/          # 🛣️ API endpoints
│   │   ├── models/          # 📋 Data models
│   │   └── services/        # 🔧 Business logic
│   ├── ai/
│   │   └── processors/      # 🤖 AI processing
│   ├── connect/             # 📱 Frame glasses connection
│   └── utils/               # 🛠️ Utilities
├── static/
│   └── images/              # 📸 Captured images
├── .env                     # ⚙️ Environment variables
└── README.md               # 📖 Documentation
```

## 🔧 Development

### Running the Server
```bash
# Development mode (with auto-reload)
python run.py

# Production mode
RELOAD=false python run.py
```

### Testing
```bash
# Test API endpoints
python test_api.py

# Test restaurant service
python test_restaurant.py
```

### Code Structure
- **`run.py`**: Simple entry point for starting the server
- **`src/api/main.py`**: FastAPI application with all routes and middleware
- **`src/api/routes/`**: API endpoint definitions
- **`src/ai/processors/`**: AI processing logic (Moondream integration)
- **`src/connect/`**: Frame glasses BLE connection and camera control

## 🚨 Troubleshooting

### Common Issues

1. **Port already in use**: Change the PORT in your .env file
2. **Frame connection fails**: Ensure glasses are powered on and Bluetooth is enabled
3. **Moondream API errors**: Verify your API key is correct and has sufficient credits
4. **Import errors**: Make sure you're running from the project root and virtual environment is activated
5. **Virtual environment issues**: Ensure you've created and activated the virtual environment before installing dependencies
6. **Display issues**: Application will fall back to headless mode automatically

### Debug Mode
```bash
LOG_LEVEL=debug python run.py
```

### Authentication Issues
If you encounter authentication issues with GitHub:
```bash
# Clear git credentials
git credential-cache exit

# Re-authenticate
git push origin feature/init
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

## 🙏 Acknowledgments

- Frame glasses SDK and Lua integration
- Moondream AI for vision processing
- Modal for cloud deployment capabilities



