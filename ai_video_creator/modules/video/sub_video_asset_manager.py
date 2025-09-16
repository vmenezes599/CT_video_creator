"""This module manages the creation of video assets for a given story chapter."""

from pathlib import Path

from logging_utils import begin_file_logging, logger
from ai_video_creator.generators import IVideoGenerator
from ai_video_creator.utils import VideoCreatorPaths
from ai_video_creator.utils import ensure_collection_index_exists
from ai_video_creator.utils import concatenate_videos_remove_last_frame_except_last

from ai_video_creator.modules.narrator_and_image import NarratorAndImageAssets
from .sub_video_recipe import SubVideoRecipe
from .sub_video_assets import SubVideoAssets


class SubVideoAssetManager:
    """Class to manage video assets creation."""

    def __init__(self, story_folder: Path, chapter_index: int):
        """Initialize VideoAssetManager with story folder and chapter index."""

        logger.info(
            f"Initializing VideoAssetManager for story: {story_folder.name}, chapter: {chapter_index}"
        )

        self.story_folder = story_folder
        self.chapter_index = chapter_index
        self.output_file_prefix = f"chapter_{self.chapter_index+1:03}"

        self.__paths = VideoCreatorPaths(story_folder, chapter_index)
        self.__narrator_and_image_assets = NarratorAndImageAssets(
            self.__paths.narrator_and_image_asset_file
        )
        self.recipe = SubVideoRecipe(self.__paths.video_recipe_file)
        self.video_assets = SubVideoAssets(self.__paths.video_asset_file)

        # Ensure video_assets lists have the same size as recipe
        self._synchronize_assets_with_image_assets()

        logger.debug(
            f"VideoAssetManager initialized with {len(self.recipe.video_data)} scenes"
        )

    def _synchronize_assets_with_image_assets(self):
        """Ensure video_assets lists have the same size as recipe."""
        recipe_size = len(self.recipe.video_data)
        logger.debug(f"Synchronizing assets with recipe - target size: {recipe_size}")

        ensure_collection_index_exists(
            self.video_assets.assembled_sub_video, recipe_size - 1
        )
        ensure_collection_index_exists(
            self.video_assets.sub_video_assets, recipe_size - 1, []
        )

        logger.debug(
            f"Asset synchronization completed - video assets: {len(self.video_assets.assembled_sub_video)}"
        )

    def _set_next_recipe_media_path(
        self, scene_index: int, recipe_index: int, media_path: Path
    ) -> None:
        """Set the media path of the next recipe in the list, if it exists."""
        video_recipe_list = self.recipe.video_data[scene_index]
        next_recipe_index = recipe_index + 1
        if next_recipe_index < len(video_recipe_list):
            next_recipe = video_recipe_list[next_recipe_index]
            next_recipe.media_path = media_path
            logger.debug(
                f"Set media path for next recipe at scene {scene_index + 1},"
                f" current recipe {recipe_index + 1}, next recipe {next_recipe_index + 1}: {media_path.name}"
            )
            self.recipe.save_current_state()

    def _generate_sub_video_file_path(
        self, scene_index: int, recipe_index: int
    ) -> Path:
        """Generate a unique sub-video file path for a specific scene and recipe index."""
        return (
            self.__paths.videos_asset_folder
            / f"{self.output_file_prefix}_sub_video_{scene_index+1:03}_{recipe_index+1:02}.mp4"
        )

    def _generate_sub_videos_assets(self, scene_index: int) -> None:
        """Generate sub-videos assets for a specific scene."""
        try:
            logger.info(f"Generating video asset for scene {scene_index}")
            video_recipe_list = self.recipe.video_data[scene_index]

            for recipe_index, recipe in enumerate(video_recipe_list):
                if self.video_assets.has_sub_videos(scene_index, recipe_index):
                    logger.debug(
                        f"Sub-video {recipe_index + 1} already exists, skipping generation."
                    )
                    continue

                video_generator: IVideoGenerator = recipe.GENERATOR()
                sub_video_file_path = self._generate_sub_video_file_path(
                    scene_index, recipe_index
                )

                logger.debug(
                    f"Using video generator: {type(video_generator).__name__} for file: {sub_video_file_path.name}"
                )

                output_sub_video = video_generator.media_to_video(
                    recipe, sub_video_file_path
                )

                self._set_next_recipe_media_path(
                    scene_index, recipe_index, output_sub_video
                )

                self.video_assets.set_scene_sub_video(
                    scene_index, recipe_index, output_sub_video
                )
                self.video_assets.save_assets_to_file()

                logger.info(
                    f"Successfully generated sub video for scene {scene_index + 1}({recipe_index+1}/{len(video_recipe_list)}): {output_sub_video.name}"
                )

        except (IOError, OSError, RuntimeError) as e:
            logger.error(
                f"Failed to generate sub video for scene {scene_index+1}({recipe_index+1}/{len(video_recipe_list)}): {e}"
            )

    def _generate_video_file_path(self, scene_index: int) -> Path:
        """Generate a unique video file path for a specific scene."""
        return (
            self.__paths.videos_asset_folder
            / f"{self.output_file_prefix}_video_{scene_index+1:03}.mp4"
        )

    def _generate_video_asset(self, scene_index: int):
        """Generate assets for a specific scene."""
        try:
            logger.info(f"Generating video asset for scene {scene_index + 1}")

            self._generate_sub_videos_assets(scene_index)

            video_file_path = self._generate_video_file_path(scene_index)
            output_video = concatenate_videos_remove_last_frame_except_last(
                self.video_assets.sub_video_assets[scene_index], video_file_path
            )

            self.video_assets.set_scene_video(scene_index, output_video)
            self.video_assets.save_assets_to_file()
            logger.info(
                f"Successfully generated video for scene {scene_index + 1}: {output_video.name}"
            )

        except (IOError, OSError, RuntimeError) as e:
            logger.error(f"Failed to generate video for scene {scene_index + 1}: {e}")

    def generate_video_assets(self):
        """Generate a video from the image assets using ffmpeg."""
        with begin_file_logging(
            name="create_subvideos_from_subvideo_recipes",
            log_level="TRACE",
            base_folder=self.__paths.video_path,
        ):
            logger.info("Starting video asset generation process")

            if not self.__narrator_and_image_assets.is_complete():
                logger.error("Cannot generate videos - Scenes are missing image assets")
                return

            missing_videos = self.video_assets.get_missing_videos()

            logger.info(f"Found {len(missing_videos)} scenes missing video assets")
            logger.info(f"Total scenes requiring processing: {len(missing_videos)}")

            for scene_index in sorted(missing_videos):
                logger.info(f"Processing scene {scene_index + 1}...")
                self._generate_video_asset(scene_index)

            logger.info("Video asset generation process completed successfully")

    def clean_unused_assets(self):
        """Clean up video assets for a specific story folder."""

        logger.info("Starting video asset cleanup process")

        valid_video_assets = [
            asset
            for asset in self.video_assets.assembled_sub_video
            if asset is not None
        ]
        valid_sub_video_assets = [
            sub_asset
            for sublist in self.video_assets.sub_video_assets
            for sub_asset in sublist
            if sub_asset is not None
        ]
        assets_to_keep = set(valid_video_assets + valid_sub_video_assets)

        for file in self.__paths.videos_asset_folder.glob("*"):
            if file.is_file():
                if file in assets_to_keep:
                    continue
                file.unlink()
                logger.info(f"Deleted asset file: {file}")

        logger.info("Video asset cleanup process completed successfully")
