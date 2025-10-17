"""
Narrator recipe for managing narrator-specific recipe data.
"""

import json
from pathlib import Path

from logging_utils import logger

from ai_video_creator.utils import VideoCreatorPaths
from ai_video_creator.generators import ZonosTTSRecipe
from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER


class NarratorRecipeDefaultSettings:
    """Default settings for narrator recipe."""

    NARRATOR_VOICE = f"{DEFAULT_ASSETS_FOLDER}/voices/ElevenLabs_Clyde.mp3"


class NarratorRecipe:
    """Narrator recipe for creating audio from text."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize NarratorRecipe with default settings."""
        self.video_creator_paths = video_creator_paths

        self.recipe_path = self.video_creator_paths.narrator_recipe_file
        self.narrator_data: list[ZonosTTSRecipe] = []

        self._load_from_file(self.recipe_path)

    def add_narrator_data(self, narrator_data: ZonosTTSRecipe) -> None:
        """Add narrator data to the recipe."""
        self.narrator_data.append(narrator_data)

        self.save_current_state()

    def _load_from_file(self, file_path: Path) -> None:
        """Load narrator recipe from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.narrator_data = [
                    self._create_recipe_from_dict(item)
                    for item in data["narrator_data"]
                ]

                logger.info(
                    f"Successfully loaded {len(self.narrator_data)} narrator recipes"
                )
                self.save_current_state()

        except FileNotFoundError:
            logger.info(
                f"Narrator recipe file not found: {file_path.name} - starting with empty recipe"
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
            logger.error(f"Error loading narrator recipe from {file_path.name}: {e}")

    def _create_recipe_from_dict(self, data: dict) -> ZonosTTSRecipe:
        """Create the appropriate recipe object from dictionary data."""
        recipe_type = data.get("recipe_type")

        if "clone_voice_path" in data:
            data["clone_voice_path"] = str(
                self.video_creator_paths.unmask_asset_path(
                    Path(data["clone_voice_path"])
                )
            )

        if recipe_type == "ZonosTTSRecipeType":
            return ZonosTTSRecipe.from_dict(data)
        else:
            logger.error(f"Unknown narrator recipe_type: {recipe_type}")
            raise ValueError(f"Unknown narrator recipe_type: {recipe_type}")

    def clean(self) -> None:
        """Clean the current recipe data."""
        self.narrator_data = []

    def to_dict(self) -> dict:
        """Convert NarratorRecipe to dictionary.

        Returns:
            Dictionary representation of the NarratorRecipe
        """
        available_voices_paths = [
            self.video_creator_paths.get_default_assets_folder() / "voices",
            self.video_creator_paths.get_user_assets_folder() / "voices",
        ]
        available_voices = []
        for path in available_voices_paths:
            available_voices.extend(
                [
                    str(self.video_creator_paths.mask_asset_path(f))
                    for f in path.glob("*.mp3")
                ]
            )

        narrator_data = [item.to_dict() for item in self.narrator_data]
        result = []
        for i, item in enumerate(narrator_data, 1):
            item["clone_voice_path"] = str(
                self.video_creator_paths.mask_asset_path(Path(item["clone_voice_path"]))
            )
            result.append({"index": i, **item, "available_voices": available_voices})

        return {"narrator_data": result}

    def save_current_state(self) -> None:
        """Save the current state of the narrator recipe to a file."""
        try:
            with open(self.recipe_path, "w", encoding="utf-8") as file:
                json.dump(self.to_dict(), file, ensure_ascii=False, indent=4)
        except IOError as e:
            logger.error(
                f"Error saving narrator recipe to {self.recipe_path.name}: {e}"
            )

    def __len__(self) -> int:
        """Return the number of narrator recipes."""
        return len(self.narrator_data)

    def __getitem__(self, index: int) -> ZonosTTSRecipe:
        """Get narrator recipe by index."""
        return self.narrator_data[index]
