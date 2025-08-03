"""
Subtitle Generation Module
"""

from pathlib import Path
import ffmpeg
import whisper


class SubtitleGenerator:
    """
    A class to generate subtitles from video files and add them to videos.
    """

    def __init__(self, model_size: str = "turbo"):
        """
        Initialize the SubtitleGenerator class.

        :param model_size: Size of the Whisper model to use (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self._model = None

    def _load_model(self):
        """Load the Whisper model if not already loaded."""
        if self._model is None:
            self._model = whisper.load_model(self.model_size)
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

    def write_srt(self, segments, output_path: Path):
        """Write subtitles to an SRT file."""

        def format_time(t):
            hours = int(t // 3600)
            minutes = int((t % 3600) // 60)
            seconds = int(t % 60)
            milliseconds = int((t - int(t)) * 1000)
            return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

        with open(output_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, 1):
                start = format_time(segment["start"])
                end = format_time(segment["end"])
                text = segment["text"].strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    def generate_srt_file(self, video_path: Path) -> Path:
        """
        Generate an SRT file from the audio track of a video.

        :param video_path: Path to the input video file
        :param output_srt_path: Path for the output SRT file (optional)
        :return: Path to the generated SRT file
        """
        output_srt_path = video_path.with_suffix(".srt")
        if not output_srt_path.exists():
            model = self._load_model()

            result = model.transcribe(str(video_path), word_timestamps=True)
            self.write_srt(segments=result["segments"], output_path=output_srt_path)

        return output_srt_path

    def add_subtitles_to_video(
        self, video_path: Path, srt_path: Path, output_video_path: Path
    ) -> Path:
        """
        Add subtitles to a video file.

        :param video_path: Path to the input video file
        :param srt_path: Path to the SRT subtitle file
        :param output_video_path: Path for the output video file (optional)
        :return: Path to the output video with subtitles
        """
        (
            ffmpeg.input(str(video_path))
            .output(
                str(output_video_path),
                vf=f"subtitles={str(srt_path)}",
                **{
                    "c:v": "h264_nvenc",
                    "preset": "p5",
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
        video_path: Path,
        cleanup_srt: bool = True,
    ) -> tuple[Path, Path]:
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
        output_video_path = video_path.with_stem(f"{video_path.stem}_subtitled")

        final_video_path = self.add_subtitles_to_video(
            video_path, srt_path, output_video_path
        )

        # Cleanup SRT file if requested
        if cleanup_srt and srt_path.exists():
            srt_path.unlink()
            srt_path = None

        return final_video_path, srt_path
