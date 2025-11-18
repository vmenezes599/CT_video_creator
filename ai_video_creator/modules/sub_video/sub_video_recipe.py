"""
Video executor for create_video command.
"""

import json
from pathlib import Path

from logging_utils import logger

from ai_video_creator.generators import (
    WanI2VRecipe,
    WanT2VRecipe,
)

from ai_video_creator.utils import VideoCreatorPaths, backup_file_to_old
from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER


class SubVideoRecipeDefaultSettings:
    """Default settings for video recipe."""

    BACKGROUND_MUSIC = f"{DEFAULT_ASSETS_FOLDER}/background_music.mp3"


class SubVideoRecipe:
    """Video recipe for creating videos from stories."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize VideoRecipe with default settings."""
        self._paths = video_creator_paths

        recipe_path = video_creator_paths.sub_video_recipe_file
        self.recipe_file_parent = recipe_path.parent
        self.recipe_path = recipe_path

        self.extra_data: list[dict] = []
        self.video_data: list[list[WanI2VRecipe | WanT2VRecipe]] = []

        self._from_dict(recipe_path)

    def add_video_data(self, video_data: list[WanI2VRecipe | WanT2VRecipe], extra_data: dict | None = None) -> None:
        """Add video data to the recipe."""
        self.video_data.append(video_data)
        # Always append extra_data to keep indices aligned, use empty dict if None
        self.extra_data.append(extra_data if extra_data else {})
        self.save_current_state()

    def _from_dict(self, file_path: Path) -> None:
        """Load video recipe from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                video_data = data.get("video_data", [])

                for item in video_data:
                    recipe_list = item.get("recipe_list", [])
                    self.video_data.append([self._create_recipe_from_dict(recipe) for recipe in recipe_list])
                    extra_data = item.get("extra_data", {})
                    self.extra_data.append(extra_data)

                logger.info(f"Successfully loaded {len(self.video_data)} video recipes")
                self.save_current_state()

        except FileNotFoundError:
            logger.info(f"Recipe file not found: {file_path.name} - starting with empty recipe")
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(
                f"Error decoding JSON from {file_path.name} - renaming to .old and starting with empty recipe\n\nDetails: {e}"
            )

            # Back up the corrupted file before overwriting
            backup_file_to_old(file_path)
            logger.debug(f"Backed up corrupted file to: {file_path.name}.old")

            # Create a new empty file
            self.save_current_state()
        except IOError as e:
            logger.error(f"Error loading video recipe from {file_path.name}: {e}")

    def _create_recipe_from_dict(self, data: dict):
        """Create the appropriate recipe object from dictionary data based on recipe_type."""
        recipe_type = data.get("recipe_type")

        recipe = None
        if recipe_type == "WanI2VRecipeType":
            recipe = WanI2VRecipe.from_dict(data)
        elif recipe_type == "WanT2VRecipeType":
            recipe = WanT2VRecipe.from_dict(data)
        else:
            logger.error(f"Unknown recipe_type: {recipe_type}")
            raise ValueError(f"Unknown recipe_type: {recipe_type}")

        if recipe.media_path:
            recipe.media_path = str(self._paths.unmask_asset_path(Path(recipe.media_path)))
        if recipe.color_match_media_path:
            recipe.color_match_media_path = str(self._paths.unmask_asset_path(Path(recipe.color_match_media_path)))
        return recipe

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
            for recipe_index, recipe in enumerate(item, 1):
                recipe_dict = recipe.to_dict()
                recipe_dict = {"sub_video_index": recipe_index, **recipe_dict}

                # Handle media_path if it exists (only for WanI2VRecipe)
                if hasattr(recipe, "media_path"):
                    media_path = recipe.media_path
                    if media_path:
                        # Convert to relative path for storage
                        try:
                            relative_path = Path(media_path).relative_to(self.recipe_file_parent.resolve())
                            recipe_dict["media_path"] = str(relative_path)
                        except ValueError:
                            # Path is outside the directory, store as absolute
                            recipe_dict["media_path"] = str(media_path)
                color_match_media_path = recipe.color_match_media_path
                if color_match_media_path:
                    # Convert to relative path for storage
                    try:
                        relative_path = Path(color_match_media_path).relative_to(self.recipe_file_parent.resolve())
                        recipe_dict["color_match_media_path"] = str(relative_path)
                    except ValueError:
                        # Path is outside the directory, store as absolute
                        recipe_dict["color_match_media_path"] = str(color_match_media_path)
                recipe_list.append(recipe_dict)

            result_item = {
                "index": i,
                "extra_data": self.extra_data[i - 1],
                "recipe_list": recipe_list,
            }
            result["video_data"].append(result_item)

        return result

    def _create_temp_copy_paste_helper_file(self) -> str:
        """"""

        result = ""

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

    def get_used_assets_list(self) -> list[Path]:
        """Get a list of all used media asset file paths."""
        used_assets = []
        for video_recipes in self.video_data:
            for recipe in video_recipes:
                if hasattr(recipe, "media_path"):
                    media_path = Path(recipe.media_path) if recipe.media_path else None
                    if media_path is not None and media_path.exists() and media_path.is_file():
                        used_assets.append(media_path)
                color_match_media_path = Path(recipe.color_match_media_path) if recipe.color_match_media_path else None
                if (
                    color_match_media_path is not None
                    and color_match_media_path.exists()
                    and color_match_media_path.is_file()
                ):
                    used_assets.append(color_match_media_path)
        return used_assets
