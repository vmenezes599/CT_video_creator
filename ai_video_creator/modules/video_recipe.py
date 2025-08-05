"""
Video executor for create_video command.
"""

import json
from pathlib import Path

from logging_utils import begin_console_logging, logger
from ai_video_creator.prompt import Prompt

from ai_video_creator.generators import (
    SparkTTSRecipe,
    FluxImageRecipe,
)

from ai_video_creator.helpers.video_recipe_paths import VideoRecipePaths


class VideoRecipeDefaultSettings:
    """Default settings for video recipe."""

    NARRATOR_VOICE = "default-assets/voices/voice_002.mp3"
    BACKGROUND_MUSIC = "default-assets/background_music.mp3"


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
        logger.debug(f"Adding narrator data of type: {type(narrator_data).__name__}")
        self.narrator_data.append(narrator_data)
        self.save_current_state()

    def add_image_data(self, image_data) -> None:
        """Add image data to the recipe."""
        logger.debug(f"Adding image data of type: {type(image_data).__name__}")
        self.image_data.append(image_data)
        self.save_current_state()

    def __load_from_file(self, file_path: Path) -> None:
        """Load video recipe from a JSON file."""
        try:
            logger.info(f"Loading video recipe from: {file_path.name}")
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.narrator_data = [
                    self._create_recipe_from_dict(item)
                    for item in data["narrator_data"]
                ]
                self.image_data = [
                    self._create_recipe_from_dict(item) for item in data["image_data"]
                ]
                logger.info(f"Successfully loaded {len(self.narrator_data)} narrator recipes and {len(self.image_data)} image recipes")

        except FileNotFoundError:
            logger.debug(f"Recipe file not found: {file_path.name} - starting with empty recipe")
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error loading video recipe from {file_path.name}: {e}")
            print(f"Error loading video recipe: {e}")

    def _create_recipe_from_dict(self, data: dict):
        """Create the appropriate recipe object from dictionary data based on recipe_type."""
        recipe_type = data.get("recipe_type")
        logger.debug(f"Creating recipe from dict with type: {recipe_type}")

        if recipe_type == "SparkTTSRecipeType":
            return SparkTTSRecipe.from_dict(data)
        elif recipe_type == "FluxImageRecipeType":
            return FluxImageRecipe.from_dict(data)
        else:
            logger.error(f"Unknown recipe_type: {recipe_type}")
            raise ValueError(f"Unknown recipe_type: {recipe_type}")

    def clean(self) -> None:
        """Clean the current recipe data."""
        logger.info("Cleaning recipe data - removing all narrator and image data")
        self.narrator_data = []
        self.image_data = []

    def to_dict(self) -> dict:
        """Convert VideoRecipe to dictionary.

        Returns:
            Dictionary representation of the VideoRecipe
        """
        return {
            "narrator_data": [item.to_dict() for item in self.narrator_data],
            "image_data": [item.to_dict() for item in self.image_data],
        }

    def save_current_state(self) -> None:
        """Save the current state of the video recipe to a file."""
        try:
            logger.debug(f"Saving video recipe state to: {self.recipe_path.name}")
            with open(self.recipe_path, "w", encoding="utf-8") as file:
                json.dump(self.to_dict(), file, indent=4)
            logger.trace(f"Recipe saved with {len(self.narrator_data)} narrator items and {len(self.image_data)} image items")
        except IOError as e:
            logger.error(f"Error saving video recipe to {self.recipe_path.name}: {e}")
            print(f"Error saving video recipe: {e}")


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
        logger.info(f"Initializing VideoRecipeBuilder for story: {story_folder.name}, chapter: {chapter_prompt_index}")
        
        # Initialize path management
        self.__paths = VideoRecipePaths(story_folder, chapter_prompt_index)
        self.__chapter_prompt_path = self.__paths.chapter_prompt_path

        # Load video prompt
        logger.debug(f"Loading video prompt from: {self.__chapter_prompt_path.name}")
        self.__video_prompt = Prompt.load_from_json(self.__chapter_prompt_path)
        logger.info(f"Loaded {len(self.__video_prompt)} prompts from chapter file")
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
            logger.debug(f"Recipe verification failed - narrator: {len(self._recipe.narrator_data) if self._recipe.narrator_data else 0}, images: {len(self._recipe.image_data) if self._recipe.image_data else 0}, prompts: {len(self.__video_prompt)}")
            return False
        
        logger.debug("Recipe verification passed - all data present and counts match")
        return True

    def _create_flux_image_recipe(self, seed: int | None = None) -> None:
        """Create video recipe from story folder and chapter prompt index."""
        logger.info(f"Creating Flux image recipes for {len(self.__video_prompt)} prompts")
        if seed is not None:
            logger.debug(f"Using seed: {seed}")
        
        for i, prompt in enumerate(self.__video_prompt, 1):
            logger.debug(f"Creating image recipe {i}/{len(self.__video_prompt)}")
            recipe = FluxImageRecipe(prompt=prompt.visual_prompt, seed=seed)
            self._recipe.add_image_data(recipe)
        
        logger.info(f"Successfully created {len(self.__video_prompt)} Flux image recipes")

    def _create_spark_tts_narrator_recipe(self) -> None:
        """Create Spark TTS narrator recipe."""
        logger.info(f"Creating Spark TTS narrator recipes for {len(self.__video_prompt)} prompts")
        logger.debug(f"Using voice: {VideoRecipeDefaultSettings.NARRATOR_VOICE}")
        
        for i, prompt in enumerate(self.__video_prompt, 1):
            logger.debug(f"Creating narrator recipe {i}/{len(self.__video_prompt)}")
            recipe = SparkTTSRecipe(
                prompt=prompt.narrator,
                clone_voice_path=VideoRecipeDefaultSettings.NARRATOR_VOICE,
            )
            self._recipe.add_narrator_data(recipe)
        
        logger.info(f"Successfully created {len(self.__video_prompt)} Spark TTS narrator recipes")

    def create_video_recipe(self) -> None:
        """Create video recipe from story folder and chapter prompt index."""
        with begin_console_logging(name="VideoRecipeBuilder", log_level="TRACE"):
            logger.info("Starting video recipe creation process")
            
            self._recipe = VideoRecipe(self.__paths.recipe_file)

            if not self._verify_recipe_against_prompt():
                logger.info("Recipe verification failed - regenerating recipe data")
                self._recipe.clean()
                self._create_flux_image_recipe()
                self._create_spark_tts_narrator_recipe()
                logger.info("Video recipe creation completed successfully")
            else:
                logger.info("Existing recipe is valid - no regeneration needed")
