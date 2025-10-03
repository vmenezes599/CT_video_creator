"""
Image assets for managing image-specific asset data and persistence.
"""

import json
from pathlib import Path

from logging_utils import logger


class ImageAssets:
    """Class to manage image assets data and persistence only."""

    def __init__(self, asset_file_path: Path):
        """Initialize ImageAssets with file path."""
        self.asset_file_parent = asset_file_path.parent.resolve()
        self.asset_file_path = asset_file_path
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
                raise ValueError(f"Only absolute paths are allowed: {asset_path}")

            # Resolve the absolute path
            resolved_path = asset_path.resolve(strict=False)

            # Basic security check: prevent path traversal attempts
            if ".." in str(asset_path):
                raise ValueError(f"Path traversal not allowed: {asset_path}")

            return resolved_path
        except (FileNotFoundError, RuntimeError, OSError) as e:
            raise ValueError(f"Invalid path: {asset_path} - {e}") from e

    def convert_from_relative_to_absolute(self, path: Path) -> Path:
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
            logger.debug(f"Loading image assets from: {self.asset_file_path.name}")
            with open(self.asset_file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            self.image_assets = []
            for asset_data in data.get("assets", []):
                if asset_data is None:
                    self.image_assets.append(None)
                else:
                    asset_path = Path(asset_data.get("image", None))
                    absolute_path = (
                        self.convert_from_relative_to_absolute(asset_path)
                        if asset_data
                        else None
                    )
                    self.image_assets.append(absolute_path)

            logger.debug(f"Successfully loaded {len(self.image_assets)} image assets")

        except json.JSONDecodeError:
            logger.error(
                f"Error decoding JSON from {self.asset_file_path.name} - renaming to .old and starting with empty assets"
            )
            # Rename corrupted file to .old for backup
            old_file_path = Path(str(self.asset_file_path) + ".old")
            if self.asset_file_path.exists():
                self.asset_file_path.rename(old_file_path)
            self.image_assets = []
            # Create a new empty file
            self.save_assets_to_file()

        except FileNotFoundError:
            logger.debug(
                f"Image asset file not found: {self.asset_file_path.name} - starting with empty assets"
            )
            self.image_assets = []

    def save_assets_to_file(self) -> None:
        """Save the current state of the image assets to a file with relative paths."""
        try:
            image_assets_data = []
            for index, image_asset in enumerate(self.image_assets, 1):
                if image_asset is None:
                    image_assets_data.append({"index": index, "image": None})
                else:
                    relative_path = self._convert_from_absolute_to_relative(image_asset)
                    image_assets_data.append(
                        {"index": index, "image": str(relative_path)}
                    )

            data = {"assets": image_assets_data}
            with open(self.asset_file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            logger.trace(f"Image assets saved with {len(image_assets_data)} items")
        except IOError as e:
            logger.error(
                f"Error saving image assets to {self.asset_file_path.name}: {e}"
            )

    def ensure_index_exists(self, scene_index: int) -> None:
        """Extend list to ensure the scene_index exists."""
        # Extend image_list if needed
        while len(self.image_assets) <= scene_index:
            self.image_assets.append(None)

    def set_scene_image(self, scene_index: int, image_file_path: Path) -> None:
        """Set image file path for a specific scene with security validation."""
        try:
            # Validate the path for security
            validated_path = self.__validate_asset_path(image_file_path)

            self.ensure_index_exists(scene_index)
            self.image_assets[scene_index] = validated_path
            logger.debug(
                f"Set image for scene {scene_index + 1}: {validated_path.name}"
            )
        except ValueError as e:
            logger.error(f"Failed to set image for scene {scene_index + 1}: {e}")
            raise

    def clear_scene_image(self, scene_index: int) -> None:
        """Clear image asset for a specific scene."""
        self.ensure_index_exists(scene_index)
        self.image_assets[scene_index] = None
        logger.debug(f"Cleared image asset for scene {scene_index + 1}")

    def has_image(self, scene_index: int) -> bool:
        """Check if a scene has image asset."""
        if scene_index < 0 or scene_index >= len(self.image_assets):
            return False
        image = self.image_assets[scene_index]
        return image is not None and image.exists() and image.is_file()

    def get_missing_image_assets(self) -> list[int]:
        """Get a list of scene indices missing image assets."""
        missing = []
        for i in range(len(self.image_assets)):
            if not self.has_image(i):
                missing.append(i)
        return missing

    def is_complete(self) -> bool:
        """Check if all image assets are present for all scenes."""
        missing = self.get_missing_image_assets()
        return len(missing) == 0

    def __len__(self) -> int:
        """Return the number of image asset slots."""
        return len(self.image_assets)

    def __getitem__(self, index: int) -> Path | None:
        """Get image asset by index."""
        if index < 0 or index >= len(self.image_assets):
            return None
        return self.image_assets[index]
