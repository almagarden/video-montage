from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.endpoints import video_endpoints, auth
from app.core.config import settings
from app.db.base import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Video Montage API",
    description="API for creating video montages with background music",
    version="1.0.0"
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
    tags=["auth"]
)

app.include_router(
    video_endpoints.router,
    prefix=f"{settings.API_V1_STR}/video-generation",
    tags=["video"]
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Video Montage API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 