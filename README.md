# Frame Connect

A low-level Python library for connecting to Frame smart glasses, capturing photos, and processing images with OCR capabilities.

## Overview

This repository provides tools to:
- **Connect to Frame smart glasses** via Bluetooth Low Energy (BLE)
- **Capture photos** from the Frame's built-in camera
- **Display live camera feed** using OpenCV
- **Process images** with OCR and vision capabilities via Modal deployment
- **Control Frame hardware** using Lua scripts

## Features

- **Single Photo Capture**: Take individual photos and save them locally
- **Live Camera Feed**: Real-time display of camera stream with OpenCV
- **Autoexposure Control**: Automatic exposure adjustment for optimal image quality
- **Cross-platform Support**: Works on macOS, Linux, and Windows
- **Headless Mode**: Operates without display for server environments
- **OCR Integration**: Cloud-based image processing and text extraction

## Installation

### Prerequisites

- Python 3.12 or higher
- Frame smart glasses
- Bluetooth capability on your device

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd connect
   ```

2. **Install dependencies using uv**:
   ```bash
   uv sync
   ```

   Alternatively, if you don't have `uv` installed:
   ```bash
   pip install uv
   uv sync
   ```

## Usage

### Basic Photo Capture

To capture a single photo from your Frame glasses:

```bash
uv run python src/connect/single_capture.py
```

This will:
1. Connect to your Frame glasses via Bluetooth
2. Initialize the camera with autoexposure
3. Display a live camera feed (if display is available)
4. Capture a photo and save it as `captured_frame.jpg`
5. Show the captured image briefly before exiting

### Key Controls

- **ESC**: Exit the application
- The application automatically captures after a 5-second autoexposure settling period

### API Server

The repository also includes a FastAPI server for OCR and vision processing:

```bash
# Deploy to Modal (requires Modal account and setup)
modal deploy src/api/api.py
```

## Project Structure

```
connect/
├── src/
│   ├── api/                    # Modal-based API for OCR/vision processing
│   │   └── api.py
│   └── connect/                # Main Frame connection library
│       ├── __init__.py
│       ├── connect.py          # Core connection utilities
│       ├── main.py             # Main application entry point
│       ├── single_capture.py   # Single photo capture example
│       └── lua/                # Lua scripts for Frame hardware control
│           └── camera_frame_app.lua
├── pyproject.toml              # Project configuration and dependencies
└── README.md                   # This file
```

## Dependencies

Key dependencies include:
- **frame-msg**: Communication protocol for Frame glasses
- **frame-ble**: Bluetooth Low Energy interface
- **opencv-python**: Image processing and display
- **Pillow**: Image manipulation
- **bleak**: Cross-platform Bluetooth LE library
- **fastapi**: Web API framework
- **modal**: Cloud deployment platform

## Troubleshooting

### Display Issues
If you encounter display issues on macOS or Linux, the application will automatically fall back to headless mode. Images will still be captured and saved, but the live preview won't be shown.

### Bluetooth Connection
Ensure your Frame glasses are:
- Powered on and in pairing mode
- Within Bluetooth range of your device
- Not connected to another device

### Permission Issues
On some systems, you may need to grant Bluetooth permissions to your terminal or Python application.

## Development

To run tests:
```bash
uv run pytest
```

To lint the code:
```bash
uv run ruff check src/
```

## License

[Add your license information here]

## Contributing

[Add contributing guidelines here]



