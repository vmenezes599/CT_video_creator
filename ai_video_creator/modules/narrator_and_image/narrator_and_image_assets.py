"""This module manages the creation of video assets for a given story chapter."""

import json
from pathlib import Path

from logging_utils import logger


class NarratorAndImageAssets:
    """Class to manage video assets data and persistence only."""

    def __init__(self, asset_file_path: Path):
        """Initialize NarratorAndImageAssets with file path and expected scene count."""
        self.asset_file_parent = asset_file_path.parent.resolve()
        self.asset_file_path = asset_file_path
        self.narrator_assets: list[Path] = []
        self.image_assets: list[Path] = []
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
                self._ensure_index_exists(len(assets) - 1)

                # Load assets from the "assets" array format
                for index, asset in enumerate(assets):
                    # Load narrator asset with security validation
                    narrator_value = asset.get("narrator")
                    narrator_value_path = (
                        Path(narrator_value) if narrator_value else None
                    )
                    self.narrator_assets[index] = (
                        self._convert_from_relative_to_absolute(narrator_value_path)
                        if narrator_value_path
                        else None
                    )

                    # Load image asset with security validation
                    image_value = asset.get("image")
                    image_value_path = Path(image_value) if image_value else None
                    self.image_assets[index] = (
                        self._convert_from_relative_to_absolute(image_value_path)
                        if image_value_path
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
            self.narrator_assets = []
            self.image_assets = []
            # Create a new empty file
            self.save_assets_to_file()

        except FileNotFoundError:
            logger.debug(
                f"Asset file not found: {self.asset_file_path.name} - starting with empty assets"
            )
            self.narrator_assets = []
            self.image_assets = []

    def save_assets_to_file(self) -> None:
        """Save the current state of the video assets to a file with relative paths."""
        try:
            assets = []
            for i, _ in enumerate(self.narrator_assets):
                # Convert absolute paths to relative paths for storage
                narrator = ""
                if (
                    i < len(self.narrator_assets)
                    and self.narrator_assets[i] is not None
                ):
                    narrator = str(
                        self._convert_from_absolute_to_relative(self.narrator_assets[i])
                    )

                image = ""
                if i < len(self.image_assets) and self.image_assets[i] is not None:
                    image = str(
                        self._convert_from_absolute_to_relative(self.image_assets[i])
                    )

                assets.append({"index": i + 1, "narrator": narrator, "image": image})

            data = {"assets": assets}
            with open(self.asset_file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            logger.trace(f"Assets saved with {len(assets)} scene assets")
        except IOError as e:
            logger.error(
                f"Error saving video assets to {self.asset_file_path.name}: {e}"
            )

    def _ensure_index_exists(self, scene_index: int) -> None:
        """Extend lists to ensure the scene_index exists."""
        # Extend narrator_list if needed
        while len(self.narrator_assets) <= scene_index:
            self.narrator_assets.append(None)

        # Extend image_list if needed
        while len(self.image_assets) <= scene_index:
            self.image_assets.append(None)

    def set_scene_narrator(self, scene_index: int, narrator_file_path: Path) -> None:
        """Set narrator file path for a specific scene with security validation."""
        try:
            # Validate the path for security
            validated_path = self.__validate_asset_path(narrator_file_path)

            self._ensure_index_exists(scene_index)
            self.narrator_assets[scene_index] = validated_path
            logger.debug(
                f"Set narrator for scene {scene_index + 1}: {validated_path.name}"
            )
        except ValueError as e:
            logger.error(f"Failed to set narrator for scene {scene_index + 1}: {e}")
            raise

    def set_scene_image(self, scene_index: int, image_file_path: Path) -> None:
        """Set image file path for a specific scene with security validation."""
        try:
            # Validate the path for security
            validated_path = self.__validate_asset_path(image_file_path)

            self._ensure_index_exists(scene_index)
            self.image_assets[scene_index] = validated_path
            logger.debug(
                f"Set image for scene {scene_index + 1}: {validated_path.name}"
            )
        except ValueError as e:
            logger.error(f"Failed to set image for scene {scene_index + 1}: {e}")
            raise

    def clear_scene_assets(self, scene_index: int) -> None:
        """Clear all assets for a specific scene."""
        self._ensure_index_exists(scene_index)
        self.narrator_assets[scene_index] = None
        self.image_assets[scene_index] = None
        logger.debug(f"Cleared all assets for scene {scene_index + 1}")

    def has_narrator(self, scene_index: int) -> bool:
        """Check if a scene has narrator asset."""
        if scene_index < 0 or scene_index >= len(self.narrator_assets):
            return False
        narrator = self.narrator_assets[scene_index]
        return narrator is not None and narrator.exists() and narrator.is_file()

    def has_image(self, scene_index: int) -> bool:
        """Check if a scene has image asset."""
        if scene_index < 0 or scene_index >= len(self.image_assets):
            return False
        image = self.image_assets[scene_index]
        return image is not None and image.exists() and image.is_file()

    def get_missing_narrator_and_image_assets(self) -> dict:
        """Get a summary of missing assets per scene."""
        missing = {"narrator": [], "image": []}
        for i, _ in enumerate(self.narrator_assets):
            if not self.has_narrator(i):
                missing["narrator"].append(i)
        for i, _ in enumerate(self.image_assets):
            if not self.has_image(i):
                missing["image"].append(i)
        return missing

    def is_complete(self) -> bool:
        """Check if all assets are present for all scenes."""
        missing = self.get_missing_narrator_and_image_assets()
        return len(missing["narrator"]) == 0 and len(missing["image"]) == 0
