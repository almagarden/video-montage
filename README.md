# Video Montage API

A FastAPI service that creates video montages by combining multiple videos sequentially with background music. Each video plays in full screen, maintaining consistent dimensions throughout the montage.

## Features

- **Sequential Video Playback**: Videos play one after another in full screen
- **Consistent Dimensions**: All videos are automatically resized to match the first video's dimensions
- **Smart Duration Control**:
  - When target duration is shorter than total video length: All videos are proportionally shortened
  - When target duration is longer than total video length: The last video loops to fill remaining time
- **Background Music**: Add background audio track that automatically:
  - Loops if shorter than the video duration
  - Trims if longer than the video duration
- **API Security**:
  - API key authentication
  - Rate limiting (5 requests/minute)
  - Monthly quota system
- **Progress Tracking**: Monitor video generation progress in real-time

## Prerequisites

- Docker
- Docker Compose

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/video-montage.git
cd video-montage
```

2. Create a `.env` file:
```bash
cp .env.example .env
```

3. Build and start services:
```bash
docker-compose up -d
```

4. Initialize the database:
```bash
docker-compose exec app python init_db.py
```

## API Usage

### Authentication

All endpoints require an API key as a query parameter:
```
?api_key=your_api_key_here
```

### Generate Video Montage

**Endpoint**: `POST /api/video-generation/generate`

**Request**:
```bash
curl -X POST "http://localhost:8000/api/video-generation/generate?api_key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "background_url": "https://example.com/background.mp3",
    "media_list": [
      "https://example.com/video1.mp4",
      "https://example.com/video2.mp4"
    ],
    "duration": 60
  }'
```

**Parameters**:
- `background_url` (required): URL to the background audio file (MP3)
- `media_list` (required): Array of video URLs (MP4)
- `duration` (optional): Target duration in seconds

**Response**:
```json
{
  "id": "task_id",
  "status": "pending",
  "progress": 0.0
}
```

### Check Progress

**Endpoint**: `GET /api/video-generation/progress/{task_id}`

**Request**:
```bash
curl "http://localhost:8000/api/video-generation/progress/task_id?api_key=YOUR_API_KEY"
```

**Response**:
```json
{
  "id": "task_id",
  "status": "done",
  "progress": 1.0,
  "output_url": "/storage/videos/output_task_id.mp4"
}
```

**Status Values**:
- `pending`: Task is queued
- `processing`: Video is being generated
- `done`: Video is ready
- `error`: Generation failed

## Video Generation Details

### Video Processing

1. **Dimension Handling**:
   - First video's dimensions become the template
   - Subsequent videos are processed to match:
     - If video is wider: Fit to height and crop width
     - If video is taller: Fit to width and crop height

2. **Duration Control**:
   ```
   Example: 3 videos of 10s, 15s, and 20s (total 45s)
   
   Case 1: Target duration = 30s
   - Each video shortened proportionally (×0.67)
   - Result: 6.7s, 10s, 13.3s
   
   Case 2: Target duration = 60s
   - Play all videos (45s)
   - Loop last video for remaining time (15s)
   ```

3. **Audio Handling**:
   ```
   Example: Background audio is 40s, video is 60s
   - Audio loops once to reach 80s
   - Trims to match 60s
   
   Example: Background audio is 90s, video is 60s
   - Audio trimmed to 60s
   ```

## Error Handling

### HTTP Status Codes
- 200: Success
- 400: Invalid request data
- 401: Missing/invalid API key
- 403: Unauthorized access
- 429: Rate limit exceeded
- 500: Internal server error

### Common Error Scenarios
```json
{
  "status": "error",
  "error_message": "Failed to download video: https://example.com/video1.mp4"
}
```

## Development

Run in development mode:
```bash
docker-compose -f docker-compose.dev.yml up
```

API Documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run all tests:
```bash
docker-compose run --rm test pytest
```

Run specific test file:
```bash
docker-compose run --rm test pytest tests/test_video_service.py -v
```

Generate coverage report:
```bash
docker-compose run --rm test pytest --cov=app --cov-report=html
```

### Test Coverage

The test suite includes:
1. **Video Processing Tests**:
   - Sequential arrangement
   - Aspect ratio matching
   - Duration control
   - Audio handling

2. **API Tests**:
   - Input validation
   - Authentication
   - Progress tracking
   - Error handling

3. **Integration Tests**:
   - End-to-end video generation
   - File handling
   - Database operations

## License

MIT 