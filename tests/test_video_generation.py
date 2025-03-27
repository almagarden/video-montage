import pytest
from unittest.mock import patch
from app.services.video_generation import VideoGenerationService

def test_generate_video(client, test_headers, test_video_urls):
    """Test video generation endpoint"""
    response = client.post(
        "/api/v1/video-generation/generate",
        headers=test_headers,
        json={
            "type": "LoopVideo",
            "data": {
                "background_url": test_video_urls["background_url"],
                "media_list": test_video_urls["media_urls"],
                "duration": 30
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "id" in data["data"]

def test_generate_video_invalid_type(client, test_headers, test_video_urls):
    """Test video generation with invalid type"""
    response = client.post(
        "/api/v1/video-generation/generate",
        headers=test_headers,
        json={
            "type": "InvalidType",
            "data": {
                "background_url": test_video_urls["background_url"],
                "media_list": test_video_urls["media_urls"],
                "duration": 30
            }
        }
    )
    
    assert response.status_code == 400
    assert "Unsupported video type" in response.json()["detail"]

def test_generate_video_rate_limit(client, test_headers, test_video_urls, db_session):
    """Test video generation rate limiting"""
    # Mock the rate limit check to simulate limit exceeded
    with patch.object(VideoGenerationService, 'check_rate_limit', side_effect=Exception("Rate limit exceeded")):
        response = client.post(
            "/api/v1/video-generation/generate",
            headers=test_headers,
            json={
                "type": "LoopVideo",
                "data": {
                    "background_url": test_video_urls["background_url"],
                    "media_list": test_video_urls["media_urls"],
                    "duration": 30
                }
            }
        )
        
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

def test_get_progress(client, test_headers, db_session):
    """Test progress endpoint"""
    # Create a test task
    service = VideoGenerationService(db_session)
    task = service.create_task(
        user_id="test-user",
        background_url="https://example.com/background.mp4",
        media_list=["https://example.com/video1.mp4"],
        duration=30
    )
    
    response = client.get(
        f"/api/v1/video-generation/progress/{task.id}",
        headers=test_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "status" in data["data"]
    assert "progress" in data["data"]

def test_get_progress_not_found(client, test_headers):
    """Test progress endpoint with non-existent task"""
    response = client.get(
        "/api/v1/video-generation/progress/non-existent-id",
        headers=test_headers
    )
    
    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]

def test_get_progress_unauthorized(client, test_headers, db_session):
    """Test progress endpoint with unauthorized access"""
    # Create a task for a different user
    service = VideoGenerationService(db_session)
    task = service.create_task(
        user_id="different-user",
        background_url="https://example.com/background.mp4",
        media_list=["https://example.com/video1.mp4"],
        duration=30
    )
    
    response = client.get(
        f"/api/v1/video-generation/progress/{task.id}",
        headers=test_headers
    )
    
    assert response.status_code == 403
    assert "You don't have permission to access this task" in response.json()["detail"] 