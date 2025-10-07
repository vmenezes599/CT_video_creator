"""
Video executor for create_video command.
"""

from pathlib import Path
from math import ceil

from logging_utils import begin_file_logging, logger

from ai_video_creator.generators import WanI2VRecipe
from ai_video_creator.modules.narrator import NarratorAssets
from ai_video_creator.modules.image import ImageAssets
from ai_video_creator.utils import VideoCreatorPaths
from ai_video_creator.prompt import Prompt
from ai_video_creator.utils import get_audio_duration

from .sub_video_recipe import SubVideoRecipe


class SubVideoRecipeBuilder:
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

        # Load separate narrator and image assets
        self.__narrator_assets = NarratorAssets(self.__paths.narrator_asset_file)
        self.__image_assets = ImageAssets(self.__paths.image_asset_file)
        self._recipe = None

        self._min_sub_videos = 3
        self._max_sub_videos = 5
        self._default_sub_video_duration_seconds = 5

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

    def _calculate_sub_videos_count(self, sub_video_index: int) -> int:
        """Calculate the number of sub-videos to generate per prompt."""

        # Handle case where narrator assets don't exist
        if (
            sub_video_index >= len(self.__narrator_assets.narrator_assets)
            or self.__narrator_assets.narrator_assets[sub_video_index] is None
        ):
            return self._min_sub_videos

        audio_duration = get_audio_duration(
            str(self.__narrator_assets.narrator_assets[sub_video_index])
        )

        sub_video_count = ceil(
            audio_duration / self._default_sub_video_duration_seconds
        )

        return max(sub_video_count, self._max_sub_videos)

    def _create_video_recipes(self, seed: int | None = None) -> None:
        """Create video recipe from story folder and chapter prompt index."""
        logger.info(
            f"Creating Wan video recipes for {len(self.__video_prompt)} prompts"
        )

        for i, prompt in enumerate(self.__video_prompt):
            # Get corresponding image asset if available, otherwise None
            sub_video_count = self._calculate_sub_videos_count(i)
            image_asset = (
                self.__image_assets.image_assets[i]
                if i < len(self.__image_assets.image_assets)
                else None
            )

            recipe_list = []
            recipe = self._create_wan_i2v_recipe(
                prompt=prompt.visual_description,
                color_match_image_asset=image_asset,
                image_asset=image_asset,
                seed=seed,
            )
            recipe_list.append(recipe)
            for _ in range(sub_video_count - 1):
                recipe = self._create_wan_i2v_recipe(seed=seed)
                recipe_list.append(recipe)

            self._recipe.add_video_data(
                recipe_list, {"helper_story_text": prompt.narrator}
            )

        logger.info(
            f"Successfully created {len(self.__video_prompt)} Wan video recipes"
        )

    def _create_wan_i2v_recipe(
        self,
        prompt: str = None,
        color_match_image_asset: Path = None,
        image_asset: Path | None = None,
        high_lora: list[str] | None = None,
        high_lora_strength: list[float] | None = None,
        low_lora: list[str] | None = None,
        low_lora_strength: list[float] | None = None,
        seed: int | None = None,
    ) -> None:
        """Create video recipe from story folder and chapter prompt index."""
        return WanI2VRecipe(
            prompt=prompt,
            high_lora=high_lora if high_lora else None,
            high_lora_strength=high_lora_strength if high_lora_strength else None,
            low_lora=low_lora if low_lora else None,
            low_lora_strength=low_lora_strength if low_lora_strength else None,
            media_path=str(image_asset) if image_asset else None,
            color_match_media_path=(
                str(color_match_image_asset) if color_match_image_asset else None
            ),
            seed=seed,
        )

    def create_video_recipe(self) -> None:
        """Create video recipe from story folder and chapter prompt index."""

        with begin_file_logging(
            name="create_sub_video_recipes_from_images",
            log_level="TRACE",
            base_folder=self.__paths.chapter_folder,
        ):
            logger.info("Starting video recipe creation process")

            self._recipe = SubVideoRecipe(self.__paths.sub_video_recipe_file)

            if not self._verify_recipe_against_prompt():
                self._recipe.clean()
                self._create_video_recipes()

            logger.info("Video recipe creation completed successfully")
