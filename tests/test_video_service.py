import pytest
from unittest.mock import patch, MagicMock
from app.services.video_generation import VideoGenerationService
from app.models.video_task import VideoTask

@pytest.fixture
def video_service(db_session):
    return VideoGenerationService(db_session)

def test_create_task(video_service, test_user):
    """Test task creation"""
    task = video_service.create_task(
        user_id=test_user.id,
        background_url="https://example.com/background.mp4",
        media_list=["https://example.com/video1.mp4"],
        duration=30
    )
    
    assert isinstance(task, VideoTask)
    assert task.user_id == test_user.id
    assert task.status == "pending"
    assert task.progress == 0.0
    assert task.background_url == "https://example.com/background.mp4"
    assert task.media_list == ["https://example.com/video1.mp4"]
    assert task.duration == 30

def test_update_task_progress(video_service, test_user):
    """Test task progress update"""
    task = video_service.create_task(
        user_id=test_user.id,
        background_url="https://example.com/background.mp4",
        media_list=["https://example.com/video1.mp4"]
    )
    
    video_service.update_task_progress(
        task_id=task.id,
        progress=0.5,
        status="processing"
    )
    
    updated_task = video_service.get_task(task.id)
    assert updated_task.progress == 0.5
    assert updated_task.status == "processing"

@patch('app.utils.download.download_file')
@patch('moviepy.editor.VideoFileClip')
@patch('moviepy.editor.CompositeVideoClip')
def test_generate_video(mock_composite, mock_video_clip, mock_download, video_service, test_user, tmp_path):
    """Test video generation process"""
    # Mock the video file download
    mock_download.return_value = str(tmp_path / "test_video.mp4")
    
    # Mock VideoFileClip
    mock_clip = MagicMock()
    mock_clip.duration = 30
    mock_clip.size = (1920, 1080)
    mock_video_clip.return_value = mock_clip
    
    # Mock CompositeVideoClip
    mock_composite_clip = MagicMock()
    mock_composite.return_value = mock_composite_clip
    
    task = video_service.create_task(
        user_id=test_user.id,
        background_url="https://example.com/background.mp4",
        media_list=["https://example.com/video1.mp4"],
        duration=30
    )
    
    # Run video generation
    video_service.generate_video(task.id)
    
    # Check final task state
    final_task = video_service.get_task(task.id)
    assert final_task.status == "done"
    assert final_task.progress == 1.0
    assert final_task.output_url is not None

@patch('app.utils.download.download_file')
def test_generate_video_download_error(mock_download, video_service, test_user):
    """Test video generation with download error"""
    # Mock download failure
    mock_download.return_value = None
    
    task = video_service.create_task(
        user_id=test_user.id,
        background_url="https://example.com/background.mp4",
        media_list=["https://example.com/video1.mp4"]
    )
    
    # Run video generation
    with pytest.raises(Exception) as exc_info:
        video_service.generate_video(task.id)
    
    assert "Failed to download background video" in str(exc_info.value)
    
    # Check task error state
    error_task = video_service.get_task(task.id)
    assert error_task.status == "error"
    assert error_task.error_message is not None 