"""This module manages the creation of video assets for a given story chapter."""

import json
from pathlib import Path

from logging_utils import begin_file_logging, logger
from ai_video_creator.generators import IVideoGenerator
from ai_video_creator.utils.video_creator_paths import VideoCreatorPaths
from ai_video_creator.utils.utils import ensure_collection_index_exists

from .video_recipe import VideoRecipeFile
from .narrator_and_image_asset_manager import NarratorAndImageAssetsFile


class VideoAssetsFile:
    """Class to manage video assets data and persistence only."""

    def __init__(self, asset_file_path: Path):
        """Initialize VideoAssets with file path and expected scene count."""
        self.asset_file_path = asset_file_path
        self.video_assets: list[Path] = []
        self.sub_video_assets: list[list[Path]] = []
        self._load_assets_from_file()

    def _load_assets_from_file(self):
        """Load assets from JSON file."""
        try:
            logger.debug(f"Loading video assets from: {self.asset_file_path.name}")
            with open(self.asset_file_path, "r", encoding="utf-8") as file:
                data: dict = json.load(file)

                assets = data.get("assets", [])
                ensure_collection_index_exists(self.video_assets, len(assets) - 1)
                ensure_collection_index_exists(
                    self.sub_video_assets, len(assets) - 1, []
                )

                # Load assets from the "assets" array format
                for index, asset in enumerate(assets):

                    # Load video asset, skip None/empty values
                    video_value = asset.get("video_asset")
                    if video_value is not None and video_value != "":
                        self.video_assets[index] = Path(video_value)
                    else:
                        self.video_assets[index] = None

                    sub_video_assets = asset.get("sub_video_assets", [])
                    for sub_video in sub_video_assets:
                        if sub_video is not None and sub_video != "":
                            self.sub_video_assets[index].append(Path(sub_video))
                        else:
                            self.sub_video_assets[index].append(None)

                self.save_assets_to_file()

        except json.JSONDecodeError:
            logger.error(
                f"Error decoding JSON from {self.asset_file_path.name} - renaming to .old and starting with empty assets"
            )
            # Rename corrupted file to .old for backup
            old_file_path = Path(str(self.asset_file_path) + ".old")
            if self.asset_file_path.exists():
                self.asset_file_path.rename(old_file_path)
            self.video_assets = []
            self.sub_video_assets = []
            # Create a new empty file
            self.save_assets_to_file()

        except FileNotFoundError:
            logger.debug(
                f"Asset file not found: {self.asset_file_path.name} - starting with empty assets"
            )
            self.video_assets = []
            self.sub_video_assets = []

    def save_assets_to_file(self) -> None:
        """Save the current state of the video assets to a file."""
        try:
            with open(self.asset_file_path, "w", encoding="utf-8") as file:
                assets = []
                for i, (video_asset, sub_video_assets) in enumerate(
                    zip(self.video_assets, self.sub_video_assets)
                ):
                    videos = {
                        "index": i + 1,
                        "video_asset": str(video_asset) if video_asset else None,
                        "sub_video_assets": [
                            (str(sub_video_asset) if sub_video_asset else None)
                            for sub_video_asset in sub_video_assets
                            if sub_video_asset is not None and sub_video_assets != []
                        ],
                    }

                    assets.append(videos)

                data = {"assets": assets}
                json.dump(data, file, indent=4)
            logger.trace(f"Assets saved with {len(assets)} scene assets")
        except IOError as e:
            logger.error(
                f"Error saving video assets to {self.asset_file_path.name}: {e}"
            )

    def set_scene_video(self, scene_index: int, video_file_path: Path) -> None:
        """Set video file path for a specific scene."""
        ensure_collection_index_exists(self.video_assets, scene_index)
        ensure_collection_index_exists(self.sub_video_assets, scene_index, [])
        self.video_assets[scene_index] = video_file_path
        logger.debug(f"Set video for scene {scene_index}: {video_file_path.name}")

    def set_scene_sub_video(
        self, scene_index: int, sub_video_index: int, sub_video_file_path: Path
    ) -> None:
        """Append a sub-video file path for a specific scene."""
        ensure_collection_index_exists(self.sub_video_assets, scene_index, [])
        ensure_collection_index_exists(
            self.sub_video_assets[scene_index], sub_video_index
        )
        self.sub_video_assets[scene_index][sub_video_index] = sub_video_file_path
        logger.debug(
            f"Appended sub-video for scene {scene_index}: {sub_video_file_path.name}"
        )

    def clear_scene_assets(self, scene_index: int) -> None:
        """Clear all assets for a specific scene."""
        ensure_collection_index_exists(self.video_assets, scene_index)
        self.video_assets[scene_index] = None
        logger.debug(f"Cleared all assets for scene {scene_index}")

    def has_video(self, scene_index: int) -> bool:
        """Check if a scene has video asset."""
        if scene_index < 0 or scene_index >= len(self.video_assets):
            return False
        video_asset = self.video_assets[scene_index]
        return (
            video_asset is not None and video_asset.exists() and video_asset.is_file()
        )

    def has_sub_videos(self, scene_index: int, sub_scene_index: int) -> bool:
        """Check if a scene has sub-video assets."""
        if scene_index < 0 or scene_index >= len(self.sub_video_assets):
            return False
        if sub_scene_index < 0 or sub_scene_index >= len(
            self.sub_video_assets[scene_index]
        ):
            return False

        sub_video = self.sub_video_assets[scene_index][sub_scene_index]
        return sub_video is not None and sub_video.exists() and sub_video.is_file()

    def get_missing_videos(self) -> list[int]:
        """Get a summary of missing videos per scene."""
        missing = []
        for i, _ in enumerate(self.video_assets):
            if not self.has_video(i):
                missing.append(i)
        return missing


