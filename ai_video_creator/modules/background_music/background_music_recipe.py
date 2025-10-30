"""
Background music recipe for managing background music data.
"""

import json
from pathlib import Path

from logging_utils import logger

from ai_video_creator.utils import VideoCreatorPaths


class BackgroundMusicRecipe:
    """Recipe for managing background music data for scenes."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize BackgroundMusicRecipe with default settings."""
        self._paths = video_creator_paths

        recipe_path = video_creator_paths.background_music_recipe_file
        self.recipe_file_parent = recipe_path.parent
        self.recipe_path = recipe_path

        self.extra_data: list[dict] = []
        self.music_data: list[dict] = []

        self.__from_dict(recipe_path)

    def add_music_data(self, music_data: dict, extra_data: dict = None) -> None:
        """Add music data to the recipe."""
        self.music_data.append(music_data)
        # Always append extra_data to keep indices aligned, use empty dict if None
        self.extra_data.append(extra_data if extra_data else {})
        self.save_current_state()

    def __from_dict(self, file_path: Path) -> None:
        """Load background music recipe from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                music_data = data.get("music_data", [])

                for item in music_data:
                    music_info = item.get("music_info", {})
                    self.music_data.append(music_info)
                    extra_data = item.get("extra_data", {})
                    self.extra_data.append(extra_data)

                logger.info(f"Successfully loaded {len(self.music_data)} background music recipes")
                self.save_current_state()

        except FileNotFoundError:
            logger.info(f"Recipe file not found: {file_path.name} - starting with empty recipe")
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Error decoding JSON from {file_path.name} - renaming to .old and starting with empty recipe")
            logger.error(f"Details: {e}")

            # Rename corrupted file to .old for backup
            old_file_path = Path(str(file_path) + ".old")
            if file_path.exists():
                file_path.rename(old_file_path)
            # Create a new empty file
            self.save_current_state()
        except IOError as e:
            logger.error(f"Error loading background music recipe from {file_path.name}: {e}")

    def clean(self) -> None:
        """Clean the current recipe data."""
        self.music_data = []
        self.extra_data = []

    def to_dict(self) -> dict:
        """Convert BackgroundMusicRecipe to dictionary.

        Returns:
            Dictionary representation of the BackgroundMusicRecipe
        """
        result = {"music_data": []}

        for i, music_info in enumerate(self.music_data, 1):
            result_item = {
                "index": i,
                "extra_data": self.extra_data[i - 1],
                "music_info": music_info,
            }
            result["music_data"].append(result_item)

        return result

    def save_current_state(self) -> None:
        """Save the current state of the background music recipe to a file."""
        try:
            # Ensure parent directory exists
            self.recipe_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.recipe_path, "w", encoding="utf-8") as file:
                json.dump(self.to_dict(), file, ensure_ascii=False, indent=4)
        except IOError as e:
            logger.error(f"Error saving background music recipe to {self.recipe_path.name}: {e}")

    def get_used_assets_list(self) -> list[Path]:
        """Get a list of all used background music asset file paths."""
        used_assets = []
        for music_info in self.music_data:
            if isinstance(music_info, dict):
                music_path = music_info.get("music_path")
                if music_path:
                    music_path = Path(music_path)
                    if music_path.exists() and music_path.is_file():
                        used_assets.append(music_path)
        return used_assets
