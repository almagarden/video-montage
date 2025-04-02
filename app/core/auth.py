from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)

async def get_api_key(
    api_key: str = Depends(API_KEY_HEADER),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate API key and return associated user
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required"
        )
    
    user = db.query(User).filter(User.api_key == api_key).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return user

def verify_api_key(api_key: str, db: Session) -> Optional[User]:
    """
    Verify API key without FastAPI dependency
    """
    if not api_key:
        return None
    
    return db.query(User).filter(User.api_key == api_key).first() 