class VideoAssetManager:
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
        self.__narrator_and_image_assets = NarratorAndImageAssetsFile(
            self.__paths.narrator_and_image_asset_file
        )
        self.recipe = VideoRecipeFile(self.__paths.video_recipe_file)
        self.video_assets = VideoAssetsFile(self.__paths.video_asset_file)

        # Ensure video_assets lists have the same size as recipe
        self._synchronize_assets_with_image_assets()

        logger.debug(
            f"VideoAssetManager initialized with {len(self.recipe.video_data)} scenes"
        )

    def _synchronize_assets_with_image_assets(self):
        """Ensure video_assets lists have the same size as recipe."""
        recipe_size = len(self.recipe.video_data)
        logger.debug(f"Synchronizing assets with recipe - target size: {recipe_size}")

        ensure_collection_index_exists(self.video_assets.video_assets, recipe_size - 1)
        ensure_collection_index_exists(
            self.video_assets.sub_video_assets, recipe_size - 1, []
        )

        logger.debug(
            f"Asset synchronization completed - video assets: {len(self.video_assets.video_assets)}"
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
                f"Set media path for next recipe at scene {scene_index}, recipe {next_recipe_index}: {media_path.name}"
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
                        f"Sub-video {recipe_index} already exists, skipping generation."
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
                    f"Successfully generated video for scene {scene_index}: {output_sub_video.name}"
                )

        except (IOError, OSError, RuntimeError) as e:
            logger.error(f"Failed to generate video for scene {scene_index}: {e}")

    def _generate_video_file_path(self, scene_index: int) -> Path:
        """Generate a unique video file path for a specific scene."""
        return (
            self.__paths.videos_asset_folder
            / f"{self.output_file_prefix}_video_{scene_index+1:03}.mp4"
        )

    def _generate_video_asset(self, scene_index: int):
        """Generate assets for a specific scene."""
        try:
            logger.info(f"Generating video asset for scene {scene_index}")

            self._generate_sub_videos_assets(scene_index)

            video_file_path = self._generate_video_file_path(scene_index)
            # output_video = self._concatenate_sub_videos(scene_index, video_file_path)

            output_video = Path(
                f"mock_concatenate_sub_video/{video_file_path.stem}.mock.mp4"
            )

            self.video_assets.set_scene_video(scene_index, output_video)
            self.video_assets.save_assets_to_file()
            logger.info(
                f"Successfully generated video for scene {scene_index}: {output_video.name}"
            )

        except (IOError, OSError, RuntimeError) as e:
            logger.error(f"Failed to generate video for scene {scene_index}: {e}")

    def generate_video_assets(self):
        """Generate a video from the image assets using ffmpeg."""
        with begin_file_logging(
            name="VideoAssetManager",
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
                logger.info(f"Processing scene {scene_index}...")
                self._generate_video_asset(scene_index)

            logger.info("Video asset generation process completed successfully")

    def clean_unused_assets(self):
        """Clean up video assets for a specific story folder."""

        logger.info("Starting video asset cleanup process")

        valid_video_assets = [
            asset for asset in self.video_assets.video_assets if asset is not None
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
