"""
A class that extends the duration of an audio clip by a specified number of seconds.
"""

from pathlib import Path
from typing_extensions import override

import ffmpeg
from logging_utils import logger

from ai_video_creator.helpers.ffmpeg_helpers import get_audio_duration, run_ffmpeg_trace
from ai_video_creator.media_effects.effect_base import EffectBase


class AudioExtender(EffectBase):
    """A class that extends the duration of an audio clip by a specified number of seconds."""

    effect_type: str = "AudioExtenderType"

    def __init__(self, seconds_to_extend: float):
        """
        Initialize the audio extender effect.

        Args:
            seconds_to_extend: The number of seconds to extend the audio clip.
        """
        super().__init__(effect_type=self.effect_type)
        self.seconds_to_extend = seconds_to_extend

    def extend_audio_to_duration(
        self, input_path: Path, output_path: Path, extra_time: float
    ):
        """
        Extend the audio clip to the target duration.
        """
        current_duration = get_audio_duration(input_path)
        target_duration = current_duration + extra_time

        cmd = (
            ffmpeg.input(str(input_path))
            .filter("apad")
            .output(
                str(output_path),
                t=target_duration,
                acodec="libmp3lame",
                format="mp3",
            )
            .overwrite_output()
            .compile()
        )

        run_ffmpeg_trace(cmd)

        return output_path

    @override
    def apply(self, media_file_path: Path, **kwargs) -> Path:
        """Apply the audio extender effect."""
        logger.info(
            f"Applying AudioExtender to {media_file_path.name} of {self.seconds_to_extend} seconds"
        )
        output_path = media_file_path.with_stem(f"{media_file_path.stem}_extended")

        result = self.extend_audio_to_duration(
            input_path=media_file_path,
            output_path=output_path,
            extra_time=self.seconds_to_extend,
        )

        logger.info(f"Audio extended successfully: {output_path.name}")
        return result

    @override
    def to_dict(self):
        """Convert the effect to a JSON-serializable format."""
        return {"type": self.effect_type, "seconds_to_extend": self.seconds_to_extend}

    @override
    def from_dict(self, json_data: dict):
        """
        Initialize the effect from a JSON-serialized format.
        """

        required_fields = ["seconds_to_extend"]
        missing_fields = set(required_fields) - json_data.keys()
        for field in missing_fields:
            raise KeyError(f"Missing required key: {field}")

        self.seconds_to_extend = json_data["seconds_to_extend"]
