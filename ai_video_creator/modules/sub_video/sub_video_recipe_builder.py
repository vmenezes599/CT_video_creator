"""
Video executor for create_video command.
"""

from pathlib import Path
from math import ceil
from concurrent.futures import ThreadPoolExecutor, as_completed

from logging_utils import logger, begin_file_logging

from ai_video_creator.generators import WanI2VRecipe, SceneScriptGenerator
from ai_video_creator.modules.narrator import NarratorAssets
from ai_video_creator.modules.image import ImageAssets
from ai_video_creator.utils import VideoCreatorPaths
from ai_video_creator.prompt import Prompt
from ai_video_creator.utils import get_media_duration

from .sub_video_recipe import SubVideoRecipe


class SubVideoRecipeBuilder:
    """Video recipe for creating videos from stories."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize VideoRecipe with recipe data.

        Args:
            video_data: List of video data dictionaries
            seeds: List of seeds for each generation (None elements use default behavior)
        """
        self._paths = video_creator_paths
        story_folder = self._paths.story_folder

        logger.info(
            "Initializing VideoRecipeBuilder for story:"
            f" {story_folder.name}, chapter: {self._paths.chapter_index + 1}"
        )

        self.__chapter_prompt_path = self._paths.chapter_prompt_path

        # Load video prompt
        self.__video_prompt = Prompt.load_from_json(self.__chapter_prompt_path)

        # Load separate narrator and image assets
        self.__narrator_assets = NarratorAssets(video_creator_paths)
        self.__image_assets = ImageAssets(video_creator_paths)
        self._recipe = None

        self._min_sub_videos = 3
        self._max_sub_videos = 8
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

        # Check if narrator asset exists and is not None
        if (
            sub_video_index >= len(self.__narrator_assets.narrator_assets)
            or self.__narrator_assets.narrator_assets[sub_video_index] is None
        ):
            # Return default count if no narrator asset is available
            return self._min_sub_videos

        audio_duration = get_media_duration(
            str(self.__narrator_assets.narrator_assets[sub_video_index])
        )

        sub_video_count = ceil(
            audio_duration / self._default_sub_video_duration_seconds
        )

        return max(self._min_sub_videos, min(sub_video_count, self._max_sub_videos))

    def _run_script_generator_parallel(self):
        """Run the scene script generator in parallel for all prompts."""

        def _generate_scene_script(i: int, prompt):
            """Helper function to generate scene script for a single prompt."""
            sub_video_count = self._calculate_sub_videos_count(i)
            image_asset = (
                self.__image_assets.image_assets[i]
                if i < len(self.__image_assets.image_assets)
                else None
            )

            previous_prompt = self.__video_prompt[i - 1] if i > 0 else None

            scene_script_generator = SceneScriptGenerator(
                scene_initial_image=image_asset,
                number_of_subdivisions=sub_video_count,
                sub_video_prompt=prompt,
                previous_sub_video_prompt=previous_prompt,
            )

            return i, scene_script_generator.generate_scenes_script()

        results_dict = {}
        with begin_file_logging(
            "run_script_generator_parallel",
            self._paths.video_chapter_folder,
            log_level="TRACE",
        ):

            with ThreadPoolExecutor() as executor:
                # Submit all tasks
                futures = {
                    executor.submit(_generate_scene_script, i, prompt): i
                    for i, prompt in enumerate(self.__video_prompt)
                }

                # Collect results as they complete
                for future in as_completed(futures):
                    i, scene_scripts = future.result()
                    results_dict[i] = scene_scripts
                    logger.debug(f"Completed scene script generation for prompt {i}")

            # Return results in original order
            results = [results_dict[i] for i in range(len(self.__video_prompt))]

        return results

    def _create_video_recipes(self, seed: int | None = None) -> None:
        """Create video recipe from story folder and chapter prompt index."""
        logger.info(
            f"Creating Wan video recipes for {len(self.__video_prompt)} prompts"
        )

        scene_scripts_results = self._run_script_generator_parallel()

        for i, prompt in enumerate(self.__video_prompt):
            # Get corresponding image asset if available, otherwise None
            sub_video_count = self._calculate_sub_videos_count(i)
            image_asset = (
                self.__image_assets.image_assets[i]
                if i < len(self.__image_assets.image_assets)
                else None
            )

            scene_scripts = scene_scripts_results[i]

            recipe_list: list[WanI2VRecipe] = []
            recipe = self._create_wan_i2v_recipe(
                prompt=scene_scripts[0],
                color_match_image_asset=image_asset,
                image_asset=image_asset,
                seed=seed,
            )
            recipe_list.append(recipe)
            for j in range(sub_video_count - 1):
                recipe = self._create_wan_i2v_recipe(
                    prompt=scene_scripts[1 + j],
                    seed=seed,
                    color_match_image_asset=image_asset,
                )
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

        logger.info("Starting video recipe creation process")

        self._recipe = SubVideoRecipe(self._paths)

        if not self._verify_recipe_against_prompt():
            self._recipe.clean()
            self._create_video_recipes()

        logger.info("Video recipe creation completed successfully")
