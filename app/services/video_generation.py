import os
import uuid
from typing import List, Optional
from moviepy.editor import VideoFileClip, CompositeVideoClip, clips_array, AudioFileClip, concatenate_videoclips
from moviepy.video.fx.resize import resize
from sqlalchemy.orm import Session
from app.models.video_task import VideoTask
from app.utils.download import download_file
from app.core.config import settings

class VideoGenerationService:
    def __init__(self, db: Session):
        self.db = db
        self.storage_path = "storage/videos"
        os.makedirs(self.storage_path, exist_ok=True)

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
            audio_path = download_file(task.background_url, self.storage_path)
            if not audio_path:
                raise Exception("Failed to download background audio")

            # Download media files
            media_paths = []
            for url in task.media_list:
                path = download_file(url, self.storage_path)
                if path:
                    media_paths.append(path)

            if not media_paths:
                raise Exception("Failed to download any media files")

            self.update_task_progress(task_id, 0.3)

            # Load background audio
            background_audio = AudioFileClip(audio_path)
            
            # Load and process media clips
            video_clips = []
            total_duration = 0
            
            for path in media_paths:
                clip = VideoFileClip(path).without_audio()  # Remove original audio
                total_duration += clip.duration
                video_clips.append(clip)
            
            # Handle duration
            target_duration = task.duration if task.duration else total_duration
            total_original_duration = total_duration

            if target_duration < total_original_duration:
                # If target duration is shorter, adjust clip durations proportionally
                scale_factor = target_duration / total_original_duration
                video_clips = [clip.subclip(0, clip.duration * scale_factor) for clip in video_clips]
            elif target_duration > total_original_duration:
                # If target duration is longer, loop the last clip
                remaining_duration = target_duration - total_original_duration
                last_clip = video_clips[-1]
                loops_needed = int(remaining_duration / last_clip.duration)
                remainder = remaining_duration % last_clip.duration
                
                # Add full loops
                for _ in range(loops_needed):
                    video_clips.append(last_clip)
                
                # Add partial loop if needed
                if remainder > 0:
                    video_clips.append(last_clip.subclip(0, remainder))

            self.update_task_progress(task_id, 0.5)

            # Get the aspect ratio from the first video
            if not video_clips:
                raise Exception("No valid video clips provided")
            
            base_width, base_height = video_clips[0].size
            aspect_ratio = base_width / base_height

            # Resize all subsequent clips to match the first video's dimensions
            for i in range(1, len(video_clips)):
                clip = video_clips[i]
                current_ratio = clip.size[0] / clip.size[1]
                
                if current_ratio > aspect_ratio:
                    # Video is wider than target ratio, fit to height
                    new_width = int(base_height * current_ratio)
                    resized = clip.resize(height=base_height)
                    # Crop to match target width
                    x_center = resized.size[0] // 2
                    video_clips[i] = resized.crop(
                        x1=x_center - (base_width // 2),
                        y1=0,
                        x2=x_center + (base_width // 2),
                        y2=base_height
                    )
                else:
                    # Video is taller than target ratio, fit to width
                    new_height = int(base_width / current_ratio)
                    resized = clip.resize(width=base_width)
                    # Crop to match target height
                    y_center = resized.size[1] // 2
                    video_clips[i] = resized.crop(
                        x1=0,
                        y1=y_center - (base_height // 2),
                        x2=base_width,
                        y2=y_center + (base_height // 2)
                    )

            # Concatenate all clips
            final_video = concatenate_videoclips(video_clips)

            # Prepare audio
            if background_audio.duration < final_video.duration:
                # Loop audio if needed
                background_audio = background_audio.loop(duration=final_video.duration)
            else:
                # Trim audio if needed
                background_audio = background_audio.subclip(0, final_video.duration)

            # Set audio to final video
            final_video = final_video.set_audio(background_audio)

            # Save the final video
            output_path = os.path.join(self.storage_path, f"output_{task_id}.mp4")
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=os.path.join(self.storage_path, f"temp_audio_{task_id}.m4a"),
                remove_temp=True
            )

            # Update task with output URL
            task.output_url = f"/storage/videos/output_{task_id}.mp4"
            task.status = "done"
            task.progress = 1.0
            self.db.commit()

            # Clean up clips
            background_audio.close()
            for clip in video_clips:
                if clip:
                    clip.close()
            final_video.close()

        except Exception as e:
            self.update_task_progress(task_id, 0, "error", error=str(e))
            raise

    def get_task(self, task_id: str) -> Optional[VideoTask]:
        """Get task by ID"""
        return self.db.query(VideoTask).filter(VideoTask.id == task_id).first() 