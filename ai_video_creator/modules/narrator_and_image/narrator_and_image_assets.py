"""This module manages the creation of video assets for a given story chapter."""

import json
from pathlib import Path

from logging_utils import logger


class NarratorAndImageAssets:
    """Class to manage video assets data and persistence only."""

    def __init__(self, asset_file_path: Path):
        """Initialize NarratorAndImageAssets with file path and expected scene count."""
        self.asset_file_parent = asset_file_path.parent
        self.asset_file_path = asset_file_path
        self.narrator_assets: list[Path] = []
        self.image_assets: list[Path] = []
        self._load_assets_from_file()

    def __is_within_directory(self, base: Path, target: Path) -> bool:
        """
        Check if a target path is within a base directory.
        Security method to prevent path traversal attacks.
        """
        try:
            base_resolved = base.resolve(strict=False)
            target_resolved = target.resolve(strict=False)
            # Check if target is equal to base or if base is an ancestor of target
            return target_resolved == base_resolved or base_resolved in target_resolved.parents
        except (FileNotFoundError, RuntimeError, OSError):
            return False

    def __validate_asset_path(self, asset_path: Path) -> Path:
        """
        Validate and resolve asset path, ensuring it's within the allowed directory.
        Returns the validated path or raises ValueError for security violations.
        """
        try:
            # Resolve the path relative to asset_file_parent if it's relative
            if not asset_path.is_absolute():
                resolved_path = (self.asset_file_parent / asset_path).resolve(
                    strict=False
                )
            else:
                resolved_path = asset_path.resolve(strict=False)

            # Security check: ensure the path is within the allowed directory
            if not self.__is_within_directory(self.asset_file_parent, resolved_path):
                raise ValueError(f"Path traversal attempt detected: {asset_path}")

            return resolved_path
        except (FileNotFoundError, RuntimeError, OSError) as e:
            raise ValueError(f"Invalid path: {asset_path} - {e}") from e

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
                    if narrator_value is not None and narrator_value != "":
                        try:
                            narrator_path = Path(narrator_value)
                            # Handle both absolute and relative paths for backward compatibility
                            if narrator_path.is_absolute():
                                # Check if absolute path is within allowed directory
                                if self.__is_within_directory(
                                    self.asset_file_parent, narrator_path
                                ):
                                    validated_path = narrator_path.resolve(strict=False)
                                    self.narrator_assets[index] = validated_path
                                    logger.debug(
                                        f"Migrated absolute narrator path at index {index}: {narrator_path}"
                                    )
                                else:
                                    logger.warning(
                                        f"Absolute narrator path outside allowed directory at index {index}: {narrator_path}"
                                    )
                                    self.narrator_assets[index] = None
                            else:
                                # Relative path - use existing validation
                                validated_path = self.__validate_asset_path(
                                    narrator_path
                                )
                                self.narrator_assets[index] = validated_path
                        except ValueError as e:
                            logger.warning(
                                f"Invalid narrator path at index {index}: {e}"
                            )
                            self.narrator_assets[index] = None

                    # Load image asset with security validation
                    image_value = asset.get("image")
                    if image_value is not None and image_value != "":
                        try:
                            image_path = Path(image_value)
                            # Handle both absolute and relative paths for backward compatibility
                            if image_path.is_absolute():
                                # Check if absolute path is within allowed directory
                                if self.__is_within_directory(
                                    self.asset_file_parent, image_path
                                ):
                                    validated_path = image_path.resolve(strict=False)
                                    self.image_assets[index] = validated_path
                                    logger.debug(
                                        f"Migrated absolute image path at index {index}: {image_path}"
                                    )
                                else:
                                    logger.warning(
                                        f"Absolute image path outside allowed directory at index {index}: {image_path}"
                                    )
                                    self.image_assets[index] = None
                            else:
                                # Relative path - use existing validation
                                validated_path = self.__validate_asset_path(image_path)
                                self.image_assets[index] = validated_path
                        except ValueError as e:
                            logger.warning(f"Invalid image path at index {index}: {e}")
                            self.image_assets[index] = None

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
                    # All paths should be within asset_file_parent due to security validation
                    narrator = str(
                        self.narrator_assets[i].relative_to(
                            self.asset_file_parent.resolve()
                        )
                    )

                image = ""
                if i < len(self.image_assets) and self.image_assets[i] is not None:
                    # All paths should be within asset_file_parent due to security validation
                    image = str(
                        self.image_assets[i].relative_to(
                            self.asset_file_parent.resolve()
                        )
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
