from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.video import VideoGenerationRequest, VideoTaskResponse
from app.services.video_generation import VideoGenerationService
from app.core.auth import get_api_key

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