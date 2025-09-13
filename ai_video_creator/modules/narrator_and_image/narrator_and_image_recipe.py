"""
Video executor for create_video command.
"""

import json
from pathlib import Path

from logging_utils import logger

from ai_video_creator.generators import (
    ZonosTTSRecipe,
    FluxImageRecipe,
)

from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER


class NarratorAndImageRecipeDefaultSettings:
    """Default settings for video recipe."""

    NARRATOR_VOICE = f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3"
    BACKGROUND_MUSIC = f"{DEFAULT_ASSETS_FOLDER}/background_music.mp3"


class NarratorAndImageRecipe:
    """Video recipe for creating videos from stories."""

    def __init__(self, recipe_path: Path):
        """Initialize NarratorAndImageRecipe with default settings."""
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
                logger.info(
                    f"Successfully loaded {len(self.narrator_data)} narrator recipes and {len(self.image_data)} image recipes"
                )
                self.save_current_state()

        except FileNotFoundError:
            logger.info(
                f"Recipe file not found: {file_path.name} - starting with empty recipe"
            )
        except json.JSONDecodeError:
            logger.error(
                f"Error decoding JSON from {file_path.name} - renaming to .old and starting with empty recipe"
            )
            # Rename corrupted file to .old for backup
            old_file_path = Path(str(file_path) + ".old")
            if file_path.exists():
                file_path.rename(old_file_path)
            # Create a new empty file
            self.save_current_state()
        except IOError as e:
            logger.error(f"Error loading video recipe from {file_path.name}: {e}")

    def _create_recipe_from_dict(self, data: dict):
        """Create the appropriate recipe object from dictionary data based on recipe_type."""
        recipe_type = data.get("recipe_type")

        if recipe_type == "FluxImageRecipeType":
            return FluxImageRecipe.from_dict(data)
        elif recipe_type == "ZonosTTSRecipeType":
            return ZonosTTSRecipe.from_dict(data)
        else:
            logger.error(f"Unknown recipe_type: {recipe_type}")
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
        narrator_data = [item.to_dict() for item in self.narrator_data]
        for i, item in enumerate(narrator_data, 1):
            item["index"] = i

        image_data = [item.to_dict() for item in self.image_data]
        for i, item in enumerate(image_data, 1):
            item["index"] = i

        return {
            "narrator_data": narrator_data,
            "image_data": image_data,
        }

    def save_current_state(self) -> None:
        """Save the current state of the video recipe to a file."""
        try:
            with open(self.recipe_path, "w", encoding="utf-8") as file:
                json.dump(self.to_dict(), file, ensure_ascii=False, indent=4)
        except IOError as e:
            logger.error(f"Error saving video recipe to {self.recipe_path.name}: {e}")
