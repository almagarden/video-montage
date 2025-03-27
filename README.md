# Video Montage API

A FastAPI-based service that creates video montages from multiple videos with background music. The service arranges videos in a grid layout and adds background music to create a seamless montage.

## Features

- Create video montages with multiple videos in a dynamic grid layout
- Background music support with automatic duration matching
- Smart video duration handling:
  - If total duration is shorter than requested, the last video is looped
  - If total duration is longer than requested, videos are proportionally trimmed
- Automatic grid layout calculation based on number of videos
- API key authentication with user management
- Rate limiting and quota management
- Progress tracking for video generation tasks
- High-quality output (1080p resolution)

## Prerequisites

- Docker
- Docker Compose

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd video-montage
```

2. Create a `.env` file:
```bash
cp .env.example .env
```
Edit the `.env` file and set your desired configuration values:
```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/video_montage
STORAGE_DIR=/app/storage
API_V1_STR=/api/v1
SECRET_KEY=your-secret-key-here
RATE_LIMIT_PER_MINUTE=5
```

3. Build and start the services:
```bash
docker-compose up -d --build
```

4. Initialize the database:
```bash
docker-compose exec app ./scripts/init_db.sh
```

## API Usage

### Authentication

1. Create a new user and get an API key:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/users" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "monthly_quota": 100}'
```

Response:
```json
{
  "id": "user-id",
  "email": "user@example.com",
  "api_key": "your-api-key",
  "monthly_quota": 100
}
```

2. Generate a video montage:
```bash
curl -X POST "http://localhost:8000/api/v1/video-generation/generate" \
     -H "Content-Type: application/json" \
     -H "api-key: YOUR_API_KEY" \
     -d '{
       "type": "LoopVideo",
       "data": {
         "background_url": "https://example.com/background.mp3",
         "media_list": [
           "https://example.com/video1.mp4",
           "https://example.com/video2.mp4",
           "https://example.com/video3.mp4"
         ],
         "duration": 30
       }
     }'
```

Response:
```json
{
  "success": true,
  "message": "Video generation started",
  "data": {
    "id": "task-id"
  }
}
```

3. Check task progress:
```bash
curl "http://localhost:8000/api/v1/video-generation/progress/TASK_ID" \
     -H "api-key: YOUR_API_KEY"
```

Response:
```json
{
  "success": true,
  "message": "Task status retrieved",
  "data": {
    "status": "processing",
    "progress": 0.5,
    "url": null,
    "error": null
  }
}
```

### Video Generation Details

The service handles video montage creation with the following logic:

1. **Video Layout**:
   - Videos are arranged in a grid layout (2x2, 3x3, etc.)
   - Grid size automatically adjusts based on number of videos
   - All videos are resized to maintain consistent quality
   - Output resolution is 1080p (1920x1080)

2. **Duration Handling**:
   - If no duration specified: uses total length of all videos
   - If duration specified:
     - Shorter than total: last video is looped to fill remaining time
     - Longer than total: videos are proportionally trimmed

3. **Audio Handling**:
   - Original video audio is removed
   - Background music (from background_url) is added
   - Music is looped or trimmed to match video duration

4. **Output Format**:
   - Video: H.264 codec (MP4)
   - Audio: AAC codec
   - Frame rate: 24 FPS

## Rate Limits

- 5 requests per minute per user
- Configurable monthly quota per user (default: 100)
- Rate limits are enforced per API key

## Error Handling

The API returns appropriate HTTP status codes:

- 200: Successful operation
- 400: Invalid request data
- 401: Missing or invalid API key
- 403: Unauthorized access or quota exceeded
- 404: Resource not found
- 429: Rate limit exceeded
- 500: Internal server error

## Development

To run the application in development mode:

```bash
docker-compose up --build
```

The API documentation will be available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

The project includes comprehensive tests for all components. To run the tests:

```bash
# Run all tests with coverage report
docker-compose run test

# Run specific test file
docker-compose run test pytest tests/test_auth.py -v

# Run tests with specific marker
docker-compose run test pytest -v -m "auth"
```

### Test Coverage

The test suite covers:
- API endpoints and request validation
- Authentication and rate limiting
- Video generation service
- Database operations
- Error handling and edge cases

To view the test coverage report:
```bash
docker-compose run test pytest --cov=app --cov-report=html
```
The coverage report will be generated in the `htmlcov` directory.

## License

MIT 