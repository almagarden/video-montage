# Video Montage API

A FastAPI-based service that creates video montages from multiple videos with a background video.

## Features

- Create video montages with multiple videos in a grid layout
- Background video support
- API key authentication
- Rate limiting and quota management
- Progress tracking for video generation tasks

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
Edit the `.env` file and set your desired configuration values.

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

2. Use the API key in subsequent requests:
```bash
curl -X POST "http://localhost:8000/api/v1/video-generation/generate" \
     -H "Content-Type: application/json" \
     -H "api-key: YOUR_API_KEY" \
     -d '{
       "type": "LoopVideo",
       "data": {
         "background_url": "https://example.com/background.mp4",
         "media_list": ["https://example.com/video1.mp4"],
         "duration": 30
       }
     }'
```

3. Check task progress:
```bash
curl "http://localhost:8000/api/v1/video-generation/progress/TASK_ID" \
     -H "api-key: YOUR_API_KEY"
```

## Rate Limits

- 5 requests per minute per user
- Configurable monthly quota per user (default: 100)

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
- API endpoints
- Authentication and rate limiting
- Video generation service
- Database operations

To view the test coverage report:
```bash
docker-compose run test pytest --cov=app --cov-report=html
```
The coverage report will be generated in the `htmlcov` directory.

## License

MIT 