"""
Image recipe for managing image-specific recipe data.
"""

import json
from pathlib import Path

from logging_utils import logger

from ai_video_creator.generators import FluxImageRecipe
from ai_video_creator.utils import VideoCreatorPaths, backup_file_to_old


class ImageRecipe:
    """Image recipe for creating images from text prompts."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize ImageRecipe with default settings."""
        self.recipe_path = video_creator_paths.image_recipe_file

        self.recipes_data: list[FluxImageRecipe] = []
        self.extra_image_data: list[dict] = []
        self.__load_from_file(self.recipe_path)

    def add_image_data(self, image_data: FluxImageRecipe, extra_image_data: dict = None) -> None:
        """Add image data to the recipe."""
        self.recipes_data.append(image_data)
        # Always append extra_image_data to maintain alignment with image_data
        self.extra_image_data.append(extra_image_data or {})
        self.save_current_state()

    def __load_from_file(self, file_path: Path) -> None:
        """Load image recipe from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.recipes_data = [self._create_recipe_from_dict(item) for item in data["image_data"]]

                for image_data in data["image_data"]:
                    extra_data = image_data.get("extra_data", {})
                    self.extra_image_data.append(extra_data)

                logger.info(f"Successfully loaded {len(self.recipes_data)} image recipes")
                self.save_current_state()

        except FileNotFoundError:
            logger.info(f"Image recipe file not found: {file_path.name} - starting with empty recipe")
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
            logger.error(f"Error loading image recipe from {file_path.name}: {e}")

    def _create_recipe_from_dict(self, data: dict) -> FluxImageRecipe:
        """Create the appropriate recipe object from dictionary data."""
        recipe_type = data.get("recipe_type")

        if recipe_type == "FluxImageRecipeType":
            return FluxImageRecipe.from_dict(data)
        else:
            logger.error(f"Unknown image recipe_type: {recipe_type}")
            raise ValueError(f"Unknown image recipe_type: {recipe_type}")

    def clean(self) -> None:
        """Clean the current recipe data."""
        self.recipes_data = []
        self.extra_image_data = []

    def to_dict(self) -> dict:
        """Convert ImageRecipe to dictionary.

        Returns:
            Dictionary representation of the ImageRecipe
        """
        image_data = [
            {"index": i, "extra_data": extra, **item.to_dict()}
            for i, (item, extra) in enumerate(zip(self.recipes_data, self.extra_image_data), 1)
        ]

        return {"image_data": image_data}

    def save_current_state(self) -> None:
        """Save the current state of the image recipe to a file."""
        try:
            with open(self.recipe_path, "w", encoding="utf-8") as file:
                json.dump(self.to_dict(), file, ensure_ascii=False, indent=4)
        except IOError as e:
            logger.error(f"Error saving image recipe to {self.recipe_path.name}: {e}")

    def is_complete(self) -> bool:
        """Check if the image recipe is complete."""
        return len(self.recipes_data) > 0

    def __len__(self) -> int:
        """Return the number of image recipes."""
        return len(self.recipes_data)

    def __getitem__(self, index: int) -> FluxImageRecipe:
        """Get image recipe by index."""
        return self.recipes_data[index]
