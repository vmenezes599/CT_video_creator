"""
Narrator assets for managing narrator-specific asset data and persistence.
"""

import json
from pathlib import Path

from ai_video_creator.utils.video_creator_paths import VideoCreatorPaths
from logging_utils import logger


class NarratorAssets:
    """Class to manage narrator assets data and persistence only."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize NarratorAssets with file path."""
        self._paths = video_creator_paths
        self._asset_file_path = self._paths.narrator_asset_file
        self._asset_file_parent = self._asset_file_path.parent.resolve()

        self.narrator_assets: list[Path] = []

        self._load_assets_from_file()

    def __validate_asset_path(self, asset_path: Path) -> Path:
        """
        Validate and resolve asset path, ensuring it's absolute.
        Returns the validated path or raises ValueError for invalid paths.
        """
        try:
            # Require absolute paths only
            if not asset_path.is_absolute():
                raise ValueError(f"Only absolute paths are allowed: {asset_path}")

            # Resolve the absolute path
            resolved_path = asset_path.resolve(strict=False)

            # Basic security check: prevent path traversal attempts
            if ".." in str(asset_path):
                raise ValueError(f"Path traversal not allowed: {asset_path}")

            return resolved_path
        except (FileNotFoundError, RuntimeError, OSError) as e:
            raise ValueError(f"Invalid path: {asset_path} - {e}") from e

    def _load_assets_from_file(self):
        """Load assets from JSON file with security validation."""
        try:
            logger.debug(f"Loading narrator assets from: {self._asset_file_path.name}")
            with open(self._asset_file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            self.narrator_assets = []
            for asset_data in data.get("assets", []):
                if asset_data is None:
                    self.narrator_assets.append(None)
                else:
                    asset_path = asset_data.get("narrator", "")
                    absolute_path = (
                        self._paths.unmask_asset_path(Path(asset_path))
                        if asset_path
                        else None
                    )
                    self.narrator_assets.append(absolute_path)

            logger.debug(
                f"Successfully loaded {len(self.narrator_assets)} narrator assets"
            )

        except json.JSONDecodeError:
            logger.error(
                f"Error decoding JSON from {self._asset_file_path.name} - renaming to .old and starting with empty assets"
            )
            # Rename corrupted file to .old for backup
            old_file_path = Path(str(self._asset_file_path) + ".old")
            if self._asset_file_path.exists():
                self._asset_file_path.rename(old_file_path)
            self.narrator_assets = []
            # Create a new empty file
            self.save_assets_to_file()

        except FileNotFoundError:
            logger.debug(
                f"Narrator asset file not found: {self._asset_file_path.name} - starting with empty assets"
            )
            self.narrator_assets = []

    def save_assets_to_file(self) -> None:
        """Save the current state of the narrator assets to a file with relative paths."""
        try:
            narrator_assets_data = []
            for index, narrator_asset in enumerate(self.narrator_assets, 1):
                if narrator_asset is None:
                    narrator_assets_data.append({"index": index, "narrator": None})
                else:
                    relative_path = self._paths.mask_asset_path(narrator_asset)
                    narrator_assets_data.append(
                        {"index": index, "narrator": str(relative_path)}
                    )

            data = {"assets": narrator_assets_data}
            with open(self._asset_file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            logger.trace(
                f"Narrator assets saved with {len(narrator_assets_data)} items"
            )
        except IOError as e:
            logger.error(
                f"Error saving narrator assets to {self._asset_file_path.name}: {e}"
            )

    def ensure_index_exists(self, scene_index: int) -> None:
        """Extend list to ensure the scene_index exists."""
        # Extend narrator_list if needed
        while len(self.narrator_assets) <= scene_index:
            self.narrator_assets.append(None)

    def set_scene_narrator(self, scene_index: int, narrator_file_path: Path) -> None:
        """Set narrator file path for a specific scene with security validation."""
        try:
            # Validate the path for security
            validated_path = self.__validate_asset_path(narrator_file_path)

            self.ensure_index_exists(scene_index)
            self.narrator_assets[scene_index] = validated_path
            logger.debug(
                f"Set narrator for scene {scene_index + 1}: {validated_path.name}"
            )
        except ValueError as e:
            logger.error(f"Failed to set narrator for scene {scene_index + 1}: {e}")
            raise

    def clear_scene_narrator(self, scene_index: int) -> None:
        """Clear narrator asset for a specific scene."""
        self.ensure_index_exists(scene_index)
        self.narrator_assets[scene_index] = None
        logger.debug(f"Cleared narrator asset for scene {scene_index + 1}")

    def has_narrator(self, scene_index: int) -> bool:
        """Check if a scene has narrator asset."""
        if scene_index < 0 or scene_index >= len(self.narrator_assets):
            return False
        narrator = self.narrator_assets[scene_index]
        return narrator is not None and narrator.exists() and narrator.is_file()

    def get_missing_narrator_assets(self) -> list[int]:
        """Get a list of scene indices missing narrator assets."""
        missing = []
        for i in range(len(self.narrator_assets)):
            if not self.has_narrator(i):
                missing.append(i)
        return missing

    def is_complete(self) -> bool:
        """Check if all narrator assets are present for all scenes."""
        missing = self.get_missing_narrator_assets()
        return len(missing) == 0

    def __len__(self) -> int:
        """Return the number of narrator asset slots."""
        return len(self.narrator_assets)

    def __getitem__(self, index: int) -> Path | None:
        """Get narrator asset by index."""
        if index < 0 or index >= len(self.narrator_assets):
            return None
        return self.narrator_assets[index]
