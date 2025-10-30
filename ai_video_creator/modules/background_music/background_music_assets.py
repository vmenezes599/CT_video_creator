"""This module manages background music assets for story scenes."""

import json
from pathlib import Path

from logging_utils import logger
from ai_video_creator.utils.video_creator_paths import VideoCreatorPaths
from ai_video_creator.utils import ensure_collection_index_exists


class BackgroundMusicAssets:
    """Class to manage background music data and persistence only."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize BackgroundMusicAssets with file path and expected scene count."""
        self._paths = video_creator_paths

        self.asset_file_path = self._paths.background_music_asset_file
        self.asset_file_parent = self.asset_file_path.parent.resolve()

        self.background_music_assets: list[Path] = []

        self._load_assets_from_file()

    def _load_assets_from_file(self):
        """Load assets from JSON file with security validation."""
        try:
            logger.debug(f"Loading background music assets from: {self.asset_file_path.name}")
            with open(self.asset_file_path, "r", encoding="utf-8") as file:
                data: dict = json.load(file)

                assets = data.get("background_music_assets", [])
                ensure_collection_index_exists(self.background_music_assets, len(assets) - 1)

                # Load assets from the "assets" array format
                for index, asset in enumerate(assets):

                    # Load background music asset with security validation
                    assembled_background_music_path = Path(asset) if asset else None
                    self.background_music_assets[index] = (
                        self._paths.unmask_asset_path(assembled_background_music_path)
                        if assembled_background_music_path
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
            self.background_music_assets = []
            # Create a new empty file
            self.save_assets_to_file()

        except FileNotFoundError:
            logger.debug(f"Asset file not found: {self.asset_file_path.name} - starting with empty assets")
            self.background_music_assets = []

    def save_assets_to_file(self) -> None:
        """Save the current state of the background music assets to a file with relative paths."""
        try:
            with open(self.asset_file_path, "w", encoding="utf-8") as file:
                assets = []

                for index, background_music_asset in enumerate(self.background_music_assets, 1):

                    # Convert paths to relative paths for storage
                    background_music_asset_relative = None
                    if background_music_asset is not None:
                        background_music_asset_relative = str(self._paths.mask_asset_path(background_music_asset))

                    background_music_asset_data = {
                        "index": index,
                        "background_music_asset": background_music_asset_relative,
                    }

                    assets.append(background_music_asset_data)

                data = {"background_music_assets": assets}
                json.dump(data, file, indent=4)
            logger.trace(f"Assets saved with {len(assets)} background music assets.")
        except IOError as e:
            logger.error(f"Error saving background music assets to {self.asset_file_path.name}: {e}")

    def clear_background_music_assets(self, scene_index: int) -> None:
        """Clear all background music assets for a specific scene."""
        ensure_collection_index_exists(self.background_music_assets, scene_index)
        self.background_music_assets[scene_index] = None
        logger.debug(f"Cleared all background music assets for scene {scene_index + 1}")

    def has_background_music(self, scene_index: int) -> bool:
        """Check if a specific scene has background music assets."""
        return scene_index < len(self.background_music_assets) and self.background_music_assets[scene_index] is not None

    def get_missing_background_music(self) -> list[int]:
        """Get a summary of missing background music assets per scene."""
        missing = []
        for i, _ in enumerate(self.background_music_assets):
            if not self.has_background_music(i):
                missing.append(i)
        return missing

    def is_complete(self) -> bool:
        """Check if all scenes have background music assets."""

        return len(self.get_missing_background_music()) == 0

    def get_used_assets_list(self) -> list[Path]:
        """Get a list of all used background music asset file paths."""
        used_assets = []

        for asset in self.background_music_assets:
            if asset is not None:
                used_assets.append(asset)

        return used_assets
