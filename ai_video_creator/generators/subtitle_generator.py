"""
Subtitle Generation Module
"""

import os
from typing import Optional
import ffmpeg
import stable_whisper


class SubtitleGenerator:
    """
    A class to generate subtitles from video files and add them to videos.
    """

    def __init__(self, model_size: str = "medium"):
        """
        Initialize the SubtitleGenerator class.

        :param model_size: Size of the Whisper model to use (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self._model = None

    def _load_model(self):
        """Load the Whisper model if not already loaded."""
        if self._model is None:
            self._model = stable_whisper.load_model(self.model_size)
        return self._model

    def _format_timestamp(self, seconds: float) -> str:
        """
        Convert seconds to 'HH:MM:SS,mmm' format.

        :param seconds: Time in seconds
        :return: Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    def generate_srt_file(
        self, video_path: str, output_srt_path: Optional[str] = None
    ) -> str:
        """
        Generate an SRT file from the audio track of a video.

        :param video_path: Path to the input video file
        :param output_srt_path: Path for the output SRT file (optional)
        :return: Path to the generated SRT file
        """
        if output_srt_path is None:
            video_path_split = video_path.split(".")
            output_srt_path = f"{video_path_split[0]}.srt"

        model = self._load_model()
        result = model.transcribe(video_path)
        stable_whisper.result_to_srt_vtt(result=result, filepath=output_srt_path)

        return output_srt_path

    def add_subtitles_to_video(
        self, video_path: str, srt_path: str, output_video_path: Optional[str] = None
    ) -> str:
        """
        Add subtitles to a video file.

        :param video_path: Path to the input video file
        :param srt_path: Path to the SRT subtitle file
        :param output_video_path: Path for the output video file (optional)
        :return: Path to the output video with subtitles
        """
        if output_video_path is None:
            video_path_split = video_path.split(".")
            output_video_path = f"{video_path_split[0]}_subtitled.{video_path_split[1]}"

        (
            ffmpeg.input(video_path)
            .output(
                output_video_path,
                vf=f"subtitles={srt_path}",
                **{
                    "c:v": "libx264",
                    "preset": "fast",
                    "crf": "23",
                    "c:a": "aac",
                    "movflags": "+faststart",
                    "pix_fmt": "yuv420p",
                },
            )
            .overwrite_output()
            .run()
        )

        return output_video_path

    def generate_and_add_subtitles(
        self,
        video_path: str,
        output_video_path: Optional[str] = None,
        cleanup_srt: bool = True,
    ) -> tuple[str, str]:
        """
        Generate subtitles and add them to the video in one step.

        :param video_path: Path to the input video file
        :param output_video_path: Path for the output video file (optional)
        :param cleanup_srt: Whether to delete the SRT file after adding to video
        :return: Tuple of (output_video_path, srt_path)
        """
        # Generate SRT file
        srt_path = self.generate_srt_file(video_path)

        # Add subtitles to video
        if output_video_path is None:
            video_path_split = video_path.split(".")
            output_video_path = f"{video_path_split[0]}_subtitled.{video_path_split[1]}"

        final_video_path = self.add_subtitles_to_video(
            video_path, srt_path, output_video_path
        )

        # Cleanup SRT file if requested
        if cleanup_srt and os.path.exists(srt_path):
            os.remove(srt_path)
            srt_path = None

        return final_video_path, srt_path
