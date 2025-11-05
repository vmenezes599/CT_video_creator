"""This module manages the creation of video assets for a given story chapter."""

import json
from pathlib import Path

from logging_utils import logger
from ai_video_creator.utils.video_creator_paths import VideoCreatorPaths
from ai_video_creator.utils import ensure_collection_index_exists, backup_file_to_old


class VideoAssemblerAssets:
    """Class to manage video assets data and persistence only."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize VideoAssets with file path and expected scene count."""
        self._paths = video_creator_paths
        self.asset_file_path = self._paths.video_assembler_asset_file
        self.asset_file_parent = self.asset_file_path.parent

        self.final_sub_videos: list[Path] = []
        self.video_ending: Path = None

        self._load_assets_from_file()

    def _load_assets_from_file(self):
        """Load assets from JSON file with security validation."""
        try:
            logger.debug(f"Loading video assets from: {self.asset_file_path.name}")
            with open(self.asset_file_path, "r", encoding="utf-8") as file:
                data: dict = json.load(file)

            assets = data.get("assets", [])
            ensure_collection_index_exists(self.final_sub_videos, len(assets) - 1)

            # Load assets from the "assets" array format
            for index, asset in enumerate(assets):

                # Load video asset with security validation
                video_value = asset.get("video_asset")
                video_value_path = Path(video_value) if video_value else None
                self.final_sub_videos[index] = (
                    self._paths.unmask_asset_path(video_value_path) if video_value_path else None
                )

            video_ending_value = data.get("video_ending")
            if video_ending_value:
                self.video_ending = self._paths.unmask_asset_path(Path(video_ending_value))

            self.save_assets_to_file()

        except json.JSONDecodeError:
            logger.error(
                f"Error decoding JSON from {self.asset_file_path.name} - renaming to .old and starting with empty assets"
            )
            self.final_sub_videos = []

            # Back up the corrupted file before overwriting
            backup_file_to_old(self.asset_file_path)
            logger.debug(f"Backed up corrupted file to: {self.asset_file_path.name}.old")

            # Create a new empty file
            self.save_assets_to_file()

        except FileNotFoundError:
            logger.debug(f"Asset file not found: {self.asset_file_path.name} - starting with empty assets")
            self.final_sub_videos = []

    def save_assets_to_file(self) -> None:
        """Save the current state of the video assets to a file with relative paths."""
        try:
            with open(self.asset_file_path, "w", encoding="utf-8") as file:
                assets = []
                # Ensure both lists have the same length
                max_length = len(self.final_sub_videos)

                for i in range(max_length):
                    video_asset = self.final_sub_videos[i] if i < len(self.final_sub_videos) else None

                    # Convert paths to relative paths for storage
                    video_asset_relative = None
                    if video_asset:
                        video_asset_relative = str(self._paths.mask_asset_path(video_asset))

                    videos = {
                        "index": i + 1,
                        "video_asset": video_asset_relative,
                    }

                    assets.append(videos)

                data = {
                    "video_ending": (
                        str(self._paths.mask_asset_path(self.video_ending)) if self.video_ending else None
                    ),
                    "assets": assets,
                }
                json.dump(data, file, indent=4)
            logger.trace(f"Assets saved with {len(assets)} scene assets")
        except IOError as e:
            logger.error(f"Error saving video assets to {self.asset_file_path.name}: {e}")

    def set_final_sub_video_video(self, scene_index: int, video_file_path: Path) -> None:
        """Set video file path for a specific scene with security validation."""
        try:
            ensure_collection_index_exists(self.final_sub_videos, scene_index)
            self.final_sub_videos[scene_index] = video_file_path
            logger.debug(f"Set video for scene {scene_index + 1}: {video_file_path.name}")
            self.save_assets_to_file()
        except ValueError as e:
            logger.error(f"Failed to set video for scene {scene_index + 1}: {e}")
            raise

    def set_video_ending(self, video_file_path: Path) -> None:
        """Set the video ending asset with security validation."""
        try:
            logger.debug(f"Set video ending: {video_file_path.name}")
            self.video_ending = video_file_path
            self.save_assets_to_file()
        except ValueError as e:
            logger.error(f"Failed to set video ending: {e}")
            raise

    def clear_scene_assets(self, scene_index: int) -> None:
        """Clear all assets for a specific scene."""
        ensure_collection_index_exists(self.final_sub_videos, scene_index)
        self.final_sub_videos[scene_index] = None
        logger.debug(f"Cleared all assets for scene {scene_index + 1}")

    def has_video(self, scene_index: int) -> bool:
        """Check if a scene has video asset."""
        if scene_index < 0 or scene_index >= len(self.final_sub_videos):
            return False
        video_asset = self.final_sub_videos[scene_index]
        return video_asset is not None and video_asset.exists() and video_asset.is_file()

    def get_missing_videos(self) -> list[int]:
        """Get a summary of missing videos per scene."""
        missing = []
        for i, _ in enumerate(self.final_sub_videos):
            if not self.has_video(i):
                missing.append(i)
        return missing

    def is_complete(self) -> bool:
        """Check if all scenes have video assets."""

        return len(self.get_missing_videos()) == 0

    def get_used_assets_list(self) -> list[Path]:
        """Get a list of all used video asset file paths."""
        used_assets = []
        for video in self.final_sub_videos:
            if video is not None and video.exists() and video.is_file():
                used_assets.append(video)

        # Include the video ending asset if it exists
        if self.video_ending is not None and self.video_ending.exists() and self.video_ending.is_file():
            used_assets.append(self.video_ending)

        return used_assets
