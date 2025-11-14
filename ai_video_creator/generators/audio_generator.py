"""
Audio Generation Module
"""

import random
from abc import ABC, abstractmethod
from pathlib import Path
import time
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
        self.endpoint = f"{TTS_SERVER_URL}"
        self.tts_endpoint = f"{self.endpoint}/tts"

        self._wait_for_service_ready()

    def _wait_for_service_ready(self, check_interval: int = 5):
        """
        Wait until the Text-to-Music service is ready to accept requests.
        """
        max_tries = (5 * 60) / check_interval  # Wait up to 5 minutes
        tries = 0
        while tries < max_tries:
            try:
                response = requests.get(f"{self.endpoint}/health", timeout=10)
                if response.ok:
                    return
            except requests.RequestException:
                print("Waiting for Text-to-Music service to be ready...")
                time.sleep(check_interval)
            finally:
                tries += 1

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
            "happiness": recipe.happiness,
            "sadness": recipe.sadness,
            "disgust": recipe.disgust,
            "fear": recipe.fear,
            "surprise": recipe.surprise,
            "anger": recipe.anger,
            "other": recipe.other,
            "neutral": recipe.neutral,
            "expressiveness": recipe.expressiveness,
            "speaking_rate": recipe.speaking_rate,
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
    seed = None
    happiness = None
    sadness = None
    disgust = None
    fear = None
    surprise = None
    anger = None
    other = None
    neutral = None
    expressiveness = None
    speaking_rate = None

    def __init__(
        self,
        prompt: str,
        clone_voice_path: str,
        seed: int | None = None,
        happiness: float | None = None,
        sadness: float | None = None,
        disgust: float | None = None,
        fear: float | None = None,
        surprise: float | None = None,
        anger: float | None = None,
        other: float | None = None,
        neutral: float | None = None,
        expressiveness: float | None = None,
        speaking_rate: float | None = None,
    ):
        """
        Initialize AudioRecipe with audio data.

        Args:
            audio_path: Path to the audio file
        """
        super().__init__(prompt, recipe_type=self.recipe_type)
        self.clone_voice_path = clone_voice_path
        self.seed = random.randint(0, 2**31 - 1) if seed is None else seed
        self.happiness = 0.3077 if happiness is None else happiness
        self.sadness = 0.0256 if sadness is None else sadness
        self.disgust = 0.0256 if disgust is None else disgust
        self.fear = 0.0256 if fear is None else fear
        self.surprise = 0.0256 if surprise is None else surprise
        self.anger = 0.0256 if anger is None else anger
        self.other = 0.2564 if other is None else other
        self.neutral = 0.3077 if neutral is None else neutral
        self.expressiveness = 0.1 if expressiveness is None else expressiveness
        self.speaking_rate = 0.375 if speaking_rate is None else speaking_rate

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
            "happiness": self.happiness,
            "sadness": self.sadness,
            "disgust": self.disgust,
            "fear": self.fear,
            "surprise": self.surprise,
            "anger": self.anger,
            "other": self.other,
            "neutral": self.neutral,
            "expressiveness": self.expressiveness,
            "speaking_rate": self.speaking_rate,
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
            happiness=data.get("happiness", None),
            sadness=data.get("sadness", None),
            disgust=data.get("disgust", None),
            fear=data.get("fear", None),
            surprise=data.get("surprise", None),
            anger=data.get("anger", None),
            other=data.get("other", None),
            neutral=data.get("neutral", None),
            expressiveness=data.get("expressiveness", None),
            speaking_rate=data.get("speaking_rate", None),
        )
