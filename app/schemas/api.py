from typing import List, Optional
from pydantic import BaseModel, EmailStr, HttpUrl, conint, Field
from datetime import datetime

# Auth Schemas
class CreateUserRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address", example="user@example.com")
    monthly_quota: Optional[int] = Field(100, description="Monthly video generation quota", example=100)

class UserResponse(BaseModel):
    id: str = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    api_key: str = Field(..., description="API key for authentication")
    monthly_quota: int = Field(..., description="Monthly video generation quota")

    class Config:
        from_attributes = True

# Video Generation Schemas
class VideoGenerationData(BaseModel):
    background_url: HttpUrl = Field(
        ..., 
        description="URL to the background music file",
        example="https://example.com/background.mp3"
    )
    media_list: List[HttpUrl] = Field(
        ..., 
        description="List of video URLs to be combined",
        example=["https://example.com/video1.mp4", "https://example.com/video2.mp4"]
    )
    duration: Optional[conint(gt=0)] = Field(
        None, 
        description="Optional duration in seconds for the final video",
        example=60
    )

class VideoGenerationRequest(BaseModel):
    type: str = Field(
        "LoopVideo", 
        description="Type of video to generate",
        example="LoopVideo"
    )
    data: VideoGenerationData

class VideoTaskResponse(BaseModel):
    id: str = Field(..., description="Task ID")
    user_id: str = Field(..., description="User ID who created the task")
    status: str = Field(..., description="Task status (pending, processing, done, error)")
    progress: float = Field(..., description="Progress percentage (0.0 to 1.0)")
    output_url: Optional[str] = Field(None, description="URL to the generated video")
    error: Optional[str] = Field(None, description="Error message if task failed")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True

class GenerationResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: dict = Field(..., description="Response data containing video ID")

class ProgressResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    data: dict = Field(
        ..., 
        description="Progress data containing status, URL, and progress percentage",
        example={
            "status": "processing",
            "url": None,
            "progress": 0.45
        }
    )

# Error Responses
class ErrorResponse(BaseModel):
    success: bool = Field(False, description="Operation status")
    message: str = Field(..., description="Error message")
    errors: Optional[List[str]] = Field(None, description="List of validation errors") 