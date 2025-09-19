"""This module manages the creation of video assets for a given story chapter."""

import json
from pathlib import Path

from logging_utils import logger
from ai_video_creator.utils import ensure_collection_index_exists


class SubVideoAssets:
    """Class to manage video assets data and persistence only."""

    def __init__(self, asset_file_path: Path):
        """Initialize VideoAssets with file path and expected scene count."""
        self.asset_file_path = asset_file_path
        self.assembled_sub_video: list[Path] = []
        self.sub_video_assets: list[list[Path]] = []
        self._load_assets_from_file()

    def _load_assets_from_file(self):
        """Load assets from JSON file."""
        try:
            logger.debug(f"Loading video assets from: {self.asset_file_path.name}")
            with open(self.asset_file_path, "r", encoding="utf-8") as file:
                data: dict = json.load(file)

                assets = data.get("assets", [])
                ensure_collection_index_exists(
                    self.assembled_sub_video, len(assets) - 1
                )
                ensure_collection_index_exists(
                    self.sub_video_assets, len(assets) - 1, []
                )

                # Load assets from the "assets" array format
                for index, asset in enumerate(assets):

                    # Load video asset, skip None/empty values
                    video_value = asset.get("video_asset")
                    if video_value is not None and video_value != "":
                        self.assembled_sub_video[index] = Path(video_value)
                    else:
                        self.assembled_sub_video[index] = None

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
            self.assembled_sub_video = []
            self.sub_video_assets = []
            # Create a new empty file
            self.save_assets_to_file()

        except FileNotFoundError:
            logger.debug(
                f"Asset file not found: {self.asset_file_path.name} - starting with empty assets"
            )
            self.assembled_sub_video = []
            self.sub_video_assets = []

    def save_assets_to_file(self) -> None:
        """Save the current state of the video assets to a file."""
        try:
            with open(self.asset_file_path, "w", encoding="utf-8") as file:
                assets = []
                # Ensure both lists have the same length
                max_length = max(len(self.assembled_sub_video), len(self.sub_video_assets))
                
                for i in range(max_length):
                    video_asset = self.assembled_sub_video[i] if i < len(self.assembled_sub_video) else None
                    sub_video_assets = self.sub_video_assets[i] if i < len(self.sub_video_assets) else []
                    
                    videos = {
                        "index": i + 1,
                        "video_asset": str(video_asset) if video_asset else None,
                        "sub_video_assets": [
                            str(sub_video_asset) if sub_video_asset else None
                            for sub_video_asset in sub_video_assets
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
        ensure_collection_index_exists(self.assembled_sub_video, scene_index)
        ensure_collection_index_exists(self.sub_video_assets, scene_index, [])
        self.assembled_sub_video[scene_index] = video_file_path
        logger.debug(f"Set video for scene {scene_index + 1}: {video_file_path.name}")

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
            f"Appended sub-video for scene {scene_index + 1}: {sub_video_file_path.name}"
        )

    def clear_scene_assets(self, scene_index: int) -> None:
        """Clear all assets for a specific scene."""
        ensure_collection_index_exists(self.assembled_sub_video, scene_index)
        self.assembled_sub_video[scene_index] = None
        logger.debug(f"Cleared all assets for scene {scene_index + 1}")

    def has_video(self, scene_index: int) -> bool:
        """Check if a scene has video asset."""
        if scene_index < 0 or scene_index >= len(self.assembled_sub_video):
            return False
        video_asset = self.assembled_sub_video[scene_index]
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
        for i, _ in enumerate(self.assembled_sub_video):
            if not self.has_video(i):
                missing.append(i)
        return missing

    def is_complete(self) -> bool:
        """Check if all scenes have video assets."""

        return len(self.get_missing_videos()) == 0
