from typing import List, Optional
from pydantic import BaseModel, HttpUrl

class VideoGenerationRequest(BaseModel):
    background_url: HttpUrl  # URL for background audio track
    media_list: List[HttpUrl]  # List of video URLs
    duration: Optional[int] = None  # Target duration in seconds (optional)

    class Config:
        json_schema_extra = {
            "example": {
                "background_url": "https://example.com/background.mp3",
                "media_list": [
                    "https://example.com/video1.mp4",
                    "https://example.com/video2.mp4"
                ],
                "duration": 60
            }
        }

class VideoTaskResponse(BaseModel):
    id: str
    status: str
    progress: float
    output_url: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "processing",
                "progress": 0.5,
                "output_url": None,
                "error_message": None
            }
        } 