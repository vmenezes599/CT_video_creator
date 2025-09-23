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
        self.recipe_file_parent = recipe_path.parent
        self.recipe_path = recipe_path

        self.extra_data: list[dict] = []
        self.video_data: list[list[VideoRecipeBase]] = []

        self.__from_dict(recipe_path)

    def _ensure_index_exists(self, iteratable: list, index: int) -> None:
        """Extend lists to ensure the index exists."""
        # Extend sub_video_data if needed
        while len(iteratable) <= index:
            iteratable.append(None)

    def __is_within_directory(self, base: Path, target: Path) -> bool:
        """
        Check if a target path is within a base directory.
        Security method to prevent path traversal attacks.
        """
        try:
            return base.resolve(strict=False) in target.resolve(
                strict=False
            ).parents or base.resolve(strict=False) == target.resolve(strict=False)
        except (FileNotFoundError, RuntimeError, OSError):
            return False

    def __validate_and_resolve_path(self, asset_path: Path) -> Path:
        """
        Validate and resolve asset path, ensuring it's within the allowed directory.
        Returns the validated path or raises ValueError for security violations.
        """
        try:
            # Resolve the path relative to recipe_file_parent if it's relative
            if not asset_path.is_absolute():
                resolved_path = (self.recipe_file_parent / asset_path).resolve(
                    strict=False
                )
            else:
                resolved_path = asset_path.resolve(strict=False)

            # Security check: ensure the path is within the allowed directory
            if not self.__is_within_directory(self.recipe_file_parent, resolved_path):
                raise ValueError(f"Path traversal attempt detected: {asset_path}")

            return resolved_path
        except (FileNotFoundError, RuntimeError, OSError) as e:
            raise ValueError(f"Invalid path: {asset_path} - {e}") from e

    def add_video_data(
        self, video_data: list[VideoRecipeBase], extra_data: dict = None
    ) -> None:
        """Add video data to the recipe."""
        self.video_data.append(video_data)
        # Always append extra_data to keep indices aligned, use empty dict if None
        self.extra_data.append(extra_data if extra_data else {})
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
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(
                f"Error decoding JSON from {file_path.name} - renaming to .old and starting with empty recipe"
            )
            logger.error(f"Details: {e}")

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
            recipe = WanVideoRecipe.from_dict(data)
            # Validate and resolve media paths
            if recipe.media_path:
                recipe.media_path = str(
                    self.__validate_and_resolve_path(Path(recipe.media_path))
                )
            if recipe.color_match_media_path:
                recipe.color_match_media_path = str(
                    self.__validate_and_resolve_path(
                        Path(recipe.color_match_media_path)
                    )
                )
            return recipe
        else:
            logger.error(f"Unknown recipe_type: {recipe_type}")
            raise ValueError(f"Unknown recipe_type: {recipe_type}")

    def clean(self) -> None:
        """Clean the current recipe data."""
        self.video_data = []

    def to_dict(self) -> dict:
        """Convert VideoRecipe to dictionary with relative paths.

        Returns:
            Dictionary representation of the VideoRecipe
        """
        result = {"video_data": []}

        for i, item in enumerate(self.video_data, 1):
            recipe_list = []
            for recipe in item:
                recipe_dict = recipe.to_dict()
                media_path = recipe.media_path
                if media_path:
                    # Convert to relative path for storage
                    relative_path = Path(media_path).relative_to(
                        self.recipe_file_parent.resolve()
                    )
                    recipe_dict["media_path"] = str(relative_path)
                color_match_media_path = recipe.color_match_media_path
                if color_match_media_path:
                    # Convert to relative path for storage
                    relative_path = Path(color_match_media_path).relative_to(
                        self.recipe_file_parent.resolve()
                    )
                    recipe_dict["color_match_media_path"] = str(relative_path)
                recipe_list.append(recipe_dict)

            result_item = {
                "index": i,
                "extra_data": self.extra_data[i - 1],
                "recipe_list": recipe_list,
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
