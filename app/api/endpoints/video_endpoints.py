from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.services.video_generation import VideoGenerationService
from app.services.auth import AuthService, get_current_user
from app.models.user import User
from app.schemas.video_schemas import (
    VideoGenerationRequest,
    VideoGenerationResponse,
    VideoTaskResponse
)

router = APIRouter()

@router.post("/generate", response_model=VideoGenerationResponse)
async def generate_video(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a new video generation task
    """
    if request.type != "LoopVideo":
        raise HTTPException(status_code=400, detail="Unsupported video type")

    # Check rate limits
    auth_service = AuthService(db)
    auth_service.check_rate_limit(current_user)

    service = VideoGenerationService(db)
    
    # Create task
    task = service.create_task(
        user_id=current_user.id,
        background_url=request.data["background_url"],
        media_list=request.data["media_list"],
        duration=request.data.get("duration")
    )

    # Start video generation in background
    background_tasks.add_task(service.generate_video, task.id)

    return VideoGenerationResponse(
        success=True,
        message="Video generation started",
        data={"id": task.id}
    )

@router.get("/progress/{task_id}", response_model=VideoGenerationResponse)
async def get_progress(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the progress of a video generation task
    """
    service = VideoGenerationService(db)
    task = service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify task ownership
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this task"
        )

    return VideoGenerationResponse(
        success=True,
        message="Task status retrieved",
        data={
            "status": task.status,
            "progress": task.progress,
            "url": task.output_url if task.status == "done" else None,
            "error": task.error_message if task.status == "error" else None
        }
    ) 