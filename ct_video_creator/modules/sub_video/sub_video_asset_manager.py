"""This module manages the creation of video assets for a given story chapter."""

from pathlib import Path

from ct_logging import logger
from ct_video_creator.generators import IVideoGenerator, FlorenceGenerator
from ct_video_creator.utils import (
    VideoCreatorPaths,
    ensure_collection_index_exists,
    concatenate_videos_remove_last_frame_except_last,
    extract_video_last_frame,
)

from ct_video_creator.modules.narrator import NarratorAssets
from ct_video_creator.modules.image import ImageAssets
from .sub_video_recipe import SubVideoRecipe
from .sub_video_assets import SubVideoAssets


class SubVideoAssetManager:
    """Class to manage video assets creation."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize VideoAssetManager with story folder and chapter index."""
        self._paths = video_creator_paths
        story_folder = self._paths.story_folder

        logger.info(
            f"Initializing VideoAssetManager for story: {story_folder.name}, chapter: {self._paths.chapter_index + 1}"
        )

        self.story_folder = story_folder
        self.chapter_index = self._paths.chapter_index
        self.output_file_prefix = f"chapter_{self.chapter_index+1:03}"

        # Load separate narrator and image assets
        self.__narrator_assets = NarratorAssets(video_creator_paths)
        self.__image_assets = ImageAssets(video_creator_paths)
        self.recipe = SubVideoRecipe(self._paths)
        self.video_assets = SubVideoAssets(video_creator_paths)

        # Ensure video_assets lists have the same size as recipe
        self._synchronize_assets_with_image_assets()

        logger.debug(f"VideoAssetManager initialized with {len(self.recipe.video_data)} scenes")

    def _synchronize_assets_with_image_assets(self):
        """Ensure video_assets lists have the same size as recipe."""
        recipe_size = len(self.recipe.video_data)
        logger.debug(f"Synchronizing assets with recipe - target size: {recipe_size}")

        ensure_collection_index_exists(self.video_assets.assembled_sub_videos, recipe_size - 1)
        ensure_collection_index_exists(self.video_assets.sub_video_assets, recipe_size - 1, [])

        logger.debug(f"Asset synchronization completed - video assets: {len(self.video_assets.assembled_sub_videos)}")

    def _set_next_recipe_media_path_and_color_match(
        self, scene_index: int, recipe_index: int, media_path: Path
    ) -> None:
        """Set the media path of the next recipe in the list, if it exists."""
        video_recipe_list = self.recipe.video_data[scene_index]
        next_recipe_index = recipe_index + 1
        if next_recipe_index < len(video_recipe_list):
            next_recipe = video_recipe_list[next_recipe_index]
            next_recipe.media_path = str(media_path)
            logger.debug(
                f"Set media path for next recipe at scene {scene_index + 1},"
                f" current recipe {recipe_index + 1}, next recipe {next_recipe_index + 1}: {media_path.name}"
            )
            self.recipe.save_current_state()

    def _generate_and_set_next_recipe_prompt_if_empty(
        self, scene_index: int, recipe_index: int, sub_video_path: Path
    ) -> None:
        """Set the prompt of the next recipe in the list, if it exists."""
        video_recipe_list = self.recipe.video_data[scene_index]
        next_recipe_index = recipe_index + 1
        if next_recipe_index < len(video_recipe_list):
            next_recipe = video_recipe_list[next_recipe_index]
            if next_recipe.prompt:
                return
            next_recipe.prompt = FlorenceGenerator().generate_description(sub_video_path)
            logger.debug(
                f"Set prompt for next recipe at scene {scene_index + 1},"
                f" current recipe {recipe_index + 1}, next recipe {next_recipe_index + 1}: {next_recipe.prompt}"
            )
            self.recipe.save_current_state()

    def _generate_sub_video_file_path(self, scene_index: int, recipe_index: int) -> Path:
        """Generate a unique sub-video file path for a specific scene and recipe index."""
        return (
            self._paths.sub_videos_asset_folder
            / f"{self.output_file_prefix}_sub_video_{scene_index+1:03}_{recipe_index+1:02}.mp4"
        )

    def _generate_sub_videos_assets(self, scene_index: int) -> None:
        """Generate sub-videos assets for a specific scene."""
        video_recipe_list = self.recipe.video_data[scene_index]
        recipe_index = 0
        try:

            for recipe_index, recipe in enumerate(video_recipe_list):
                if self.video_assets.has_sub_videos(scene_index, recipe_index):
                    logger.debug(f"Sub-video {recipe_index + 1} already exists, skipping generation.")
                    continue

                logger.info(
                    f"Generating sub video asset for scene {scene_index + 1}({recipe_index+1}/{len(video_recipe_list)})"
                )

                video_generator: IVideoGenerator = recipe.GENERATOR_TYPE()
                sub_video_file_path = self._generate_sub_video_file_path(scene_index, recipe_index)

                logger.debug(
                    f"Using video generator: {type(video_generator).__name__} for file: {sub_video_file_path.name}"
                )

                output_sub_video = video_generator.generate_video(recipe, sub_video_file_path)

                video_last_frame = extract_video_last_frame(output_sub_video, self._paths.image_asset_folder)

                self._set_next_recipe_media_path_and_color_match(scene_index, recipe_index, video_last_frame)

                self._generate_and_set_next_recipe_prompt_if_empty(scene_index, recipe_index, video_last_frame)

                self.video_assets.set_scene_sub_video(scene_index, recipe_index, output_sub_video)

                logger.info(
                    f"Successfully generated sub video for scene {scene_index + 1}({recipe_index+1}/{len(video_recipe_list)}): {output_sub_video.name}"
                )

        except (IOError, OSError, RuntimeError) as e:
            logger.error(
                f"Failed to generate sub video for scene {scene_index+1}({recipe_index+1}/{len(video_recipe_list)}): {e}"
            )

    def _generate_video_file_path(self, scene_index: int) -> Path:
        """Generate a unique video file path for a specific scene."""
        return self._paths.sub_videos_asset_folder / f"{self.output_file_prefix}_video_{scene_index+1:03}.mp4"

    def _generate_video_asset(self, scene_index: int):
        """Generate assets for a specific scene."""
        try:
            logger.info(f"Generating video asset for scene {scene_index + 1}")

            self._generate_sub_videos_assets(scene_index)

            video_file_path = self._generate_video_file_path(scene_index)
            sub_videos_filtered: list[str | Path] = [v for v in self.video_assets.sub_video_assets[scene_index] if v is not None]
            output_video = concatenate_videos_remove_last_frame_except_last(
                sub_videos_filtered, video_file_path
            )

            self.video_assets.set_scene_video(scene_index, output_video)
            logger.info(f"Successfully generated video for scene {scene_index + 1}: {output_video.name}")

        except (IOError, OSError, RuntimeError) as e:
            logger.error(f"Failed to generate video for scene {scene_index + 1}: {e}")

    def generate_video_assets(self):
        """Generate a video from the image assets using ffmpeg."""

        logger.info("Starting video asset generation process")

        if not self.__narrator_assets.is_complete() or not self.__image_assets.is_complete():
            logger.error("Cannot generate videos - Some scenes are missing narrator or image assets")
            return

        missing_videos = self.video_assets.get_missing_videos()

        logger.info(f"Found {len(missing_videos)} scenes missing video assets")
        logger.info(f"Total scenes requiring processing: {len(missing_videos)}")

        for scene_index in sorted(missing_videos):
            logger.info(f"Processing scene {scene_index + 1}...")
            self._generate_video_asset(scene_index)

        logger.info("Video asset generation process completed successfully")
