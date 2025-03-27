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
        background_url="https://example.com/background.mp3",
        media_list=["https://example.com/video1.mp4"],
        duration=30
    )
    
    assert isinstance(task, VideoTask)
    assert task.user_id == test_user.id
    assert task.status == "pending"
    assert task.progress == 0.0
    assert task.background_url == "https://example.com/background.mp3"
    assert task.media_list == ["https://example.com/video1.mp4"]
    assert task.duration == 30

def test_update_task_progress(video_service, test_user):
    """Test task progress update"""
    task = video_service.create_task(
        user_id=test_user.id,
        background_url="https://example.com/background.mp3",
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
@patch('moviepy.editor.AudioFileClip')
@patch('moviepy.editor.CompositeVideoClip')
def test_generate_video_with_duration_shorter(
    mock_composite, mock_audio, mock_video_clip, mock_download,
    video_service, test_user, tmp_path
):
    """Test video generation when specified duration is shorter than total video length"""
    # Mock the file downloads
    mock_download.side_effect = lambda url, _: str(tmp_path / "test_file.mp4")
    
    # Mock video clips
    mock_clips = []
    for duration in [10, 15, 20]:  # Total duration: 45 seconds
        clip = MagicMock()
        clip.duration = duration
        clip.size = (1920, 1080)
        clip.without_audio.return_value = clip
        mock_clips.append(clip)
    
    mock_video_clip.side_effect = mock_clips
    
    # Mock audio clip
    mock_audio_clip = MagicMock()
    mock_audio_clip.duration = 60  # 1-minute audio
    mock_audio.return_value = mock_audio_clip
    
    # Mock composite clip
    mock_composite_clip = MagicMock()
    mock_composite.return_value = mock_composite_clip
    
    # Create and run task with 30-second duration
    task = video_service.create_task(
        user_id=test_user.id,
        background_url="https://example.com/background.mp3",
        media_list=[
            "https://example.com/video1.mp4",
            "https://example.com/video2.mp4",
            "https://example.com/video3.mp4"
        ],
        duration=30
    )
    
    video_service.generate_video(task.id)
    
    # Verify final task state
    final_task = video_service.get_task(task.id)
    assert final_task.status == "done"
    assert final_task.progress == 1.0
    assert final_task.output_url is not None
    
    # Verify audio was trimmed to match video duration
    mock_audio_clip.subclip.assert_called_with(0, 30)

@patch('app.utils.download.download_file')
@patch('moviepy.editor.VideoFileClip')
@patch('moviepy.editor.AudioFileClip')
@patch('moviepy.editor.CompositeVideoClip')
def test_generate_video_with_duration_longer(
    mock_composite, mock_audio, mock_video_clip, mock_download,
    video_service, test_user, tmp_path
):
    """Test video generation when specified duration is longer than total video length"""
    # Mock the file downloads
    mock_download.side_effect = lambda url, _: str(tmp_path / "test_file.mp4")
    
    # Mock video clips
    mock_clips = []
    for duration in [10, 15]:  # Total duration: 25 seconds
        clip = MagicMock()
        clip.duration = duration
        clip.size = (1920, 1080)
        clip.without_audio.return_value = clip
        mock_clips.append(clip)
    
    mock_video_clip.side_effect = mock_clips
    
    # Mock audio clip
    mock_audio_clip = MagicMock()
    mock_audio_clip.duration = 20  # 20-second audio
    mock_audio.return_value = mock_audio_clip
    
    # Mock composite clip
    mock_composite_clip = MagicMock()
    mock_composite.return_value = mock_composite_clip
    
    # Create and run task with 40-second duration
    task = video_service.create_task(
        user_id=test_user.id,
        background_url="https://example.com/background.mp3",
        media_list=[
            "https://example.com/video1.mp4",
            "https://example.com/video2.mp4"
        ],
        duration=40
    )
    
    video_service.generate_video(task.id)
    
    # Verify final task state
    final_task = video_service.get_task(task.id)
    assert final_task.status == "done"
    assert final_task.progress == 1.0
    assert final_task.output_url is not None
    
    # Verify audio was looped to match video duration
    mock_audio_clip.loop.assert_called_with(duration=40)

@patch('app.utils.download.download_file')
def test_generate_video_audio_download_error(mock_download, video_service, test_user):
    """Test video generation with audio download error"""
    # Mock audio download failure
    mock_download.return_value = None
    
    task = video_service.create_task(
        user_id=test_user.id,
        background_url="https://example.com/background.mp3",
        media_list=["https://example.com/video1.mp4"]
    )
    
    # Run video generation
    with pytest.raises(Exception) as exc_info:
        video_service.generate_video(task.id)
    
    assert "Failed to download background audio" in str(exc_info.value)
    
    # Check task error state
    error_task = video_service.get_task(task.id)
    assert error_task.status == "error"
    assert error_task.error_message is not None 