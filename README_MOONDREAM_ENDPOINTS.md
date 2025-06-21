# Moondream AI Endpoints Documentation

This document describes the four new Moondream AI endpoints that have been added to the Frame BLE Connect API. These endpoints provide advanced computer vision capabilities including image captioning, visual question answering, object detection, and object localization.

## Overview

The new endpoints extend the existing `/analysis` router with four specialized Moondream AI capabilities:

1. **`/analysis/caption`** - Generate natural language descriptions of images
2. **`/analysis/query`** - Visual Question Answering (VQA) 
3. **`/analysis/detect`** - Object detection with bounding boxes
4. **`/analysis/point`** - Object localization with center points

All endpoints accept image uploads and return structured JSON responses with processing metadata.

## Endpoints

### 1. Caption Endpoint

**POST** `/analysis/caption`

Generate natural language descriptions of images, from brief summaries to detailed explanations of visual content.

**Parameters:**
- `image` (File, required): Image file to analyze (JPEG, PNG, GIF)
- `length` (string, optional): Caption detail level
  - `"short"`: Brief 1-2 sentence summary
  - `"normal"`: Detailed description (default)
- `stream` (boolean, optional): Stream response token by token (default: false)

**Response:**
```json
{
  "success": true,
  "caption": "A detailed caption describing the image...",
  "request_id": "2025-03-25_caption_123456",
  "length": "normal",
  "timestamp": "2025-03-25T21:00:39.123Z",
  "processing_time_ms": 1250.5,
  "error_message": null
}
```

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/analysis/caption" \
  -F "image=@test_image.jpg" \
  -F "length=short"
```

**Use Cases:**
- Generate alt text for accessibility
- Content indexing and organization
- Image search functionality
- Social media content creation

### 2. Query Endpoint

**POST** `/analysis/query`

Ask natural language questions about images and receive detailed answers (Visual Question Answering).

**Parameters:**
- `image` (File, required): Image file to analyze (JPEG, PNG, GIF)
- `question` (string, required): Natural language question (max 512 characters)
- `stream` (boolean, optional): Stream response token by token (default: false)

**Response:**
```json
{
  "success": true,
  "answer": "The main subject is a red sports car...",
  "question": "What is the main subject of this image?",
  "request_id": "2025-03-25_query_123456",
  "timestamp": "2025-03-25T21:00:39.123Z",
  "processing_time_ms": 1350.2,
  "error_message": null
}
```

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/analysis/query" \
  -F "image=@test_image.jpg" \
  -F "question=What colors are prominent in this image?"
```

**Example Questions:**
- "What is the main subject of this image?"
- "What colors are prominent in this image?"
- "Is this image taken indoors or outdoors?"
- "How many people are in this image?"
- "What time of day was this photo taken?"

### 3. Detect Endpoint

**POST** `/analysis/detect`

Detect and locate specific objects in images, returning bounding box coordinates for each detected instance.

**Parameters:**
- `image` (File, required): Image file to analyze (JPEG, PNG, GIF)
- `object_type` (string, required): Type of object to detect

**Response:**
```json
{
  "success": true,
  "objects": [
    {
      "x_min": 0.2,
      "y_min": 0.3,
      "x_max": 0.6,
      "y_max": 0.8
    }
  ],
  "object_type": "person",
  "count": 1,
  "request_id": "2025-03-25_detect_123456",
  "timestamp": "2025-03-25T21:00:39.123Z",
  "processing_time_ms": 980.1,
  "error_message": null
}
```

**Coordinate System:**
- Coordinates are normalized to range 0-1
- (0,0) is top-left corner, (1,1) is bottom-right corner
- To convert to pixels: `pixel_x = x * image_width`

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/analysis/detect" \
  -F "image=@test_image.jpg" \
  -F "object_type=person"
```

**Common Object Types:**
- `person`, `face`, `car`, `dog`, `cat`
- `building`, `furniture`, `text`, `food`, `plant`
- Custom objects (zero-shot detection)

### 4. Point Endpoint

**POST** `/analysis/point`

Get precise center point coordinates for objects. Unlike detect, this returns center points rather than bounding boxes.

**Parameters:**
- `image` (File, required): Image file to analyze (JPEG, PNG, GIF)
- `object_type` (string, required): Type of object to locate

**Response:**
```json
{
  "success": true,
  "points": [
    {
      "x": 0.65,
      "y": 0.42
    }
  ],
  "object_type": "person",
  "count": 1,
  "request_id": "2025-03-25_point_123456",
  "timestamp": "2025-03-25T21:00:39.123Z",
  "processing_time_ms": 920.8,
  "error_message": null
}
```

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/analysis/point" \
  -F "image=@test_image.jpg" \
  -F "object_type=face"
```

