import pytest
from app.services.auth import AuthService

def test_create_user(client):
    """Test user creation endpoint"""
    response = client.post(
        "/api/v1/auth/users",
        json={
            "email": "newuser@example.com",
            "monthly_quota": 100
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "api_key" in data
    assert data["monthly_quota"] == 100

def test_create_user_duplicate_email(client, test_user):
    """Test user creation with duplicate email"""
    response = client.post(
        "/api/v1/auth/users",
        json={
            "email": test_user.email,
            "monthly_quota": 100
        }
    )
    
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_regenerate_api_key(client, test_user, test_headers):
    """Test API key regeneration"""
    old_api_key = test_user.api_key
    
    response = client.post(
        f"/api/v1/auth/users/{test_user.id}/regenerate-key",
        headers=test_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["api_key"] != old_api_key

def test_regenerate_api_key_unauthorized(client, test_user):
    """Test API key regeneration without authentication"""
    response = client.post(
        f"/api/v1/auth/users/{test_user.id}/regenerate-key"
    )
    
    assert response.status_code == 401
    assert "API key is required" in response.json()["detail"]

def test_regenerate_api_key_wrong_user(client, test_user, test_headers):
    """Test API key regeneration for different user"""
    wrong_user_id = "wrong-id"
    
    response = client.post(
        f"/api/v1/auth/users/{wrong_user_id}/regenerate-key",
        headers=test_headers
    )
    
    assert response.status_code == 403
    assert "You can only regenerate your own API key" in response.json()["detail"]

def test_invalid_api_key(client):
    """Test request with invalid API key"""
    headers = {"api-key": "invalid-key"}
    
    response = client.get(
        "/api/v1/video-generation/progress/123",
        headers=headers
    )
    
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]