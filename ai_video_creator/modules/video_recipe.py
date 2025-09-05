"""
Video executor for create_video command.
"""

import json
from pathlib import Path

from logging_utils import begin_file_logging, logger
from ai_video_creator.prompt import Prompt

from ai_video_creator.generators import (
    ZonosTTSRecipe,
    FluxImageRecipe,
)

from ai_video_creator.utils.video_recipe_paths import VideoRecipePaths
from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER


class VideoRecipeDefaultSettings:
    """Default settings for video recipe."""

    NARRATOR_VOICE = f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3"
    BACKGROUND_MUSIC = f"{DEFAULT_ASSETS_FOLDER}/background_music.mp3"


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
                logger.info(
                    f"Successfully loaded {len(self.narrator_data)} narrator recipes and {len(self.image_data)} image recipes"
                )
                self.save_current_state()

        except FileNotFoundError:
            logger.info(
                f"Recipe file not found: {file_path.name} - starting with empty recipe"
            )
        except (IOError, json.JSONDecodeError) as e:
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
        logger.info(
            "Initializing VideoRecipeBuilder for story:"
            f" {story_folder.name}, chapter: {chapter_prompt_index}"
        )

        self.__paths = VideoRecipePaths(story_folder, chapter_prompt_index)
        self.__chapter_prompt_path = self.__paths.chapter_prompt_path

        # Load video prompt
        self.__video_prompt = Prompt.load_from_json(self.__chapter_prompt_path)
        self._recipe = None

    def _verify_recipe_against_prompt(self) -> None:
        """Verify the recipe against the prompt to ensure all required data is present."""
        logger.debug("Verifying recipe against prompt data")

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
        logger.info(
            f"Creating Flux image recipes for {len(self.__video_prompt)} prompts"
        )

        for prompt in self.__video_prompt:
            recipe = FluxImageRecipe(prompt=prompt.visual_prompt, seed=seed)
            self._recipe.add_image_data(recipe)

        logger.info(
            f"Successfully created {len(self.__video_prompt)} Flux image recipes"
        )

    def _create_zonos_tts_narrator_recipe(self, seed: int | None = None) -> None:
        """Create Zonos TTS narrator recipe."""
        logger.info(
            f"Creating Zonos TTS narrator recipes for {len(self.__video_prompt)} prompts"
        )

        for prompt in self.__video_prompt:
            recipe = ZonosTTSRecipe(
                prompt=prompt.narrator,
                clone_voice_path=VideoRecipeDefaultSettings.NARRATOR_VOICE,
                seed=seed,
            )
            self._recipe.add_narrator_data(recipe)

        logger.info(
            f"Successfully created {len(self.__video_prompt)} Zonos TTS narrator recipes"
        )

    def create_video_recipe(self) -> None:
        """Create video recipe from story folder and chapter prompt index."""

        with begin_file_logging(
            name="VideoRecipeBuilder",
            log_level="TRACE",
            base_folder=self.__paths.video_path,
        ):
            logger.info("Starting video recipe creation process")

            self._recipe = VideoRecipe(self.__paths.recipe_file)

            if not self._verify_recipe_against_prompt():
                self._recipe.clean()
                self._create_flux_image_recipe()
                self._create_zonos_tts_narrator_recipe()
                # self._create_spark_tts_narrator_recipe()

            logger.info("Video recipe creation completed successfully")
