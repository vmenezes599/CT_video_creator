"""
Video executor for create_video command.
"""

import json
from pathlib import Path

from logging_utils import logger

from ai_video_creator.generators import VideoRecipeBase, WanVideoRecipe

from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER


class SubVideoRecipeDefaultSettings:
    """Default settings for video recipe."""

    NARRATOR_VOICE = f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3"
    BACKGROUND_MUSIC = f"{DEFAULT_ASSETS_FOLDER}/background_music.mp3"


class SubVideoRecipe:
    """Video recipe for creating videos from stories."""

    def __init__(self, recipe_path: Path):
        """Initialize VideoRecipe with default settings."""
        self.recipe_path = recipe_path

        self.extra_data: list[dict] = []
        self.video_data: list[list[VideoRecipeBase]] = []

        self.__from_dict(recipe_path)

    def _ensure_index_exists(self, iteratable: list, index: int) -> None:
        """Extend lists to ensure the index exists."""
        # Extend sub_video_data if needed
        while len(iteratable) <= index:
            iteratable.append(None)

    def add_video_data(
        self, video_data: list[VideoRecipeBase], extra_data: dict = None
    ) -> None:
        """Add video data to the recipe."""
        self.video_data.append(video_data)
        if extra_data:
            self.extra_data.append(extra_data)
        self.save_current_state()

    def __from_dict(self, file_path: Path) -> None:
        """Load video recipe from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                video_data = data.get("video_data", [])

                for item in video_data:
                    recipe_list = item.get("recipe_list", [])
                    self.video_data.append(
                        [
                            self._create_recipe_from_dict(recipe)
                            for recipe in recipe_list
                        ]
                    )
                    extra_data = item.get("extra_data", {})
                    self.extra_data.append(extra_data)

                logger.info(f"Successfully loaded {len(self.video_data)} video recipes")
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

        if recipe_type == "WanVideoRecipeType":
            return WanVideoRecipe.from_dict(data)
        else:
            logger.error(f"Unknown recipe_type: {recipe_type}")
            raise ValueError(f"Unknown recipe_type: {recipe_type}")

    def clean(self) -> None:
        """Clean the current recipe data."""
        self.video_data = []

    def to_dict(self) -> dict:
        """Convert VideoRecipe to dictionary.

        Returns:
            Dictionary representation of the VideoRecipe
        """
        result = {"video_data": []}

        for i, item in enumerate(self.video_data, 1):
            result_item = {
                "index": i,
                "extra_data": self.extra_data[i - 1],
                "recipe_list": [recipe.to_dict() for recipe in item],
            }
            result["video_data"].append(result_item)

        return result

    def save_current_state(self) -> None:
        """Save the current state of the video recipe to a file."""
        try:
            # Ensure parent directory exists
            self.recipe_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.recipe_path, "w", encoding="utf-8") as file:
                json.dump(self.to_dict(), file, ensure_ascii=False, indent=4)
        except IOError as e:
            logger.error(f"Error saving video recipe to {self.recipe_path.name}: {e}")
