"""
Background music recipe for managing background music data.
"""

import json
from pathlib import Path

from logging_utils import logger

from ai_video_creator.utils import VideoCreatorPaths, backup_file_to_old


class MusicRecipe:
    """Class to represent music data for a scene."""

    def __init__(self, narrator: str, prompt: str, mood: str, seed: int):
        self.narrator = narrator
        self.prompt = prompt
        self.mood = mood
        self.seed = seed

    def to_dict(self) -> dict:
        """Convert MusicRecipe to dictionary."""
        return {
            "narrator": self.narrator,
            "prompt": self.prompt,
            "mood": self.mood,
        }

    @staticmethod
    def from_dict(data: dict) -> "MusicRecipe":
        """Create MusicRecipe from dictionary."""
        required_fields = ["narrator", "prompt", "mood", "volume_level"]
        missing_fields = set(required_fields - data.keys())
        if missing_fields:
            raise ValueError(f"Missing fields in MusicRecipe data: {missing_fields}")

        return MusicRecipe(
            narrator=data["narrator"],
            prompt=data["prompt"],
            mood=data["mood"],
            seed=data["seed"],
        )


class BackgroundMusicRecipe:
    """Recipe for managing background music data for scenes."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize BackgroundMusicRecipe with default settings."""
        self._paths = video_creator_paths

        recipe_path = video_creator_paths.background_music_recipe_file
        self.recipe_file_parent = recipe_path.parent
        self.recipe_path = recipe_path

        self.music_recipes: list[MusicRecipe] = []

        self._from_dict(recipe_path)

    def add_music_recipe(self, music_recipe: MusicRecipe) -> None:
        """Add music data to the recipe."""
        self.music_recipes.append(music_recipe)
        self.save_current_state()

    def _from_dict(self, file_path: Path) -> None:
        """Load background music recipe from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                music_recipes = data.get("music_recipes", [])

                for item in music_recipes:
                    self.music_recipes.append(MusicRecipe.from_dict(item))

                logger.info(f"Successfully loaded {len(self.music_recipes)} background music recipes")
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
            logger.error(f"Error loading background music recipe from {file_path.name}: {e}")

    def clean(self) -> None:
        """Clean the current recipe data."""
        self.music_recipes = []

    def to_dict(self) -> dict:
        """Convert BackgroundMusicRecipe to dictionary.

        Returns:
            Dictionary representation of the BackgroundMusicRecipe
        """
        recipes = []
        for i, music_info in enumerate(self.music_recipes, 1):
            recipe_dict = {
                "index": i,
                **music_info.to_dict(),
            }
            recipes.append(recipe_dict)

        return {"music_recipes": recipes}

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
        for music_info in self.music_recipes:
            if isinstance(music_info, dict):
                music_path = music_info.get("music_path")
                if music_path:
                    music_path = Path(music_path)
                    if music_path.exists() and music_path.is_file():
                        used_assets.append(music_path)
        return used_assets

    def is_empty(self) -> bool:
        """Check if the music recipes list is empty."""
        return not self.music_recipes
