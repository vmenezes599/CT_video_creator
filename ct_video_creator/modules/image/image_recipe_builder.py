"""
Image recipe builder for creating image recipes from prompts.
"""

from ct_logging import logger
from ct_video_creator.prompt import Prompt

from ct_video_creator.generators import FluxImageRecipe

from ct_video_creator.utils import VideoCreatorPaths, AspectRatios

from .image_recipe import ImageRecipe


class ImageRecipeBuilder:
    """Image recipe builder for creating image recipes from stories."""

    DEFAULT_WIDTH = 848
    DEFAULT_HEIGHT = 480

    def __init__(self, video_creator_paths: VideoCreatorPaths, aspect_ratio: AspectRatios):
        """Initialize ImageRecipeBuilder with recipe data."""
        self._paths = video_creator_paths
        self._aspect_ratio = aspect_ratio
        story_folder = self._paths.story_folder

        logger.info(
            "Initializing ImageRecipeBuilder for story:"
            f" {story_folder.name}, chapter: {self._paths.chapter_index + 1}"
        )

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

        if not self._recipe.recipes_data or len(self._recipe.recipes_data) != len(self.__video_prompt):
            return False

        return True

    def _get_resolution_from_aspect_ratio(self) -> tuple[int, int]:
        """Get image resolution based on the specified aspect ratio."""
        ratio = self._aspect_ratio
        x, y = ratio.value
        if x > y:
            width = self.DEFAULT_WIDTH
            height = self.DEFAULT_HEIGHT
        else:
            width = self.DEFAULT_HEIGHT
            height = self.DEFAULT_WIDTH
        return width, height

    def _create_flux_image_recipe(self, seed: int | None = None) -> None:
        """Create video recipe from story folder and chapter prompt index."""
        logger.info(f"Creating Flux image recipes for {len(self.__video_prompt)} prompts")

        for prompt in self.__video_prompt:
            width, height = self._get_resolution_from_aspect_ratio()
            recipe = FluxImageRecipe(prompt=prompt.visual_prompt, seed=seed, width=width, height=height)
            self._recipe.add_image_data(recipe, {"helper_story_text": prompt.narrator})

        logger.info(f"Successfully created {len(self.__video_prompt)} Flux image recipes")

    def create_image_recipes(self) -> None:
        """Create image recipe from story folder and chapter prompt index."""

        logger.info("Starting image recipe creation process")

        self._recipe = ImageRecipe(self._paths)

        if not self._verify_recipe_against_prompt():
            self._recipe.clean()
            self._create_flux_image_recipe()

        logger.info("Image recipe creation completed successfully")
