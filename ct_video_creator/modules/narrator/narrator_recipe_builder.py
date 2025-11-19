"""
Narrator recipe builder for creating narrator recipes from prompts.
"""

from ct_logging import logger
from ct_video_creator.prompt import Prompt

from ct_video_creator.generators import ZonosTTSRecipe

from ct_video_creator.utils import VideoCreatorPaths

from .narrator_recipe import (
    NarratorRecipe,
    NarratorRecipeDefaultSettings,
)


class NarratorRecipeBuilder:
    """Narrator recipe builder for creating narrator recipes from stories."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize NarratorRecipeBuilder with recipe data."""

        self._paths = video_creator_paths
        story_folder = self._paths.story_folder

        logger.info(
            "Initializing NarratorRecipeBuilder for story:"
            f" {story_folder.name}, chapter: {self._paths.chapter_index + 1}"
        )

        self._chapter_prompt_path = self._paths.chapter_prompt_path

        # Load video prompt
        self._video_prompt = Prompt.load_from_json(self._chapter_prompt_path)

        self._recipe = None

    @property
    def recipe(self):
        """Get the current recipe."""
        return self._recipe

    def _verify_recipe_against_prompt(self) -> bool:
        """Verify the recipe against the prompt to ensure all required data is present."""
        logger.debug("Verifying narrator recipe against prompt data")

        if not self._recipe.narrator_data or len(self._recipe.narrator_data) != len(
            self._video_prompt
        ):
            return False

        return True

    def _create_zonos_tts_narrator_recipe(self, seed: int | None = None) -> None:
        """Create Zonos TTS narrator recipe."""
        logger.info(
            f"Creating Zonos TTS narrator recipes for {len(self._video_prompt)} prompts"
        )

        for prompt in self._video_prompt:
            recipe = ZonosTTSRecipe(
                prompt=prompt.narrator,
                clone_voice_path=NarratorRecipeDefaultSettings.NARRATOR_VOICE,
                seed=seed,
            )
            self._recipe.add_narrator_data(recipe)

        logger.info(
            f"Successfully created {len(self._video_prompt)} Zonos TTS narrator recipes"
        )

    def create_narrator_recipes(self) -> None:
        """Create narrator recipe from story folder and chapter prompt index."""

        logger.info("Starting narrator recipe creation process")

        self._recipe = NarratorRecipe(self._paths)

        if not self._verify_recipe_against_prompt():
            self._recipe.clean()
            self._create_zonos_tts_narrator_recipe()

        logger.info("Narrator recipe creation completed successfully")
