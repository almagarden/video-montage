from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class VideoGenerationRequest(BaseModel):
    type: str = Field(..., description="Type of video to generate")
    data: dict = Field(..., description="Video generation data")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "LoopVideo",
                "data": {
                    "background_url": "https://example.com/background.mp4",
                    "media_list": ["https://example.com/video1.mp4"],
                    "duration": 30
                }
            }
        }

class VideoGenerationData(BaseModel):
    background_url: str
    media_list: List[str]
    duration: Optional[int] = None

class VideoTaskResponse(BaseModel):
    id: str
    status: str
    progress: float
    output_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class VideoGenerationResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None 