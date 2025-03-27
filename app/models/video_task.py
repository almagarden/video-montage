from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class VideoTask(Base):
    __tablename__ = "video_tasks"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    status = Column(String, default="pending")  # pending, processing, done, error
    progress = Column(Float, default=0.0)
    background_url = Column(String)
    media_list = Column(JSON)
    duration = Column(Integer, nullable=True)
    output_url = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    user = relationship("User", back_populates="tasks") 