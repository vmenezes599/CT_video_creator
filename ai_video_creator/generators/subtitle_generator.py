"""
Subtitle Generation Module
"""

from pathlib import Path
import stable_whisper
from logging_utils import logger
from ai_video_creator.utils import SubtitleAlignment, SubtitlePosition


class SubtitleGenerator:
    """
    A class to generate subtitles from video files and add them to videos.
    """

    def __init__(self, model_size: str = "medium"):
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
            self._model = stable_whisper.load_model(self.model_size)
            logger.info("Whisper model loaded successfully")
        else:
            logger.debug("Whisper model already loaded, reusing existing model")
        return self._model

    def _unload_model(self):
        """Unload the Whisper model to free up resources."""
        if self._model is not None:
            logger.info("Unloading Whisper model to free up resources")
            del self._model
            self._model = None
            logger.info("Whisper model unloaded successfully")
        else:
            logger.debug("No Whisper model loaded to unload")

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
        logger.info(f"Writing SRT file: {output_path.name} with {len(segments)} segments")

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

    def generate_subtitles_from_audio(
        self,
        video_path: Path,
        word_level: bool = False,
        segment_level: bool = True,
        font_size: int = 24,
        margin: int = 50,
        karaoke: bool = True,
        position: SubtitlePosition = SubtitlePosition.BOTTOM,
        alignment: SubtitleAlignment = SubtitleAlignment.CENTER,
    ) -> tuple[Path, Path]:
        """
        Generate an ASS subtitle file from the audio track of a video.

        :param video_path: Path to the input video file
        :param word_level: Whether to use word-level timestamps
        :param segment_level: Whether to use segment-level timestamps
        :param font_size: Font size for subtitles
        :param position: Vertical position (TOP, CENTER, BOTTOM)
        :param margin: Vertical margin in pixels
        :param alignment: Horizontal alignment (LEFT, CENTER, RIGHT, JUSTIFIED)
        :return: tuple[Path, Path] Paths to the generated ASS and SRT files
        """
        # Calculate ASS alignment value based on vertical position and horizontal alignment
        # ASS Alignment values (numpad layout):
        # 1=bottom-left, 2=bottom-center, 3=bottom-right
        # 4=middle-left, 5=middle-center, 6=middle-right
        # 7=top-left,    8=top-center,    9=top-right

        # Map position to row (1=bottom, 2=middle, 3=top)
        position_row = {
            SubtitlePosition.BOTTOM: 0,
            SubtitlePosition.CENTER: 3,
            SubtitlePosition.TOP: 6,
        }

        # Map alignment to column (0=left, 1=center, 2=right)
        alignment_col = {
            SubtitleAlignment.LEFT: 0,
            SubtitleAlignment.CENTER: 1,
            SubtitleAlignment.RIGHT: 2,
        }

        # Calculate final ASS alignment (1-9)
        ass_alignment = position_row[position] + alignment_col[alignment] + 1

        logger.info(f"Generating ASS subtitle file for video: {video_path.name}")
        logger.debug(
            f"Subtitle settings: position={position.value}, margin={margin}, "
            f"font_size={font_size}, alignment={alignment.value}, ass_alignment={ass_alignment}"
        )
        logger.info(f"Transcribing audio from: {video_path.name}")
        model = self._load_model()

        logger.info("Starting audio transcription with Whisper")
        result = model.transcribe(str(video_path), vad=True)
        logger.info("Transcription completed.")

        # Generate ASS with custom styling parameters
        output_ass_path = video_path.with_suffix(".ass")
        result.to_ass(
            str(output_ass_path),
            word_level=word_level,
            segment_level=segment_level,
            font_size=font_size,
            Alignment=ass_alignment,
            MarginV=margin,
            karaoke=karaoke,
        )

        # Generate SRT file
        output_srt_path = video_path.with_suffix(".srt")
        result.to_srt_vtt(str(output_srt_path), word_level=word_level, segment_level=segment_level)

        self._unload_model()

        return output_ass_path, output_srt_path
