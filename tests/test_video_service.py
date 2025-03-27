import pytest
from unittest.mock import patch, MagicMock
from app.services.video_generation import VideoGenerationService
from app.models.video_task import VideoTask

@pytest.fixture
def video_service(db_session):
    return VideoGenerationService(db_session)

def test_create_task(video_service, test_user):
    """Test task creation with valid parameters"""
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
    """Test updating task progress"""
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
@patch('moviepy.editor.concatenate_videoclips')
def test_generate_video_basic(
    mock_concatenate, mock_audio, mock_video_clip, mock_download,
    video_service, test_user, tmp_path
):
    """Test basic video generation with sequential arrangement"""
    # Mock downloads
    mock_download.side_effect = lambda url, _: str(tmp_path / "test_file.mp4")
    
    # Mock video clips
    clip1 = MagicMock()
    clip1.duration = 10
    clip1.size = (1920, 1080)
    clip1.without_audio.return_value = clip1
    
    clip2 = MagicMock()
    clip2.duration = 15
    clip2.size = (1280, 720)
    clip2.without_audio.return_value = clip2
    clip2.resize.return_value = clip2
    clip2.crop.return_value = clip2
    
    mock_video_clip.side_effect = [clip1, clip2]
    
    # Mock audio
    mock_audio_clip = MagicMock()
    mock_audio_clip.duration = 30
    mock_audio.return_value = mock_audio_clip
    
    # Mock final video
    mock_final = MagicMock()
    mock_concatenate.return_value = mock_final
    
    # Create and run task
    task = video_service.create_task(
        user_id=test_user.id,
        background_url="https://example.com/background.mp3",
        media_list=[
            "https://example.com/video1.mp4",
            "https://example.com/video2.mp4"
        ]
    )
    
    video_service.generate_video(task.id)
    
    # Verify aspect ratio handling
    clip2.resize.assert_called_once()
    clip2.crop.assert_called_once()
    
    # Verify concatenation
    mock_concatenate.assert_called_once()
    
    # Verify final state
    final_task = video_service.get_task(task.id)
    assert final_task.status == "done"
    assert final_task.progress == 1.0
    assert final_task.output_url is not None

@patch('app.utils.download.download_file')
@patch('moviepy.editor.VideoFileClip')
@patch('moviepy.editor.AudioFileClip')
@patch('moviepy.editor.concatenate_videoclips')
def test_generate_video_with_shorter_duration(
    mock_concatenate, mock_audio, mock_video_clip, mock_download,
    video_service, test_user, tmp_path
):
    """Test video generation with duration shorter than total length"""
    # Mock downloads
    mock_download.side_effect = lambda url, _: str(tmp_path / "test_file.mp4")
    
    # Mock video clips
    clips = []
    for duration in [10, 15, 20]:  # Total: 45 seconds
        clip = MagicMock()
        clip.duration = duration
        clip.size = (1920, 1080)
        clip.without_audio.return_value = clip
        clip.subclip.return_value = clip
        clips.append(clip)
    
    mock_video_clip.side_effect = clips
    
    # Mock audio
    mock_audio_clip = MagicMock()
    mock_audio_clip.duration = 60
    mock_audio.return_value = mock_audio_clip
    
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
    
    # Verify clips were scaled
    for clip in clips:
        clip.subclip.assert_called_once()
    
    # Verify audio was trimmed
    mock_audio_clip.subclip.assert_called_with(0, 30)
    
    # Verify final state
    final_task = video_service.get_task(task.id)
    assert final_task.status == "done"
    assert final_task.progress == 1.0

@patch('app.utils.download.download_file')
@patch('moviepy.editor.VideoFileClip')
@patch('moviepy.editor.AudioFileClip')
@patch('moviepy.editor.concatenate_videoclips')
def test_generate_video_with_longer_duration(
    mock_concatenate, mock_audio, mock_video_clip, mock_download,
    video_service, test_user, tmp_path
):
    """Test video generation with duration longer than total length"""
    # Mock downloads
    mock_download.side_effect = lambda url, _: str(tmp_path / "test_file.mp4")
    
    # Mock video clips
    clips = []
    for duration in [10, 15]:  # Total: 25 seconds
        clip = MagicMock()
        clip.duration = duration
        clip.size = (1920, 1080)
        clip.without_audio.return_value = clip
        clips.append(clip)
    
    mock_video_clip.side_effect = clips
    
    # Mock audio
    mock_audio_clip = MagicMock()
    mock_audio_clip.duration = 20
    mock_audio.return_value = mock_audio_clip
    
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
    
    # Verify last clip was used for looping
    assert mock_concatenate.call_args[0][0][-1] == clips[-1]
    
    # Verify audio was looped
    mock_audio_clip.loop.assert_called_with(duration=40)
    
    # Verify final state
    final_task = video_service.get_task(task.id)
    assert final_task.status == "done"
    assert final_task.progress == 1.0

@patch('app.utils.download.download_file')
def test_generate_video_download_errors(mock_download, video_service, test_user):
    """Test error handling for download failures"""
    # Test audio download failure
    mock_download.return_value = None
    
    task = video_service.create_task(
        user_id=test_user.id,
        background_url="https://example.com/background.mp3",
        media_list=["https://example.com/video1.mp4"]
    )
    
    with pytest.raises(Exception) as exc_info:
        video_service.generate_video(task.id)
    
    assert "Failed to download background audio" in str(exc_info.value)
    
    error_task = video_service.get_task(task.id)
    assert error_task.status == "error"
    assert error_task.error_message is not None
    
    # Test video download failure
    mock_download.side_effect = lambda url, _: None if "video" in url else "audio.mp3"
    
    task = video_service.create_task(
        user_id=test_user.id,
        background_url="https://example.com/background.mp3",
        media_list=["https://example.com/video1.mp4"]
    )
    
    with pytest.raises(Exception) as exc_info:
        video_service.generate_video(task.id)
    
    assert "Failed to download video" in str(exc_info.value)
    
    error_task = video_service.get_task(task.id)
    assert error_task.status == "error"
    assert error_task.error_message is not None 