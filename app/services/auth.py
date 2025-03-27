import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from app.models.user import User
from app.db.base import get_db
from app.core.config import settings

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def generate_api_key(self) -> str:
        """Generate a new API key"""
        return secrets.token_urlsafe(32)

    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key"""
        return self.db.query(User).filter(User.api_key == api_key).first()

    def create_user(self, email: str, monthly_quota: int = 100) -> User:
        """Create a new user with API key"""
        api_key = self.generate_api_key()
        user = User(
            id=secrets.token_urlsafe(16),
            email=email,
            api_key=api_key,
            monthly_quota=monthly_quota
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def validate_api_key(self, api_key: str) -> User:
        """Validate API key and return user"""
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="API key is required"
            )

        user = self.get_user_by_api_key(api_key)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="User account is disabled"
            )

        return user

    def check_rate_limit(self, user: User):
        """Check if user has exceeded rate limits"""
        # Get the first day of current month
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Count tasks created this month
        monthly_tasks = self.db.query(User)\
            .join(User.tasks)\
            .filter(User.id == user.id)\
            .filter(User.created_at >= start_of_month)\
            .count()

        if monthly_tasks >= user.monthly_quota:
            raise HTTPException(
                status_code=429,
                detail="Monthly API quota exceeded"
            )

        # Check rate limit per minute
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        recent_tasks = self.db.query(User)\
            .join(User.tasks)\
            .filter(User.id == user.id)\
            .filter(User.created_at >= one_minute_ago)\
            .count()

        if recent_tasks >= settings.RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {settings.RATE_LIMIT_PER_MINUTE} requests per minute."
            )

def get_current_user(
    api_key: str,
    db: Session = Depends(get_db)
) -> User:
    """Dependency for getting the current user from API key"""
    auth_service = AuthService(db)
    return auth_service.validate_api_key(api_key) 