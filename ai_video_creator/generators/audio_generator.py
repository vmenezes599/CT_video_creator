"""
Audio Generation Module
"""

import random
from abc import ABC, abstractmethod
from pathlib import Path
import requests

from ai_video_creator.environment_variables import COMFYUI_OUTPUT_FOLDER, TTS_SERVER_URL

from typing_extensions import override


class AudioRecipeBase:
    """Base class for audio recipes."""

    prompt: str
    recipe_type = "AudioRecipeBase"

    def __init__(
        self,
        prompt: str,
        recipe_type: str,
    ):
        """Initialize AudioRecipeBase with a name."""
        self.prompt = prompt
        self.recipe_type = recipe_type


class IAudioGenerator(ABC):
    """
    An interface for audio generation classes.
    """

    @abstractmethod
    def text_to_speech(self, text_list: list[str], output_file_path: Path) -> Path:
        """
        Convert the given text to audio and save it to the specified file.

        :param text: The text to convert to audio.
        :param output_path: The path to save the generated audio file.
        """

    @abstractmethod
    def clone_text_to_speech(self, recipe: AudioRecipeBase, output_file_path: Path) -> Path:
        """
        Convert the given text to audio and save it to the specified file.

        :param text: The text to convert to audio.
        :param output_path: The path to save the generated audio file.
        """

    @abstractmethod
    def play(self, text: str) -> None:
        """
        Play the given text as audio.

        :param text: The text to play as audio.
        """

    def get_output_directory(self) -> str:
        """
        Get the output directory for generated audio files.

        :return: The output directory path.
        """
        return COMFYUI_OUTPUT_FOLDER


class ZonosTTSAudioGenerator(IAudioGenerator):
    """
    A class to generate audio from text using Zonos TTS.
    """

    MAXIMUM_GENERATION_TIME = 60 * 30  # 30 minutes

    def __init__(self):
        """
        Initialize the ZonosTTSAudioGenerator class.
        """
        self.tts_endpoint = f"{TTS_SERVER_URL}/tts"

    @override
    def text_to_speech(self, text_list: list[str], output_file_path: Path) -> Path:
        """
        Convert the given text to audio and save it to the specified file.
        """
        raise NotImplementedError("Zonos TTS only supports voice cloning.")

    @override
    def clone_text_to_speech(self, recipe: "ZonosTTSRecipe", output_file_path: Path) -> Path:
        """
        Clone the voice from the given recipe and save it to the specified file.
        """
        data = {
            "text": recipe.prompt,
            "seed": recipe.seed,
        }

        with open(recipe.clone_voice_path, "rb") as audio_file:
            files = {"reference_audio_file": audio_file}

            response = requests.post(
                self.tts_endpoint,
                data=data,
                files=files,
                stream=True,
                timeout=self.MAXIMUM_GENERATION_TIME,
            )

            if response.status_code == 200:
                with open(output_file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return Path(output_file_path)  # Return the saved file path
            else:
                error_msg = f"Error: {response.status_code} - {response.text}"
                print(error_msg)
                raise RuntimeError(error_msg)

    @override
    def play(self, text: str) -> None:
        """
        Play the given text as audio.

        :param text: The text to play as audio.
        """
        raise NotImplementedError("Playing audio directly is not implemented in ElevenLabsAudioGenerator.")


class ZonosTTSRecipe(AudioRecipeBase):
    """Audio recipe for creating audio from text."""

    GENERATOR_TYPE = ZonosTTSAudioGenerator

    recipe_type = "ZonosTTSRecipeType"
    clone_voice_path = ""
    seed = 0

    def __init__(self, prompt: str, clone_voice_path: str, seed: int | None = None):
        """
        Initialize AudioRecipe with audio data.

        Args:
            audio_path: Path to the audio file
        """
        super().__init__(prompt, recipe_type=self.recipe_type)
        self.clone_voice_path = clone_voice_path
        self.seed = random.randint(0, 2**31 - 1) if seed is None else seed

    def to_dict(self) -> dict:
        """
        Convert AudioRecipe to dictionary.

        Returns:
            Dictionary representation of the AudioRecipe
        """
        return {
            "prompt": self.prompt,
            "clone_voice_path": self.clone_voice_path,
            "recipe_type": self.recipe_type,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AudioRecipe":  # pyright: ignore[reportUndefinedVariable]
        """
        Create AudioRecipe from dictionary.

        Args:
            data: Dictionary containing AudioRecipe data

        Returns:
            AudioRecipe  instance

        Raises:
            KeyError: If required keys are missing from data
            ValueError: If data format is invalid
        """
        # Validate required keys
        required_keys = ["prompt", "clone_voice_path", "recipe_type"]
        missing_fields = set(required_keys) - data.keys()
        for field in missing_fields:
            raise KeyError(f"Missing required key: {field}")

        if not isinstance(data["prompt"], str):
            raise ValueError("prompt must be a string")
        if not isinstance(data["clone_voice_path"], str):
            raise ValueError("clone_voice_path must be a string")
        if not isinstance(data["recipe_type"], str):
            raise ValueError("recipe_type must be a string")

        if data["recipe_type"] != cls.recipe_type:
            raise ValueError(f"Invalid recipe_type: {data['recipe_type']}")

        return cls(
            prompt=data["prompt"],
            clone_voice_path=data["clone_voice_path"],
            seed=data.get("seed", None),
        )
