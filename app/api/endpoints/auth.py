from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.db.base import get_db
from app.services.auth import AuthService
from typing import Optional

router = APIRouter()

class CreateUserRequest(BaseModel):
    email: EmailStr
    monthly_quota: Optional[int] = 100

class UserResponse(BaseModel):
    id: str
    email: str
    api_key: str
    monthly_quota: int

    class Config:
        from_attributes = True

@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new user and generate API key
    """
    auth_service = AuthService(db)
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    user = auth_service.create_user(
        email=request.email,
        monthly_quota=request.monthly_quota
    )
    
    return user

@router.post("/users/{user_id}/regenerate-key", response_model=UserResponse)
async def regenerate_api_key(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Regenerate API key for a user
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only regenerate your own API key"
        )
    
    auth_service = AuthService(db)
    current_user.api_key = auth_service.generate_api_key()
    db.commit()
    db.refresh(current_user)
    
    return current_user 