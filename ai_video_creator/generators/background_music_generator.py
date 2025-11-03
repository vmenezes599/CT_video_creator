"""
Audio Generation Module
"""

import random
import tempfile
import requests

from zipfile import ZipFile
from pathlib import Path
from abc import ABC, abstractmethod

from ai_video_creator.environment_variables import TTM_SERVER_URL

from typing_extensions import override


class BackgroundMusicRecipeBase:
    """Base class for audio recipes."""

    prompt: str
    recipe_type = "BackgroundMusicRecipeBase"

    def __init__(
        self,
        prompt: str,
        recipe_type: str,
    ):
        """Initialize BackgroundMusicRecipeBase with a name."""
        self.prompt = prompt
        self.recipe_type = recipe_type


class IBackgroundMusicGenerator(ABC):
    """
    An interface for audio generation classes.
    """

    @abstractmethod
    def text_to_music(self, recipe: "MusicGenRecipe", output_folder: Path) -> Path:
        """
        Generate music from text prompt and save it to the specified folder.

        :param recipe: The MusicGenRecipe containing prompt and generation parameters.
        :param output_folder: The folder to save the generated music file.
        :return: Path to the first generated music file.
        """


class MusicGenGenerator(IBackgroundMusicGenerator):
    """
    A class to generate music from text prompts using MusicGen.
    """

    MAXIMUM_GENERATION_TIME = 60 * 5  # 5 minutes
    DEFAULT_VIDEO_DURATION_SECONDS = 30  # seconds

    def __init__(self):
        """
        Initialize the MusicGenGenerator class.
        """
        self.ttm_endpoint = f"{TTM_SERVER_URL}/ttm"

    @override
    def text_to_music(self, recipe: "MusicGenRecipe", output_folder: Path) -> Path:
        """
        Generate music from text prompt and save it to the specified folder.

        Returns path to the first generated music file from the ZIP.
        """
        if not output_folder.exists() or not output_folder.is_dir():
            raise ValueError(f"Output folder does not exist or is not a directory: {output_folder}")

        data = {"prompt": recipe.prompt, "seed": recipe.seed, "seconds": self.DEFAULT_VIDEO_DURATION_SECONDS}

        response = requests.post(
            self.ttm_endpoint,
            data=data,
            stream=True,
            timeout=self.MAXIMUM_GENERATION_TIME,
        )

        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(suffix=".zip", prefix="musicgen_") as temp_zip:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_zip.write(chunk)
                temp_zip.flush()
                temp_zip_path = Path(temp_zip.name)

                extracted_files = []
                with ZipFile(temp_zip_path, "r") as zipf:
                    extracted_files = zipf.namelist()
                    zipf.extractall(output_folder)

                print(f"Music files extracted to {output_folder}")
            return Path(output_folder) / extracted_files[0]
        else:
            error_msg = f"Error: {response.status_code} - {response.text}"
            print(error_msg)
            raise RuntimeError(error_msg)


class MusicGenRecipe(BackgroundMusicRecipeBase):
    """Music generation recipe for creating music from text prompts."""

    GENERATOR_TYPE = MusicGenGenerator

    mood: str
    seed: int
    recipe_type = "MusicGenRecipeType"

    def __init__(self, prompt: str, mood: str, seed: int | None = None):
        """
        Initialize MusicGenRecipe with music generation parameters.

        Args:
            prompt: Text prompt for music generation
            seed: Random seed for reproducibility (auto-generated if None)
        """
        super().__init__(prompt, recipe_type=self.recipe_type)
        self.mood = mood
        self.seed = random.randint(0, 2**31 - 1) if seed is None else seed

    def __eq__(self, other) -> bool:
        """
        Compare two MusicGenRecipe instances for equality based on their values.

        Args:
            other: Another object to compare with

        Returns:
            True if recipes have the same prompt, mood, and seed, False otherwise
        """
        if not isinstance(other, MusicGenRecipe):
            return False
        return self.prompt == other.prompt and self.mood == other.mood and self.seed == other.seed

    def to_dict(self) -> dict:
        """
        Convert MusicGenRecipe to dictionary.

        Returns:
            Dictionary representation of the MusicGenRecipe
        """
        return {
            "prompt": self.prompt,
            "mood": self.mood,
            "seed": self.seed,
            "recipe_type": self.recipe_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MusicGenRecipe":
        """
        Create MusicGenRecipe from dictionary.

        Args:
            data: Dictionary containing MusicGenRecipe data

        Returns:
            MusicGenRecipe instance

        Raises:
            KeyError: If required keys are missing from data
            ValueError: If data format is invalid
        """
        # Validate required keys
        required_keys = ["prompt", "mood", "seed", "recipe_type"]
        missing_fields = set(required_keys) - data.keys()
        for field in missing_fields:
            raise KeyError(f"Missing required key: {field}")

        if not isinstance(data["prompt"], str):
            raise ValueError("prompt must be a string")
        if not isinstance(data["mood"], str):
            raise ValueError("mood must be a string")
        if not isinstance(data["seed"], int):
            raise ValueError("seed must be an integer")
        if not isinstance(data["recipe_type"], str):
            raise ValueError("recipe_type must be a string")

        if data["recipe_type"] != cls.recipe_type:
            raise ValueError(f"Invalid recipe_type: {data['recipe_type']}")

        return cls(
            prompt=data["prompt"],
            mood=data["mood"],
            seed=data["seed"],
        )
