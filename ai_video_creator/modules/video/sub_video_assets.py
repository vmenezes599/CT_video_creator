"""This module manages the creation of video assets for a given story chapter."""

import json
from pathlib import Path

from logging_utils import logger
from ai_video_creator.utils import ensure_collection_index_exists


class SubVideoAssets:
    """Class to manage video assets data and persistence only."""

    def __init__(self, asset_file_path: Path):
        """Initialize VideoAssets with file path and expected scene count."""
        self.asset_file_parent = asset_file_path.parent.resolve()
        self.asset_file_path = asset_file_path
        self.assembled_sub_videos: list[Path] = []
        self.sub_video_assets: list[list[Path]] = []

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
                ensure_collection_index_exists(
                    self.assembled_sub_videos, len(assets) - 1
                )
                ensure_collection_index_exists(
                    self.sub_video_assets, len(assets) - 1, []
                )

                # Load assets from the "assets" array format
                for index, asset in enumerate(assets):

                    # Load video asset with security validation
                    video_value = asset.get("video_asset")
                    assembled_video_path = Path(video_value) if video_value else None
                    self.assembled_sub_videos[index] = (
                        self._convert_from_relative_to_absolute(assembled_video_path)
                        if assembled_video_path
                        else None
                    )

                    sub_video_assets = asset.get("sub_video_assets", [])
                    for sub_video in sub_video_assets:
                        if sub_video is not None and sub_video != "":
                            sub_video_path = Path(sub_video)
                            self.sub_video_assets[index].append(
                                self._convert_from_relative_to_absolute(sub_video_path)
                                if sub_video_path
                                else None
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
            self.assembled_sub_videos = []
            self.sub_video_assets = []
            # Create a new empty file
            self.save_assets_to_file()

        except FileNotFoundError:
            logger.debug(
                f"Asset file not found: {self.asset_file_path.name} - starting with empty assets"
            )
            self.assembled_sub_videos = []
            self.sub_video_assets = []

    def save_assets_to_file(self) -> None:
        """Save the current state of the video assets to a file with relative paths."""
        try:
            with open(self.asset_file_path, "w", encoding="utf-8") as file:
                assets = []
                # Ensure both lists have the same length
                max_length = max(
                    len(self.assembled_sub_videos), len(self.sub_video_assets)
                )

                for i in range(max_length):
                    video_asset = (
                        self.assembled_sub_videos[i]
                        if i < len(self.assembled_sub_videos)
                        else None
                    )
                    sub_video_assets = (
                        self.sub_video_assets[i]
                        if i < len(self.sub_video_assets)
                        else []
                    )

                    # Convert paths to relative paths for storage
                    video_asset_relative = None
                    if video_asset is not None:
                        video_asset_relative = str(
                            self._convert_from_absolute_to_relative(video_asset)
                        )

                    sub_video_assets_relative = []
                    for sub_video_asset in sub_video_assets:
                        if sub_video_asset is not None:
                            sub_video_assets_relative.append(
                                str(
                                    self._convert_from_absolute_to_relative(
                                        sub_video_asset
                                    )
                                )
                            )
                        else:
                            sub_video_assets_relative.append(None)

                    videos = {
                        "index": i + 1,
                        "video_asset": video_asset_relative,
                        "sub_video_assets": sub_video_assets_relative,
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
        """Set video file path for a specific scene with security validation."""
        try:
            # Validate the path for security
            validated_path = self.__validate_asset_path(video_file_path)

            ensure_collection_index_exists(self.assembled_sub_videos, scene_index)
            ensure_collection_index_exists(self.sub_video_assets, scene_index, [])
            self.assembled_sub_videos[scene_index] = validated_path
            self.save_assets_to_file()
            logger.debug(
                f"Set video for scene {scene_index + 1}: {validated_path.name}"
            )
        except ValueError as e:
            logger.error(f"Failed to set video for scene {scene_index + 1}: {e}")
            raise

    def set_scene_sub_video(
        self, scene_index: int, sub_video_index: int, sub_video_file_path: Path
    ) -> None:
        """Append a sub-video file path for a specific scene with security validation."""
        try:
            # Validate the path for security
            validated_path = self.__validate_asset_path(sub_video_file_path)

            ensure_collection_index_exists(self.sub_video_assets, scene_index, [])
            ensure_collection_index_exists(
                self.sub_video_assets[scene_index], sub_video_index
            )
            self.sub_video_assets[scene_index][sub_video_index] = validated_path
            self.save_assets_to_file()
            logger.debug(
                f"Set sub-video for scene {scene_index + 1}: {validated_path.name}"
            )
        except ValueError as e:
            logger.error(f"Failed to set sub-video for scene {scene_index + 1}: {e}")
            raise

    def clear_scene_assets(self, scene_index: int) -> None:
        """Clear all assets for a specific scene."""
        ensure_collection_index_exists(self.assembled_sub_videos, scene_index)
        self.assembled_sub_videos[scene_index] = None
        logger.debug(f"Cleared all assets for scene {scene_index + 1}")

    def has_video(self, scene_index: int) -> bool:
        """Check if a scene has video asset."""
        if scene_index < 0 or scene_index >= len(self.assembled_sub_videos):
            return False
        video_asset = self.assembled_sub_videos[scene_index]
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
        for i, _ in enumerate(self.assembled_sub_videos):
            if not self.has_video(i):
                missing.append(i)
        return missing

    def is_complete(self) -> bool:
        """Check if all scenes have video assets."""

        return len(self.get_missing_videos()) == 0
