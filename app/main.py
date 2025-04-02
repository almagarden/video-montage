from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from app.api.endpoints import video_endpoints, auth
from app.core.config import settings
from app.db.base import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

description = """
# Video Montage API 🎥

This API allows you to create video montages by combining multiple videos and adding background music.

## Features

* 📝 User Management
* 🔑 API Key Authentication
* 🎬 Video Montage Generation
* 🎵 Background Music Integration
* 📊 Progress Tracking

## Authentication

All API endpoints (except user creation) require an API key to be passed in the `X-API-Key` header.

## Rate Limiting

* Maximum 5 requests per minute per user
* Monthly quota system enforced per user

## Example Usage

1. Create a user to get an API key
2. Use the API key to generate video montages
3. Track the progress of your video generation
4. Download the final video when ready

For detailed examples and testing, use the interactive API documentation below.
"""

app = FastAPI(
    title="Video Montage API",
    description=description,
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "API Support",
        "url": "http://example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for video storage
app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

# Include routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"}
    }
)

app.include_router(
    video_endpoints.router,
    prefix=f"{settings.API_V1_STR}/video-generation",
    tags=["Video Generation"],
    responses={
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded or quota exceeded"}
    }
)

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint that provides API information and documentation links.
    """
    return {
        "message": "Welcome to Video Montage API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 