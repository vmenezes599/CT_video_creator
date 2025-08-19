"""Effect base class for media effects."""

from pathlib import Path
from abc import ABC, abstractmethod


class EffectBase(ABC):
    """
    Abstract base class for all media effects.

    This interface defines the contract that all effects must implement.
    """

    effect_type: str = "EffectBaseType"

    def __init__(self, effect_type: str):
        """
        Initialize the effect with a specific type.

        Args:
            effect_type: The type of the effect (e.g., "audio", "video").
        """
        self.effect_type = effect_type

    @abstractmethod
    def apply(self, media_file_path: Path, **kwargs) -> Path:
        """
        Apply the effect to the media data.

        Args:
            media_file_path: The path to the input media file
            **kwargs: Additional parameters specific to the effect

        Returns:
            The path to the processed media file with the effect applied

        Raises:
            NotImplementedError: If not implemented by subclass
        """

    @abstractmethod
    def to_dict(self):
        """Convert the effect to a JSON-serializable format."""
        raise NotImplementedError

    @abstractmethod
    def from_dict(self, json_data: dict):
        """Initialize the effect from a JSON-serialized format."""
        raise NotImplementedError
