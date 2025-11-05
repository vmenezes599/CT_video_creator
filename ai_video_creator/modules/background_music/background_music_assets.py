"""This module manages background music assets for story scenes."""

import json
from pathlib import Path

from logging_utils import logger
from ai_video_creator.utils.video_creator_paths import VideoCreatorPaths
from ai_video_creator.utils import ensure_collection_index_exists, backup_file_to_old


class BackgroundMusicAsset:
    """Class representing a single background music asset."""

    def __init__(self, asset: Path, volume: float, skip: bool):
        """Initialize BackgroundMusicAsset with index and file path."""
        self.asset = asset
        self.volume = volume
        self.skip = skip

        if volume < 0.0 or volume > 1.0:
            raise ValueError("Volume must be between 0.0 and 1.0")

    def to_dict(self) -> dict:
        """Convert the BackgroundMusicAsset to a dictionary for JSON serialization."""
        return {
            "asset": str(self.asset) if self.asset else None,
            "volume": self.volume,
            "skip": self.skip,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackgroundMusicAsset":
        """Create a BackgroundMusicAsset from a dictionary."""

        required_fields = {"asset", "volume", "skip"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise ValueError(f"Missing fields in BackgroundMusicAsset data: {missing_fields}")

        asset_path = Path(data["asset"]) if data["asset"] else None
        volume = data["volume"]
        skip = data["skip"]

        return cls(asset=asset_path, volume=volume, skip=skip)


class BackgroundMusicAssets:
    """Class to manage background music data and persistence only."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize BackgroundMusicAssets with file path and expected scene count."""
        self._paths = video_creator_paths

        self.asset_file_path = self._paths.background_music_asset_file
        self.asset_file_parent = self.asset_file_path.parent.resolve()

        self.background_music_assets: list[BackgroundMusicAsset] = []

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
                for index, asset_dict in enumerate(assets):
                    asset = asset_dict.get("asset")
                    assembled_background_music_path = Path(asset) if asset else None
                    assembled_background_music_path = (
                        self._paths.unmask_asset_path(assembled_background_music_path)
                        if assembled_background_music_path
                        else None
                    )
                    volume = asset_dict.get("volume", 0.5)
                    skip = asset_dict.get("skip", False)

                    self.background_music_assets[index] = BackgroundMusicAsset(
                        asset=assembled_background_music_path, volume=volume, skip=skip
                    )

                self.save_assets_to_file()

        except json.JSONDecodeError:
            logger.error(
                f"Error decoding JSON from {self.asset_file_path.name} - saving to .old and starting with empty assets"
            )
            self.background_music_assets = []

            # Back up the corrupted file before overwriting
            backup_file_to_old(self.asset_file_path)
            logger.debug(f"Backed up corrupted file to: {self.asset_file_path.name}.old")

            # Now safe to create new empty file
            self.save_assets_to_file()

        except FileNotFoundError:
            logger.debug(f"Asset file not found: {self.asset_file_path.name} - starting with empty assets")
            self.background_music_assets = []

    def save_assets_to_file(self) -> None:
        """Save the current state of the background music assets to a file with relative paths."""
        try:
            with open(self.asset_file_path, "w", encoding="utf-8") as file:
                assets = []

                for index, asset in enumerate(self.background_music_assets, 1):

                    asset_dict = asset.to_dict() if asset is not None else None
                    if asset_dict:
                        asset_dict["asset"] = (
                            str(self._paths.mask_asset_path(asset.asset)) if asset and asset.asset else None
                        )

                    background_music_asset_data = {
                        "index": index,
                        "asset": "",
                        "volume": 0.0,
                        "skip": False,
                    }
                    if asset_dict:
                        background_music_asset_data.update(asset_dict)

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
        if scene_index < 0 or scene_index >= len(self.background_music_assets):
            return False

        music_asset_path = self.background_music_assets[scene_index]
        if music_asset_path is None:
            return False

        if music_asset_path.skip:
            return True

        return music_asset_path.asset.exists() and music_asset_path.asset.is_file()

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
            if asset is not None and asset.asset is not None:
                used_assets.append(asset.asset)

        return used_assets
