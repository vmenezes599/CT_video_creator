"""This module manages the creation of video assets for a given story chapter."""

import json
from pathlib import Path

from logging_utils import logger
from ai_video_creator.utils import ensure_collection_index_exists


class VideoAssemblerAssets:
    """Class to manage video assets data and persistence only."""

    def __init__(self, asset_file_path: Path):
        """Initialize VideoAssets with file path and expected scene count."""
        self.asset_file_parent = asset_file_path.parent
        self.asset_file_path = asset_file_path
        self.final_sub_videos: list[Path] = []
        self._load_assets_from_file()

    def __validate_asset_path(self, asset_path: Path) -> Path:
        """
        Validate and resolve asset path, ensuring it's absolute.
        Returns the validated path or raises ValueError for invalid paths.
        """
        try:
            # Require absolute paths only
            if not asset_path.is_absolute():
                raise ValueError(f"Path must be absolute: {asset_path}")

            # Resolve the absolute path
            resolved_path = asset_path.resolve(strict=False)

            # Basic security check: prevent path traversal attempts
            if ".." in str(asset_path):
                raise ValueError(f"Path traversal attempt detected: {asset_path}")

            return resolved_path
        except (FileNotFoundError, RuntimeError, OSError) as e:
            raise ValueError(f"Invalid path: {asset_path} - {e}") from e

    def _convert_from_relative_to_absolute(self, path: Path) -> Path:
        """Convert a possibly relative path to an absolute path based on the asset file parent directory."""
        if not path.is_absolute():
            path = (self.asset_file_parent / path).resolve(strict=False)

        # Now validate as absolute path
        validated_path = self.__validate_asset_path(path)
        return validated_path

    def _convert_from_absolute_to_relative(self, path: Path) -> Path:
        """Convert an absolute path to a relative path based on the asset file parent directory."""
        return path.relative_to(self.asset_file_parent)

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
                        self._convert_from_relative_to_absolute(video_value_path)
                    )

                self.save_assets_to_file()

        except json.JSONDecodeError:
            logger.error(
                f"Error decoding JSON from {self.asset_file_path.name} - renaming to .old and starting with empty assets"
            )
            # Rename corrupted file to .old for backup
            old_file_path = Path(str(self.asset_file_path) + ".old")
            if self.asset_file_path.exists():
                self.asset_file_path.rename(old_file_path)
            self.final_sub_videos = []
            self.sub_video_assets = []
            # Create a new empty file
            self.save_assets_to_file()

        except FileNotFoundError:
            logger.debug(
                f"Asset file not found: {self.asset_file_path.name} - starting with empty assets"
            )
            self.final_sub_videos = []
            self.sub_video_assets = []

    def save_assets_to_file(self) -> None:
        """Save the current state of the video assets to a file with relative paths."""
        try:
            with open(self.asset_file_path, "w", encoding="utf-8") as file:
                assets = []
                # Ensure both lists have the same length
                max_length = max(len(self.final_sub_videos), len(self.sub_video_assets))

                for i in range(max_length):
                    video_asset = (
                        self.final_sub_videos[i]
                        if i < len(self.final_sub_videos)
                        else None
                    )

                    # Convert paths to relative paths for storage
                    video_asset_relative = None
                    if video_asset is not None:
                        try:
                            video_asset_relative = str(
                                video_asset.relative_to(
                                    self.asset_file_parent.resolve()
                                )
                            )
                        except ValueError:
                            # Path is outside the directory, store as absolute
                            video_asset_relative = str(video_asset)

                    videos = {
                        "index": i + 1,
                        "video_asset": video_asset_relative,
                    }

                    assets.append(videos)

                data = {"assets": assets}
                json.dump(data, file, indent=4)
            logger.trace(f"Assets saved with {len(assets)} scene assets")
        except IOError as e:
            logger.error(
                f"Error saving video assets to {self.asset_file_path.name}: {e}"
            )

    def set_final_sub_video_video(
        self, scene_index: int, video_file_path: Path
    ) -> None:
        """Set video file path for a specific scene with security validation."""
        try:
            # Validate the path for security
            validated_path = self.__validate_asset_path(video_file_path)

            ensure_collection_index_exists(self.final_sub_videos, scene_index)
            ensure_collection_index_exists(self.sub_video_assets, scene_index, [])
            self.final_sub_videos[scene_index] = validated_path
            logger.debug(
                f"Set video for scene {scene_index + 1}: {validated_path.name}"
            )
            self.save_assets_to_file()
        except ValueError as e:
            logger.error(f"Failed to set video for scene {scene_index + 1}: {e}")
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
        return (
            video_asset is not None and video_asset.exists() and video_asset.is_file()
        )

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
