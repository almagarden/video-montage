from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.api import (
    VideoGenerationRequest,
    VideoTaskResponse,
    GenerationResponse,
    ProgressResponse,
    ErrorResponse,
    VideoGenerationData
)
from app.services.video_generation import VideoGenerationService
from app.core.auth import get_api_key
from app.api.deps import verify_api_key, check_rate_limit, verify_quota
from app.services.video import VideoService

router = APIRouter()

@router.post("/generate", response_model=VideoTaskResponse)
async def generate_video(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    user_id: str = Depends(get_api_key)
):
    """
    Generate a video montage with background audio.
    - Takes a list of video URLs and a background audio URL
    - Videos will be arranged sequentially
    - All videos will be resized to match the first video's aspect ratio
    - If duration is specified:
        - If shorter than total video length: videos will be scaled proportionally
        - If longer than total video length: last video will loop to fill the time
    """
    service = VideoGenerationService(db)
    
    # Create task
    task = service.create_task(
        user_id=user_id,
        background_url=request.background_url,
        media_list=request.media_list,
        duration=request.duration
    )
    
    # Start video generation in background
    background_tasks.add_task(service.generate_video, task.id)
    
    return task

@router.get("/progress/{task_id}", response_model=VideoTaskResponse)
async def get_progress(
    task_id: str,
    db: Session = Depends(deps.get_db),
    user_id: str = Depends(get_api_key)
):
    """
    Get the progress of a video generation task.
    Returns:
    - Task status (pending, processing, done, error)
    - Progress percentage (0.0 to 1.0)
    - Output URL when complete
    - Error message if failed
    """
    service = VideoGenerationService(db)
    task = service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
    
    return task

@router.post(
    "/loop-video",
    response_model=GenerationResponse,
    responses={
        200: {
            "description": "Successfully started video generation",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Video generation started",
                        "data": {"id": "video_123"}
                    }
                }
            }
        },
        401: {
            "description": "Invalid API key",
            "model": ErrorResponse
        },
        429: {
            "description": "Rate limit or quota exceeded",
            "model": ErrorResponse
        }
    },
    summary="Generate Loop Video",
    description="Start a new video generation task that combines multiple videos with background music"
)
async def generate_loop_video(
    request: VideoGenerationRequest,
    api_key: str = Depends(verify_api_key),
    _: None = Depends(check_rate_limit),
    __: None = Depends(verify_quota)
):
    """
    Generate a loop video by combining multiple videos with background music.

    - **type**: Type of video to generate (currently only 'LoopVideo' is supported)
    - **data.background_url**: URL to the background music file
    - **data.media_list**: List of video URLs to be combined
    - **data.duration**: Optional duration in seconds for the final video

    The API will return a video ID that can be used to check the generation progress.
    """
    video_service = VideoService()
    video_id = await video_service.start_generation(request.data)
    
    return {
        "success": True,
        "message": "Video generation started",
        "data": {"id": video_id}
    }

@router.get(
    "/progress/{video_id}",
    response_model=ProgressResponse,
    responses={
        200: {
            "description": "Successfully retrieved progress",
            "content": {
                "application/json": {
                    "examples": {
                        "processing": {
                            "value": {
                                "success": True,
                                "data": {
                                    "status": "processing",
                                    "url": None,
                                    "progress": 0.45
                                }
                            }
                        },
                        "completed": {
                            "value": {
                                "success": True,
                                "data": {
                                    "status": "done",
                                    "url": "https://example.com/videos/final_123.mp4",
                                    "progress": 1.0
                                }
                            }
                        }
                    }
                }
            }
        },
        401: {
            "description": "Invalid API key",
            "model": ErrorResponse
        },
        404: {
            "description": "Video not found",
            "model": ErrorResponse
        }
    },
    summary="Check Generation Progress",
    description="Check the progress of a video generation task"
)
async def check_progress(
    video_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Check the progress of a video generation task.

    - **video_id**: The ID of the video generation task
    
    Returns:
    - **status**: Current status of the generation ('pending', 'processing', 'done')
    - **url**: URL to the final video (only available when status is 'done')
    - **progress**: Progress value between 0 and 1
    """
    video_service = VideoService()
    progress = await video_service.get_progress(video_id)
    
    return {
        "success": True,
        "data": progress
    } 