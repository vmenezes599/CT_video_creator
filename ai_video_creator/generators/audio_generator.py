"""
Audio Generation Module
"""

import os
import random
from abc import ABC, abstractmethod
from pathlib import Path

# ZonosTTSAudioGenerator
import requests
from ai_video_creator.environment_variables import TTS_SERVER_URL, DEFAULT_ASSETS_FOLDER

# Pyttsx3AudioGenerator
import pyttsx3

# ElevenLabsAudioGenerator
from elevenlabs import save
from elevenlabs.client import ElevenLabs
from typing_extensions import override

# SparkTTSComfyUIAudioGenerator
from ai_video_creator.environment_variables import COMFYUI_OUTPUT_FOLDER
from ai_video_creator.utils import get_next_available_filename

from .environment_variables import ELEVENLABS_API_KEY


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
    def clone_text_to_speech(
        self, recipe: AudioRecipeBase, output_file_path: Path
    ) -> Path:
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


class Pyttsx3AudioGenerator(IAudioGenerator):
    """
    A class to generate audio from text using pyttsx3.
    """

    def __init__(self):
        """
        Initialize the AudioGenerator class and configure the pyttsx3 engine.
        """
        self.engine = pyttsx3.init()
        self.engine.setProperty(
            "voice",
            "HKEY_LOCAL_MACHINE/SOFTWARE/Microsoft/Speech/Voices/Tokens/TTS_MS_EN-GB_HAZEL_11.0",
        )
        self.engine.setProperty("rate", 150)  # Set speech rate
        self.engine.setProperty("volume", 1.0)  # Set volume (0.0 to 1.0)

    @override
    def text_to_speech(self, text_list: list[str], output_file_name: str) -> list[str]:
        """
        Convert the given text to audio and save it to the specified file.

        :param text: The text to convert to audio.
        :param output_path: The path to save the generated audio file.
        """
        output_file_name = os.path.splitext(output_file_name)[0] + ".mp3"

        output_list: list[str] = []
        for text in text_list:
            name = get_next_available_filename(
                f"{COMFYUI_OUTPUT_FOLDER}/{output_file_name}"
            )
            self.engine.save_to_file(text, name)
            self.engine.runAndWait()
            output_list.append(name)

        return output_list

    @override
    def play(self, text: str) -> None:
        """
        Play the given text as audio.

        :param text: The text to play as audio.
        """
        self.engine.say(text)
        self.engine.runAndWait()

    def set_property(self, args, kwargs):
        """
        Set properties for the pyttsx3 engine.

        :param args: The property name.
        :param kwargs: The property value.
        """
        self.engine.setProperty(args, kwargs)

    def get_property(self, args):
        """
        Get properties from the pyttsx3 engine.

        :param args: The property name.
        :return: The property value.
        """
        return self.engine.getProperty(args)


class ElevenLabsAudioGenerator(IAudioGenerator):
    """
    A class to generate audio from text using ElevenLabs API.
    """

    def __init__(self):
        """
        Initialize the ElevenLabsAudioGenerator class with the provided API key.
        """
        self.client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    @override
    def text_to_speech(self, text_list: list[str], output_file_name: str) -> list[str]:
        """
        Convert the given text to audio and save it to the specified file.
        """
        # Extract the file name without the extension
        output_file_name = os.path.splitext(output_file_name)[0] + ".mp3"

        os.makedirs(
            COMFYUI_OUTPUT_FOLDER, exist_ok=True
        )  # Ensure the output directory exists

        output_list: list[str] = []
        for text in text_list:
            # Generate a unique filename for each audio file
            name = get_next_available_filename(
                f"{COMFYUI_OUTPUT_FOLDER}/{output_file_name}"
            )

            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )

            save(audio, name)
            output_list.append(name)

        return output_list

    @override
    def play(self, text: str) -> None:
        """
        Play the given text as audio.

        :param text: The text to play as audio.
        """
        raise NotImplementedError(
            "Playing audio directly is not implemented in ElevenLabsAudioGenerator."
        )


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
    def clone_text_to_speech(
        self, recipe: "ZonosTTSRecipe", output_file_path: Path
    ) -> Path:
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
        raise NotImplementedError(
            "Playing audio directly is not implemented in ElevenLabsAudioGenerator."
        )


class ZonosTTSRecipe(AudioRecipeBase):
    """Audio recipe for creating audio from text."""

    GENERATOR = ZonosTTSAudioGenerator

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
        self.seed = random.randint(0, 2**64 - 1) if seed is None else seed

    def to_dict(self) -> dict:
        """
        Convert AudioRecipe to dictionary.

        Returns:
            Dictionary representation of the AudioRecipe
        """

        voices_path = Path(DEFAULT_ASSETS_FOLDER) / "voices"
        available_voices = [str(f) for f in voices_path.glob("*.mp3")]

        return {
            "prompt": self.prompt,
            "clone_voice_path": self.clone_voice_path,
            "available_voices": available_voices,
            "recipe_type": self.recipe_type,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(
        cls, data: dict
    ) -> "AudioRecipe":  # pyright: ignore[reportUndefinedVariable]
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
