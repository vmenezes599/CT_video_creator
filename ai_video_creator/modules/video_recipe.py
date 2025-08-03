"""
Video executor for create_video command.
"""

import json
from pathlib import Path

from ai_video_creator.prompt import Prompt

from ai_video_creator.generators import (
    SparkTTSRecipe,
    FluxImageRecipe,
)

from .video_recipe_paths import VideoRecipePaths


class VideoRecipeDefaultSettings:
    """Default settings for video recipe."""

    NARRATOR_VOICE = "default-assets/voices/voice_002.mp3"
    BACKGROUND_MUSIC = "default-assets/background_music.mp3"


class VideoRecipe:
    """Video recipe for creating videos from stories."""

    def __init__(self, recipe_path: Path):
        """Initialize VideoRecipe with default settings."""
        self.recipe_path = recipe_path

        self.narrator_data = []
        self.image_data = []

        self.__load_from_file(recipe_path)

    def add_narrator_data(self, narrator_data) -> None:
        """Add narrator data to the recipe."""
        self.narrator_data.append(narrator_data)
        self.save_current_state()

    def add_image_data(self, image_data) -> None:
        """Add image data to the recipe."""
        self.image_data.append(image_data)
        self.save_current_state()

    def __load_from_file(self, file_path: Path) -> None:
        """Load video recipe from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.narrator_data = [
                    self._create_recipe_from_dict(item)
                    for item in data["narrator_data"]
                ]
                self.image_data = [
                    self._create_recipe_from_dict(item) for item in data["image_data"]
                ]

        except FileNotFoundError:
            pass
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading video recipe: {e}")

    def _create_recipe_from_dict(self, data: dict):
        """Create the appropriate recipe object from dictionary data based on recipe_type."""
        recipe_type = data.get("recipe_type")

        if recipe_type == "SparkTTSRecipeType":
            return SparkTTSRecipe.from_dict(data)
        elif recipe_type == "FluxImageRecipeType":
            return FluxImageRecipe.from_dict(data)
        else:
            raise ValueError(f"Unknown recipe_type: {recipe_type}")

    def clean(self) -> None:
        """Clean the current recipe data."""
        self.narrator_data = []
        self.image_data = []

    def to_dict(self) -> dict:
        """Convert VideoRecipe to dictionary.

        Returns:
            Dictionary representation of the VideoRecipe
        """
        return {
            "narrator_data": [item.to_dict() for item in self.narrator_data],
            "image_data": [item.to_dict() for item in self.image_data],
        }

    def save_current_state(self) -> None:
        """Save the current state of the video recipe to a file."""
        try:
            with open(self.recipe_path, "w", encoding="utf-8") as file:
                json.dump(self.to_dict(), file, indent=4)
        except IOError as e:
            print(f"Error saving video recipe: {e}")


class VideoRecipeBuilder:
    """Video recipe for creating videos from stories."""

    def __init__(self, story_folder: Path, chapter_prompt_index: int):
        """Initialize VideoRecipe with recipe data.

        Args:
            narrators: List of narrator text strings
            visual_descriptions: List of visual description strings
            narrator_audio: Audio voice setting for narrator
            background_music: Background music setting
            seeds: List of seeds for each generation (None elements use default behavior)
        """
        # Initialize path management
        self.__paths = VideoRecipePaths(story_folder, chapter_prompt_index)
        self.__chapter_prompt_path = self.__paths.chapter_prompt_path

        # Load video prompt
        self.__video_prompt = Prompt.load_from_json(self.__chapter_prompt_path)
        self._recipe = None

    def _verify_recipe_against_prompt(self) -> None:
        """Verify the recipe against the prompt to ensure all required data is present."""
        if (
            not self._recipe.narrator_data
            or not self._recipe.image_data
            or len(self._recipe.image_data) != len(self.__video_prompt)
            or len(self._recipe.narrator_data) != len(self.__video_prompt)
        ):
            return False
        return True

    def _create_flux_image_recipe(self, seed: int | None = None) -> None:
        """Create video recipe from story folder and chapter prompt index."""
        # Load chapter prompt

        for prompt in self.__video_prompt:

            recipe = FluxImageRecipe(prompt=prompt.visual_prompt, seed=seed)

            self._recipe.add_image_data(recipe)

    def _create_spark_tts_narrator_recipe(self) -> None:
        """Create Spark TTS narrator recipe."""
        # Load chapter prompt
        for prompt in self.__video_prompt:
            recipe = SparkTTSRecipe(
                prompt=prompt.narrator,
                clone_voice_path=VideoRecipeDefaultSettings.NARRATOR_VOICE,
            )
            self._recipe.add_narrator_data(recipe)

    def create_video_recipe(self) -> None:
        """Create video recipe from story folder and chapter prompt index."""
        self._recipe = VideoRecipe(self.__paths.recipe_file)

        if not self._verify_recipe_against_prompt():
            self._recipe.clean()
            self._create_flux_image_recipe()
            self._create_spark_tts_narrator_recipe()
