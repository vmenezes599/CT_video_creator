"""
Narrator recipe builder for creating narrator recipes from prompts.
"""

from pathlib import Path

from logging_utils import begin_file_logging, logger
from ai_video_creator.prompt import Prompt

from ai_video_creator.generators import ZonosTTSRecipe

from ai_video_creator.utils import VideoCreatorPaths

from .narrator_recipe import (
    NarratorRecipe,
    NarratorRecipeDefaultSettings,
)


class NarratorRecipeBuilder:
    """Narrator recipe builder for creating narrator recipes from stories."""

    def __init__(self, story_folder: Path, chapter_prompt_index: int):
        """Initialize NarratorRecipeBuilder with recipe data."""
        logger.info(
            "Initializing NarratorRecipeBuilder for story:"
            f" {story_folder.name}, chapter: {chapter_prompt_index + 1}"
        )

        self._paths = VideoCreatorPaths(story_folder, chapter_prompt_index)
        self.__chapter_prompt_path = self._paths.chapter_prompt_path

        # Load video prompt
        self.__video_prompt = Prompt.load_from_json(self.__chapter_prompt_path)
        self._recipe = None

    @property
    def recipe(self):
        """Get the current recipe."""
        return self._recipe

    def _verify_recipe_against_prompt(self) -> bool:
        """Verify the recipe against the prompt to ensure all required data is present."""
        logger.debug("Verifying narrator recipe against prompt data")

        if not self._recipe.narrator_data or len(self._recipe.narrator_data) != len(
            self.__video_prompt
        ):
            return False

        return True

    def _create_zonos_tts_narrator_recipe(self, seed: int | None = None) -> None:
        """Create Zonos TTS narrator recipe."""
        logger.info(
            f"Creating Zonos TTS narrator recipes for {len(self.__video_prompt)} prompts"
        )

        for prompt in self.__video_prompt:
            recipe = ZonosTTSRecipe(
                prompt=prompt.narrator,
                clone_voice_path=NarratorRecipeDefaultSettings.NARRATOR_VOICE,
                seed=seed,
            )
            self._recipe.add_narrator_data(recipe)

        logger.info(
            f"Successfully created {len(self.__video_prompt)} Zonos TTS narrator recipes"
        )

    def create_narrator_recipes(self) -> None:
        """Create narrator recipe from story folder and chapter prompt index."""

        with begin_file_logging(
            name="create_narrator_recipes_from_prompt",
            log_level="TRACE",
            base_folder=self._paths.chapter_folder,
        ):
            logger.info("Starting narrator recipe creation process")

            # Create narrator recipe file path
            narrator_recipe_file = self._paths.narrator_recipe_file

            self._recipe = NarratorRecipe(narrator_recipe_file)

            if not self._verify_recipe_against_prompt():
                self._recipe.clean()
                self._create_zonos_tts_narrator_recipe()

            logger.info("Narrator recipe creation completed successfully")
