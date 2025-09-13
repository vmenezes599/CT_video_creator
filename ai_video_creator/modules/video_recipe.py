"""
Video executor for create_video command.
"""

import json
from pathlib import Path

from logging_utils import begin_file_logging, logger
from ai_video_creator.prompt import Prompt

from ai_video_creator.generators import VideoRecipeBase, WanVideoRecipe

from ai_video_creator.utils.video_creator_paths import VideoCreatorPaths
from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER
from .narrator_and_image_asset_manager import NarratorAndImageAssetsFile


class VideoRecipeDefaultSettings:
    """Default settings for video recipe."""

    NARRATOR_VOICE = f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3"
    BACKGROUND_MUSIC = f"{DEFAULT_ASSETS_FOLDER}/background_music.mp3"


class VideoRecipeFile:
    """Video recipe for creating videos from stories."""

    def __init__(self, recipe_path: Path):
        """Initialize VideoRecipe with default settings."""
        self.recipe_path = recipe_path

        self.video_data: list[list[VideoRecipeBase]] = []

        self.__from_dict(recipe_path)

    def _ensure_index_exists(self, iteratable: list, index: int) -> None:
        """Extend lists to ensure the index exists."""
        # Extend sub_video_data if needed
        while len(iteratable) <= index:
            iteratable.append(None)

    def add_video_data(self, video_data: list[VideoRecipeBase]) -> None:
        """Add video data to the recipe."""
        self.video_data.append(video_data)
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

                logger.info(f"Successfully loaded {len(self.video_data)} video recipes")
                self.save_current_state()

        except FileNotFoundError:
            logger.info(
                f"Recipe file not found: {file_path.name} - starting with empty recipe"
            )
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {file_path.name} - renaming to .old and starting with empty recipe")
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
            item = {"index": i, "recipe_list": [recipe.to_dict() for recipe in item]}
            result["video_data"].append(item)

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


class VideoRecipeBuilder:
    """Video recipe for creating videos from stories."""

    def __init__(self, story_folder: Path, chapter_prompt_index: int):
        """Initialize VideoRecipe with recipe data.

        Args:
            video_data: List of video data dictionaries
            seeds: List of seeds for each generation (None elements use default behavior)
        """
        logger.info(
            "Initializing VideoRecipeBuilder for story:"
            f" {story_folder.name}, chapter: {chapter_prompt_index}"
        )

        self.__paths = VideoCreatorPaths(story_folder, chapter_prompt_index)
        self.__chapter_prompt_path = self.__paths.chapter_prompt_path

        # Load video prompt
        self.__video_prompt = Prompt.load_from_json(self.__chapter_prompt_path)
        self.__image_assets = NarratorAndImageAssetsFile(
            self.__paths.narrator_and_image_asset_file
        )
        self._recipe = None

    def _verify_recipe_against_prompt(self) -> None:
        """Verify the recipe against the prompt to ensure all required data is present."""
        logger.debug("Verifying recipe against prompt data")

        if (
            not self._recipe.video_data
            or len(self._recipe.video_data) != len(self.__video_prompt)
            or len(self.__image_assets.image_assets) != len(self.__video_prompt)
        ):
            return False

        return True

    def _create_video_recipes(
        self, sub_videos_length: int, seed: int | None = None
    ) -> None:
        """Create video recipe from story folder and chapter prompt index."""
        logger.info(
            f"Creating Wan video recipes for {len(self.__video_prompt)} prompts"
        )

        for i, prompt in enumerate(self.__video_prompt):
            # Get corresponding image asset if available, otherwise None
            image_asset = (
                self.__image_assets.image_assets[i] 
                if i < len(self.__image_assets.image_assets) 
                else None
            )
            
            recipe_list = []
            recipe = self._create_wan_video_recipe(
                prompt=prompt, image_asset=image_asset, seed=seed
            )
            recipe_list.append(recipe)
            for _ in range(sub_videos_length - 1):
                recipe = self._create_wan_video_recipe(prompt=prompt, seed=seed)
                recipe_list.append(recipe)

            self._recipe.add_video_data(recipe_list)

        logger.info(
            f"Successfully created {len(self.__video_prompt)} Wan video recipes"
        )

    def _create_wan_video_recipe(
        self, prompt: Prompt, image_asset: Path | None = None, seed: int | None = None
    ) -> None:
        """Create video recipe from story folder and chapter prompt index."""
        return WanVideoRecipe(
            prompt=prompt.visual_description,
            media_path=str(image_asset) if image_asset else None,
            seed=seed,
        )

    def create_video_recipe(self, sub_videos_length: int = 5) -> None:
        """Create video recipe from story folder and chapter prompt index."""

        with begin_file_logging(
            name="VideoRecipeBuilder",
            log_level="TRACE",
            base_folder=self.__paths.video_path,
        ):
            logger.info("Starting video recipe creation process")

            self._recipe = VideoRecipeFile(self.__paths.video_recipe_file)

            if not self._verify_recipe_against_prompt():
                self._recipe.clean()
                self._create_video_recipes(sub_videos_length)

            logger.info("Video recipe creation completed successfully")
