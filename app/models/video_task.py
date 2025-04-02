from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class VideoTask(Base):
    __tablename__ = "video_tasks"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, processing, done, error
    progress = Column(Float, nullable=False, default=0.0)
    background_url = Column(String, nullable=False)  # URL for background audio track
    media_list = Column(JSON, nullable=False)  # List of video URLs
    duration = Column(Integer, nullable=True)  # Target duration in seconds (optional)
    output_url = Column(String, nullable=True)  # URL of the generated video
    error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    user = relationship("User", back_populates="tasks")

    class Config:
        orm_mode = True

    def __repr__(self):
        return f"<VideoTask(id={self.id}, status={self.status})>" 