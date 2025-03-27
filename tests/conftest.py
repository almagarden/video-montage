import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base, get_db
from app.services.auth import AuthService
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = "postgresql://postgres:postgres@db:5432/test_video_montage"

# Create test database engine
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def test_db():
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop test database tables
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db):
    # Create a new database session for a test
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    # Rollback the transaction and close the session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    # Override the get_db dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    # Create a test user with API key
    auth_service = AuthService(db_session)
    user = auth_service.create_user(
        email="test@example.com",
        monthly_quota=100
    )
    return user

@pytest.fixture
def test_headers(test_user):
    # Create headers with API key for authenticated requests
    return {"api-key": test_user.api_key}

@pytest.fixture
def test_video_urls():
    # Sample video URLs for testing
    return {
        "background_url": "https://example.com/background.mp4",
        "media_urls": [
            "https://example.com/video1.mp4",
            "https://example.com/video2.mp4"
        ]
    }

@pytest.fixture(autouse=True)
def test_storage_dir(tmp_path):
    # Create a temporary storage directory for test files
    os.environ["STORAGE_DIR"] = str(tmp_path)
    return tmp_path 