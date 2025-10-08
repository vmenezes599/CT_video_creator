"""
Image recipe builder for creating image recipes from prompts.
"""

from pathlib import Path

from logging_utils import logger
from ai_video_creator.prompt import Prompt

from ai_video_creator.generators import FluxImageRecipe

from ai_video_creator.utils import VideoCreatorPaths

from .image_recipe import ImageRecipe


class ImageRecipeBuilder:
    """Image recipe builder for creating image recipes from stories."""

    def __init__(self, story_folder: Path, chapter_prompt_index: int):
        """Initialize ImageRecipeBuilder with recipe data."""
        logger.info(
            "Initializing ImageRecipeBuilder for story:"
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
        logger.debug("Verifying image recipe against prompt data")

        if not self._recipe.image_data or len(self._recipe.image_data) != len(
            self.__video_prompt
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
            self._recipe.add_image_data(recipe, {"helper_story_text": prompt.narrator})

        logger.info(
            f"Successfully created {len(self.__video_prompt)} Flux image recipes"
        )

    def create_image_recipes(self) -> None:
        """Create image recipe from story folder and chapter prompt index."""

        
        logger.info("Starting image recipe creation process")

        # Create image recipe file path
        image_recipe_file = self._paths.image_recipe_file

        self._recipe = ImageRecipe(image_recipe_file)

        if not self._verify_recipe_against_prompt():
            self._recipe.clean()
            self._create_flux_image_recipe()

        logger.info("Image recipe creation completed successfully")
