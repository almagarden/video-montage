import os
import uuid
from typing import List, Optional
from moviepy.editor import VideoFileClip, CompositeVideoClip, clips_array, AudioFileClip
from moviepy.video.fx.resize import resize
from sqlalchemy.orm import Session
from app.models.video_task import VideoTask
from app.utils.download import download_file
from app.core.config import settings

class VideoGenerationService:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, user_id: str, background_url: str, media_list: List[str], duration: Optional[int] = None) -> VideoTask:
        """Create a new video generation task"""
        task = VideoTask(
            id=str(uuid.uuid4()),
            user_id=user_id,
            status="pending",
            background_url=background_url,  # Now used for audio track
            media_list=media_list,
            duration=duration
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_task_progress(self, task_id: str, progress: float, status: str = None, error: str = None, output_url: str = None):
        """Update task progress and status"""
        task = self.db.query(VideoTask).filter(VideoTask.id == task_id).first()
        if task:
            task.progress = progress
            if status:
                task.status = status
            if error:
                task.error_message = error
            if output_url:
                task.output_url = output_url
            self.db.commit()
            self.db.refresh(task)

    async def generate_video(self, task_id: str):
        """Generate video montage with background audio"""
        try:
            task = self.db.query(VideoTask).filter(VideoTask.id == task_id).first()
            if not task:
                return

            self.update_task_progress(task_id, 0.1, "processing")

            # Download background audio
            audio_path = download_file(task.background_url, task_id)
            if not audio_path:
                raise Exception("Failed to download background audio")

            # Download media files
            media_paths = []
            for url in task.media_list:
                path = download_file(url, task_id)
                if path:
                    media_paths.append(path)

            if not media_paths:
                raise Exception("Failed to download any media files")

            self.update_task_progress(task_id, 0.3)

            # Load background audio
            background_audio = AudioFileClip(audio_path)
            
            # Load and process media clips
            media_clips = []
            total_duration = 0
            
            for path in media_paths[:-1]:  # Process all clips except the last one
                clip = VideoFileClip(path).without_audio()  # Remove original audio
                total_duration += clip.duration
                media_clips.append(clip)
            
            # Handle the last clip specially for duration requirements
            last_clip = VideoFileClip(media_paths[-1]).without_audio()
            
            if task.duration:
                remaining_duration = task.duration - total_duration
                if remaining_duration > 0:
                    # Need to loop the last clip
                    loops_needed = int(remaining_duration / last_clip.duration) + 1
                    last_clip = last_clip.loop(n=loops_needed)
                    last_clip = last_clip.subclip(0, remaining_duration)
                else:
                    # Need to cut all clips proportionally
                    scale_factor = task.duration / (total_duration + last_clip.duration)
                    media_clips = [clip.subclip(0, clip.duration * scale_factor) for clip in media_clips]
                    last_clip = last_clip.subclip(0, last_clip.duration * scale_factor)
            
            media_clips.append(last_clip)
            final_duration = task.duration or (total_duration + last_clip.duration)

            self.update_task_progress(task_id, 0.5)

            # Calculate grid layout
            n_clips = len(media_clips)
            grid_size = 2  # 2x2 grid
            while grid_size * grid_size < n_clips:
                grid_size += 1

            # Resize clips to fit grid
            target_size = (1920 // grid_size, 1080 // grid_size)  # Assuming 1080p output
            resized_clips = [resize(clip, target_size) for clip in media_clips]

            # Pad with None if needed
            while len(resized_clips) < grid_size * grid_size:
                resized_clips.append(None)

            # Create grid layout
            grid = []
            for i in range(0, len(resized_clips), grid_size):
                row = resized_clips[i:i + grid_size]
                grid.append(row)

            self.update_task_progress(task_id, 0.7)

            # Create composite video
            grid_clip = clips_array(grid)
            
            # Trim or loop background audio to match video duration
            if background_audio.duration < final_duration:
                background_audio = background_audio.loop(duration=final_duration)
            else:
                background_audio = background_audio.subclip(0, final_duration)

            # Create final composite with background audio
            final_clip = CompositeVideoClip([grid_clip]).set_audio(background_audio)

            # Generate output path
            output_path = os.path.join(settings.STORAGE_DIR, task_id, "output.mp4")
            final_clip.write_videofile(output_path, 
                                     codec='libx264', 
                                     audio_codec='aac',
                                     threads=4,
                                     fps=24)

            # Clean up clips
            background_audio.close()
            for clip in media_clips:
                if clip:
                    clip.close()

            # Update task as completed
            output_url = f"/storage/{task_id}/output.mp4"
            self.update_task_progress(task_id, 1.0, "done", output_url=output_url)

        except Exception as e:
            self.update_task_progress(task_id, 0, "error", error=str(e))
            raise

    def get_task(self, task_id: str) -> Optional[VideoTask]:
        """Get task by ID"""
        return self.db.query(VideoTask).filter(VideoTask.id == task_id).first() 