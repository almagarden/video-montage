from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch
from app.main import app
from app.core.auth import create_api_key

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def api_key(test_user):
    return create_api_key(test_user.id)

def test_generate_video_endpoint(client, api_key):
    """Test successful video generation request"""
    response = client.post(
        "/api/video-generation/generate",
        params={"api_key": api_key},
        json={
            "background_url": "https://example.com/background.mp3",
            "media_list": [
                "https://example.com/video1.mp4",
                "https://example.com/video2.mp4"
            ],
            "duration": 60
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"
    assert data["progress"] == 0.0

def test_generate_video_validation(client, api_key):
    """Test input validation for video generation"""
    # Test missing background URL
    response = client.post(
        "/api/video-generation/generate",
        params={"api_key": api_key},
        json={
            "media_list": ["https://example.com/video1.mp4"]
        }
    )
    assert response.status_code == 422
    
    # Test invalid URL format
    response = client.post(
        "/api/video-generation/generate",
        params={"api_key": api_key},
        json={
            "background_url": "not-a-url",
            "media_list": ["https://example.com/video1.mp4"]
        }
    )
    assert response.status_code == 422
    
    # Test empty media list
    response = client.post(
        "/api/video-generation/generate",
        params={"api_key": api_key},
        json={
            "background_url": "https://example.com/background.mp3",
            "media_list": []
        }
    )
    assert response.status_code == 422
    
    # Test negative duration
    response = client.post(
        "/api/video-generation/generate",
        params={"api_key": api_key},
        json={
            "background_url": "https://example.com/background.mp3",
            "media_list": ["https://example.com/video1.mp4"],
            "duration": -10
        }
    )
    assert response.status_code == 422

def test_generate_video_unauthorized(client):
    """Test authentication requirements"""
    # Test missing API key
    response = client.post(
        "/api/video-generation/generate",
        json={
            "background_url": "https://example.com/background.mp3",
            "media_list": ["https://example.com/video1.mp4"]
        }
    )
    assert response.status_code == 401
    
    # Test invalid API key
    response = client.post(
        "/api/video-generation/generate",
        params={"api_key": "invalid-key"},
        json={
            "background_url": "https://example.com/background.mp3",
            "media_list": ["https://example.com/video1.mp4"]
        }
    )
    assert response.status_code == 401

@patch('app.services.video_generation.VideoGenerationService.get_task')
def test_get_progress_endpoint(mock_get_task, client, api_key, test_user):
    """Test progress checking endpoint"""
    # Mock a task in progress
    mock_get_task.return_value = type('Task', (), {
        'id': 'test-task',
        'user_id': test_user.id,
        'status': 'processing',
        'progress': 0.5,
        'output_url': None,
        'error_message': None
    })
    
    response = client.get(
        "/api/video-generation/progress/test-task",
        params={"api_key": api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-task"
    assert data["status"] == "processing"
    assert data["progress"] == 0.5
    assert data["output_url"] is None
    
    # Mock a completed task
    mock_get_task.return_value = type('Task', (), {
        'id': 'test-task',
        'user_id': test_user.id,
        'status': 'done',
        'progress': 1.0,
        'output_url': '/storage/videos/output_test-task.mp4',
        'error_message': None
    })
    
    response = client.get(
        "/api/video-generation/progress/test-task",
        params={"api_key": api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "done"
    assert data["progress"] == 1.0
    assert data["output_url"] == '/storage/videos/output_test-task.mp4'

def test_get_progress_not_found(client, api_key):
    """Test progress endpoint with non-existent task"""
    response = client.get(
        "/api/video-generation/progress/non-existent-task",
        params={"api_key": api_key}
    )
    assert response.status_code == 404

@patch('app.services.video_generation.VideoGenerationService.get_task')
def test_get_progress_unauthorized(mock_get_task, client, api_key, test_user):
    """Test progress endpoint authorization"""
    # Mock a task owned by a different user
    mock_get_task.return_value = type('Task', (), {
        'id': 'test-task',
        'user_id': 'different-user',
        'status': 'processing',
        'progress': 0.5
    })
    
    response = client.get(
        "/api/video-generation/progress/test-task",
        params={"api_key": api_key}
    )
    assert response.status_code == 403 