**Use Cases:**
- Precise targeting for UI interactions
- Click/tap coordinates for automation
- Object counting and positioning
- Augmented reality overlays

## Error Handling

All endpoints return standardized error responses:

```json
{
  "success": false,
  "error_message": "Detailed error description",
  "timestamp": "2025-03-25T21:00:39.123Z",
  "processing_time_ms": 0
}
```

**Common HTTP Status Codes:**
- `400` - Bad Request (invalid parameters or image format)
- `401` - Unauthorized (invalid or missing API key)
- `413` - Payload Too Large (image size exceeds limits)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error (server-side issue)

## Testing

A comprehensive test script is provided: `test_moondream_endpoints.py`

**Run all tests:**
```bash
python test_moondream_endpoints.py [image_path]
```

**Run with default test image:**
```bash
python test_moondream_endpoints.py
```

The test script will:
- Test all four endpoints with various parameters
- Validate responses and error handling
- Measure performance and processing times
- Generate a detailed test report
- Save results to `moondream_test_results.json`

## Integration Examples

### Python with httpx

```python
import httpx
from pathlib import Path

async def test_caption():
    async with httpx.AsyncClient() as client:
        with open("test_image.jpg", "rb") as f:
            response = await client.post(
                "http://localhost:8000/analysis/caption",
                files={"image": f},
                data={"length": "normal"}
            )
        result = response.json()
        print(f"Caption: {result['caption']}")
```

### JavaScript/TypeScript

```javascript
const formData = new FormData();
formData.append('image', imageFile);
formData.append('question', 'What is in this image?');

const response = await fetch('http://localhost:8000/analysis/query', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Answer:', result.answer);
```

### Frame Integration

The endpoints integrate seamlessly with the existing Frame service:

```python
# Capture from Frame glasses and analyze
frame_service = FrameService()
await frame_service.connect()

capture_result = await frame_service.capture_image(720)
if capture_result["success"]:
    # Use any of the four endpoints
    analysis_result = await moondream_processor.caption(
        capture_result["image_data"], 
        length="short"
    )
    
    # Display result on glasses
    if analysis_result["success"]:
        await frame_service.display_text(analysis_result["caption"][:50])

await frame_service.disconnect()
```

## Performance Considerations

- **Processing Time**: Typical range 1-3 seconds per image
- **Image Size**: Maximum 10MB, optimal < 5MB
- **Supported Formats**: JPEG, PNG, GIF (first frame only)
- **Rate Limits**: Apply based on Moondream API plan
- **Concurrent Requests**: Supported, but may impact performance

## Advanced Features

### Zero-Shot Detection
Both `detect` and `point` endpoints support zero-shot object detection:

```bash
# Detect custom objects
curl -X POST "http://localhost:8000/analysis/detect" \
  -F "image=@scene.jpg" \
  -F "object_type=red traffic light"

curl -X POST "http://localhost:8000/analysis/point" \
  -F "image=@ui.jpg" \
  -F "object_type=submit button"
```

### Streaming Responses
Caption and query endpoints support streaming (when enabled):

```python
# Note: Streaming implementation would require additional SSE handling
data = {"question": "Describe this image", "stream": True}
# Implementation depends on your streaming requirements
```

## Configuration

Ensure your `.env` file contains:

```env
MOONDREAM_API_KEY=your_moondream_api_key_here
```

The API key is required for all Moondream endpoints to function.

## Troubleshooting

**API Key Issues:**
- Ensure `MOONDREAM_API_KEY` is set in environment variables
- Verify API key has proper permissions
- Check API key format and validity

**Image Processing Errors:**
- Verify image format is supported (JPEG, PNG, GIF)
- Check image file size (< 10MB recommended)
- Ensure image is not corrupted

**Performance Issues:**
- Use appropriate image resolution (720p-1080p optimal)
- Consider reducing image size for faster processing
- Monitor rate limits and concurrent request limits

**Network Connectivity:**
- Verify API server is running on localhost:8000
- Check firewall settings
- Ensure stable internet connection for Moondream API calls 