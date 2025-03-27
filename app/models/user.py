from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    api_key = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    monthly_quota = Column(Integer, default=100)  # Number of requests allowed per month
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    tasks = relationship("VideoTask", back_populates="user") 