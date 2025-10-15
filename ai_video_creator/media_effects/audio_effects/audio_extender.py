"""
A class that extends the duration of an audio clip by a specified number of seconds.
"""

from pathlib import Path
from typing_extensions import override

from logging_utils import logger

from ai_video_creator.utils import extend_audio_to_duration
from ai_video_creator.media_effects.effect_base import EffectBase


class AudioExtender(EffectBase):
    """A class that extends the duration of an audio clip by a specified number of seconds."""

    effect_type: str = "AudioExtenderType"

    def __init__(
        self,
        seconds_to_extend_front: float = 0.0,
        seconds_to_extend_back: float = 0.0,
    ):
        """
        Initialize the audio extender effect.

        Args:
            seconds_to_extend_front: The number of seconds to prepend (extend at the front).
            seconds_to_extend_back: The number of seconds to append (extend at the back).
        """
        super().__init__(effect_type=self.effect_type)
        self.__seconds_to_extend_front = seconds_to_extend_front
        self.__seconds_to_extend_back = seconds_to_extend_back

    @override
    def apply(self, media_file_path: Path, **kwargs) -> Path:
        """Apply the audio extender effect."""
        logger.info(
            f"Applying AudioExtender to {media_file_path.name} - "
            f"front: {self.__seconds_to_extend_front}s, back: {self.__seconds_to_extend_back}s"
        )
        output_path = media_file_path.with_stem(f"{media_file_path.stem}_extended")

        result = extend_audio_to_duration(
            input_path=media_file_path,
            output_path=output_path,
            extra_time_front=self.__seconds_to_extend_front,
            extra_time_back=self.__seconds_to_extend_back,
        )

        logger.info(f"Audio extended successfully: {output_path.name}")
        return result

    @override
    def to_dict(self):
        """Convert the effect to a JSON-serializable format."""
        return {
            "type": self.effect_type,
            "seconds_to_extend_front": self.__seconds_to_extend_front,
            "seconds_to_extend_back": self.__seconds_to_extend_back,
        }

    @override
    def from_dict(self, json_data: dict):
        """
        Initialize the effect from a JSON-serialized format.
        """

        required_fields = ["seconds_to_extend_front", "seconds_to_extend_back"]
        missing_fields = set(required_fields) - json_data.keys()
        for field in missing_fields:
            raise KeyError(f"Missing required key: {field}")

        self.__seconds_to_extend_front = json_data["seconds_to_extend_front"]
        self.__seconds_to_extend_back = json_data["seconds_to_extend_back"]
