"""Module to build video assembler recipes based on assets and defaults."""

from pathlib import Path
from logging_utils import logger

from ai_video_creator.utils import VideoCreatorPaths
from ai_video_creator.media_effects.effects_map import (
    AudioExtender,
)

from ai_video_creator.modules.narrator import NarratorRecipe, NarratorAssets
from ai_video_creator.modules.image import ImageRecipe, ImageAssets

from .video_assembler_recipe import (
    VideoAssemblerRecipe,
    VideoIntroRecipe,
    VideoEndingRecipe,
    VideoOverlayRecipe,
)


class VideoAssemblerRecipeBuilder:
    """Class to manage video effects creation and business logic."""

    def __init__(
        self,
        video_creator_paths: VideoCreatorPaths,
    ):
        """Initialize VideoAssemblerRecipeBuilder with story folder and chapter index."""

        self._paths = video_creator_paths

        logger.info(
            f"Initializing VideoAssemblerRecipeBuilder for story: {video_creator_paths.story_folder.name},"
            f" chapter: {video_creator_paths.chapter_index + 1}"
        )

        # Load separate narrator and image assets
        self.narrator_recipe = NarratorRecipe(video_creator_paths)
        self.narrator_assets = NarratorAssets(video_creator_paths)
        self.image_recipe = ImageRecipe(video_creator_paths)
        self.image_assets = ImageAssets(video_creator_paths)

        if not self.narrator_assets.is_complete() or not self.image_assets.is_complete():
            raise ValueError("Video assets are incomplete. Please ensure all required assets are present.")

        if not self.narrator_recipe.is_complete():
            raise ValueError("Narrator recipe is incomplete. Please ensure narrator data is present.")

        self.video_assembler_recipe = VideoAssemblerRecipe(video_creator_paths)

        # Only add default values if no effects were loaded
        if not self.video_assembler_recipe.is_complete():
            self._add_default_values()

        self.video_assembler_recipe.save_to_file()

        logger.debug("VideoAssemblerRecipeBuilder initialized.")

    def _synchronize_effects_with_assets(self):
        """Ensure video_effects lists have the same size as assets."""
        assets_size = len(self.narrator_assets.narrator_assets)
        logger.debug(f"Synchronizing effects with assets - target size: {assets_size}")

        self.video_assembler_recipe.match_size_to_target(assets_size)

        logger.debug(
            f"Synchronized narrator effects with narrator size: {self.video_assembler_recipe.len_narrator_effects()}"
        )

    def _add_default_values(self):
        """Add default values for video effects."""

        logger.info("Adding default effect values")

        self.video_assembler_recipe.clear()
        self._synchronize_effects_with_assets()

        if self.video_assembler_recipe.len_narrator_effects() > 0:
            self.video_assembler_recipe.add_narrator_effect(
                0,
                AudioExtender(seconds_to_extend_front=0.5, seconds_to_extend_back=1.5),
            )

            for index in range(1, self.video_assembler_recipe.len_narrator_effects()):
                self.video_assembler_recipe.add_narrator_effect(
                    index,
                    AudioExtender(seconds_to_extend_front=0, seconds_to_extend_back=1),
                )

        intro = VideoIntroRecipe(self._paths)

        image_data = self.image_recipe.recipes_data
        intro.skip = image_data[0].width < image_data[0].height if len(image_data) > 0 else False

        intro.intro_asset = VideoIntroRecipe.DEFAULT_INTRO_ASSET
        self.video_assembler_recipe.set_video_intro_recipe(intro)

        overlay = VideoOverlayRecipe(self._paths)
        overlay.overlay_asset = VideoOverlayRecipe.DEFAULT_OVERLAY_ASSET
        self.video_assembler_recipe.set_video_overlay_recipe(overlay)

        ending = VideoEndingRecipe(self._paths)
        ending.narrator_text_list = [
            "Thank you so much for watching! We hope to see you in the next episode.",
            "If you enjoyed this video, please like and subscribe for more content. Leave a comment below to let us know your thoughts.",
        ]
        ending.narrator_clone_voice = Path(self.narrator_recipe.narrator_data[0].clone_voice_path)
        ending.ending_overlay_start_narrator_index = 1
        ending.ending_overlay_asset = VideoEndingRecipe.DEFAULT_ENDING_OVERLAY_ASSET
        ending.ending_start_delay_seconds = 1.0
        self.video_assembler_recipe.set_video_ending_recipe(ending)

        logger.debug("Default effect values added successfully")
