"""Using functionalities from ffmpeg_wrapper to create a video segment from a sub-video and audio, freezing the last frame."""

from pathlib import Path
from ct_video_creator.utils import (
    create_video_segment_from_sub_video_and_audio_freeze_last_frame,
    concatenate_videos_with_fade_in_out,
    blit_overlay_video_onto_main_video,
)


def create_video_logo():
    """Main function to create a video segment from a sub-video and audio, freezing the last frame."""
    video_path = Path(
        "/home/vitor/projects/DATABASES/CT_default_assets/logo/logo_video.mp4"
    )
    audio_path = Path(
        "/home/vitor/projects/DATABASES/CT_default_assets/logo/logo_audio.mp3"
    )
    output_path = Path(
        "/home/vitor/projects/DATABASES/CT_default_assets/logo/combined.mp4"
    )

    create_video_segment_from_sub_video_and_audio_freeze_last_frame(
        sub_video_path=video_path,
        audio_path=audio_path,
        output_path=output_path,
    )


def run_concatenate_videos_with_fade_in_out():
    """Main function to test video concatenation with fade in and out effects."""
    video_1_path = Path(
        "/home/vitor/projects/DATABASES/CT_default_assets/logo/combined.mp4"
    )
    video_2_path = Path(
        "/home/vitor/projects/DATABASES/STORY_PRODUCTION_DATABASE/database/users/Rafael/stories/Heracles The Weight of a Curse/video/chapter_001/output_raw.mp4"
    )
    output_path = Path(
        "/home/vitor/projects/DATABASES/CT_default_assets/logo/test.mp4"
    )
    concatenate_videos_with_fade_in_out([video_1_path, video_2_path], output_path)


def run_blit_intro_video_onto_main_video():
    """Main function to test blitting an intro video onto a main video."""
    outro_video_path = Path(
        "/home/vitor/projects/DATABASES/CT_default_assets/videos/CTA_YOUTUBE_INGLES.mov"
    )
    main_video_path = Path(
        "/home/vitor/projects/DATABASES/STORY_PRODUCTION_DATABASE/database/users/Rafael/stories/Heracles The Weight of a Curse/video/chapter_001/output_raw.mp4"
    )
    output_path = Path(
        "/home/vitor/projects/DATABASES/CT_default_assets/logo/blitted_test.mp4"
    )
    blit_overlay_video_onto_main_video(outro_video_path, main_video_path, output_path)


def main():
    """Main function to run the desired video processing tasks."""

    # create_video_logo()
    # run_concatenate_videos_with_fade_in_out()
    run_blit_intro_video_onto_main_video()

    return 0


if __name__ == "__main__":
    main()
