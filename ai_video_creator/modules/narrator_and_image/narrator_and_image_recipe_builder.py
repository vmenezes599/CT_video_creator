"""
Video executor for create_video command.
"""

from pathlib import Path

from logging_utils import begin_file_logging, logger
from ai_video_creator.prompt import Prompt

from ai_video_creator.generators import (
    ZonosTTSRecipe,
    FluxImageRecipe,
)

from ai_video_creator.utils import VideoCreatorPaths

from .narrator_and_image_recipe import (
    NarratorAndImageRecipe,
    NarratorAndImageRecipeDefaultSettings,
)


class NarratorAndImageRecipeBuilder:
    """Video recipe for creating videos from stories."""

    def __init__(self, story_folder: Path, chapter_prompt_index: int):
        """Initialize VideoRecipe with recipe data."""
        logger.info(
            "Initializing NarratorAndImageRecipeBuilder for story:"
            f" {story_folder.name}, chapter: {chapter_prompt_index}"
        )

        self._paths = VideoCreatorPaths(story_folder, chapter_prompt_index)
        self.__chapter_prompt_path = self._paths.chapter_prompt_path

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
                clone_voice_path=NarratorAndImageRecipeDefaultSettings.NARRATOR_VOICE,
                seed=seed,
            )
            self._recipe.add_narrator_data(recipe)

        logger.info(
            f"Successfully created {len(self.__video_prompt)} Zonos TTS narrator recipes"
        )

    def create_narrator_and_image_recipes(self) -> None:
        """Create video recipe from story folder and chapter prompt index."""

        with begin_file_logging(
            name="CreateNarratorAndImageRecipesFromPrompt",
            log_level="TRACE",
            base_folder=self._paths.video_path,
        ):
            logger.info("Starting video recipe creation process")

            self._recipe = NarratorAndImageRecipe(
                self._paths.narrator_and_image_recipe_file
            )

            if not self._verify_recipe_against_prompt():
                self._recipe.clean()
                self._create_flux_image_recipe()
                self._create_zonos_tts_narrator_recipe()

            logger.info("Video recipe creation completed successfully")
