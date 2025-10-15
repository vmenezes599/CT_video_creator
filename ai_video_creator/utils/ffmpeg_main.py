"""Using functionalities from ffmpeg_wrapper to create a video segment from a sub-video and audio, freezing the last frame."""

from pathlib import Path
from ai_video_creator.utils import (
    create_video_segment_from_sub_video_and_audio_freeze_last_frame,
    concatenate_videos_with_fade_in_out,
)


def create_video_logo():
    """Main function to create a video segment from a sub-video and audio, freezing the last frame."""
    video_path = Path(
        "/home/vitor/projects/DATABASES/AI-Video-Default-Assets/logo/logo_video.mp4"
    )
    audio_path = Path(
        "/home/vitor/projects/DATABASES/AI-Video-Default-Assets/logo/logo_audio.mp3"
    )
    output_path = Path(
        "/home/vitor/projects/DATABASES/AI-Video-Default-Assets/logo/combined.mp4"
    )

    create_video_segment_from_sub_video_and_audio_freeze_last_frame(
        sub_video_path=video_path,
        audio_path=audio_path,
        output_path=output_path,
    )


def main():
    """Main function to test video concatenation with fade in and out effects."""
    video_1_path = Path(
        "/home/vitor/projects/DATABASES/AI-Video-Default-Assets/logo/combined.mp4"
    )
    video_2_path = Path(
        "/home/vitor/projects/DATABASES/STORY_PRODUCTION_DATABASE/database/users/Rafael/stories/Heracles The Weight of a Curse/video/chapter_001/output_raw.mp4"
    )
    output_path = Path(
        "/home/vitor/projects/DATABASES/AI-Video-Default-Assets/logo/test.mp4"
    )
    concatenate_videos_with_fade_in_out([video_1_path, video_2_path], output_path)


if __name__ == "__main__":
    main()
