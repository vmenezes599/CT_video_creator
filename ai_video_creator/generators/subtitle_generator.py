"""
Subtitle Generation Module
"""

from pathlib import Path

import whisper
from logging_utils import logger


class SubtitleGenerator:
    """
    A class to generate subtitles from video files and add them to videos.
    """

    def __init__(self, model_size: str = "turbo"):
        """
        Initialize the SubtitleGenerator class.

        :param model_size: Size of the Whisper model to use (tiny, base, small, medium, large)
        """
        logger.info(f"Initializing SubtitleGenerator with model size: {model_size}")
        self.model_size = model_size
        self._model = None

    def _load_model(self):
        """Load the Whisper model if not already loaded."""
        if self._model is None:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self._model = whisper.load_model(self.model_size)
            logger.info("Whisper model loaded successfully")
        else:
            logger.debug("Whisper model already loaded, reusing existing model")
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
        logger.info(
            f"Writing SRT file: {output_path.name} with {len(segments)} segments"
        )

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

        logger.info(f"SRT file written successfully: {output_path.name}")

    def generate_subtitles_from_audio(self, video_path: Path) -> Path:
        """
        Generate an SRT file from the audio track of a video.

        :param video_path: Path to the input video file
        :param output_srt_path: Path for the output SRT file (optional)
        :return: Path to the generated SRT file
        """
        logger.info(f"Generating SRT file for video: {video_path.name}")
        output_srt_path = video_path.with_suffix(".srt")
        logger.info(
            f"SRT file doesn't exist, transcribing audio from: {video_path.name}"
        )
        model = self._load_model()

        logger.info("Starting audio transcription with Whisper")
        result = model.transcribe(str(video_path), word_timestamps=True)
        logger.info(f"Transcription completed with {len(result['segments'])} segments")

        self.write_srt(segments=result["segments"], output_path=output_srt_path)

        return output_srt_path
