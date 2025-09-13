"""
Video executor for create_video command.
"""

from pathlib import Path

from logging_utils import begin_file_logging, logger
from ai_video_creator.prompt import Prompt

from ai_video_creator.generators import WanVideoRecipe

from ai_video_creator.modules.narrator_and_image import NarratorAndImageAssets
from ai_video_creator.utils import VideoCreatorPaths
from .video_recipe import VideoRecipe


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
        self.__image_assets = NarratorAndImageAssets(
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

            self._recipe = VideoRecipe(self.__paths.video_recipe_file)

            if not self._verify_recipe_against_prompt():
                self._recipe.clean()
                self._create_video_recipes(sub_videos_length)

            logger.info("Video recipe creation completed successfully")
