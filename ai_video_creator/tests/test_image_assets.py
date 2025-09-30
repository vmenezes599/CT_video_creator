"""
Unit tests for image_assets module.
"""

import json
from pathlib import Path

import pytest

from ai_video_creator.modules.image.image_assets import ImageAssets


class TestImageAssets:
    """Test ImageAssets class."""

    def test_image_assets_initialization(self, tmp_path):
        """Test ImageAssets initialization with empty file."""
        asset_file = tmp_path / "test_image_assets.json"
        assets = ImageAssets(asset_file)

        assert assets.asset_file_path == asset_file
        assert len(assets.image_assets) == 0

    def test_image_assets_load_existing_file(self, tmp_path):
        """Test loading existing image assets file."""
        asset_file = tmp_path / "test_image_assets.json"
        
        # Create test asset files
        test_image1 = tmp_path / "image_001.png"
        test_image2 = tmp_path / "image_002.png"
        test_image1.touch()
        test_image2.touch()

        test_data = {
            "image_assets": [
                str(test_image1.relative_to(tmp_path)),
                str(test_image2.relative_to(tmp_path)),
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        assets = ImageAssets(asset_file)

        assert len(assets.image_assets) == 2
        assert assets.image_assets[0] == test_image1
        assert assets.image_assets[1] == test_image2

    def test_image_assets_set_scene_image(self, tmp_path):
        """Test setting image asset for a scene."""
        asset_file = tmp_path / "test_image_assets.json"
        assets = ImageAssets(asset_file)

        # Create test image file
        test_image = tmp_path / "image_001.png"
        test_image.touch()

        assets.set_scene_image(0, test_image)

        assert len(assets.image_assets) == 1
        assert assets.image_assets[0] == test_image

    def test_image_assets_has_image(self, tmp_path):
        """Test checking if image exists for a scene."""
        asset_file = tmp_path / "test_image_assets.json"
        assets = ImageAssets(asset_file)

        # Create test image file
        test_image = tmp_path / "image_001.png"
        test_image.touch()

        # Initially no image
        assert not assets.has_image(0)

        # After setting image
        assets.set_scene_image(0, test_image)
        assert assets.has_image(0)

        # File doesn't exist
        assets.image_assets[0] = tmp_path / "nonexistent.png"
        assert not assets.has_image(0)

    def test_image_assets_get_missing_assets(self, tmp_path):
        """Test getting missing image assets."""
        asset_file = tmp_path / "test_image_assets.json"
        assets = ImageAssets(asset_file)

        # Create some test files
        test_image1 = tmp_path / "image_001.png"
        test_image1.touch()

        # Set up mixed scenario
        assets.set_scene_image(0, test_image1)  # Exists
        assets.set_scene_image(1, tmp_path / "nonexistent.png")  # Doesn't exist
        assets.image_assets.append(None)  # No asset set

        missing = assets.get_missing_image_assets()

        assert 0 not in missing  # Has valid file
        assert 1 in missing      # File doesn't exist
        assert 2 in missing      # No asset set

    def test_image_assets_save_and_load(self, tmp_path):
        """Test saving and loading image assets."""
        asset_file = tmp_path / "test_image_assets.json"
        
        # Create test image files
        test_image1 = tmp_path / "image_001.png"
        test_image2 = tmp_path / "image_002.png"
        test_image1.touch()
        test_image2.touch()

        # Create and save assets
        assets1 = ImageAssets(asset_file)
        assets1.set_scene_image(0, test_image1)
        assets1.set_scene_image(1, test_image2)
        assets1.save_assets_to_file()

        # Load in new instance
        assets2 = ImageAssets(asset_file)

        assert len(assets2.image_assets) == 2
        assert assets2.image_assets[0] == test_image1
        assert assets2.image_assets[1] == test_image2

    def test_image_assets_is_complete(self, tmp_path):
        """Test checking if all image assets are complete."""
        asset_file = tmp_path / "test_image_assets.json"
        assets = ImageAssets(asset_file)

        # Initially complete (empty)
        assert assets.is_complete()

        # Create test files
        test_image1 = tmp_path / "image_001.png"
        test_image1.touch()

        # Add valid asset
        assets.set_scene_image(0, test_image1)
        assert assets.is_complete()

        # Add invalid asset
        assets.set_scene_image(1, tmp_path / "nonexistent.png")
        assert not assets.is_complete()

    def test_image_assets_len_and_getitem(self, tmp_path):
        """Test __len__ and __getitem__ methods."""
        asset_file = tmp_path / "test_image_assets.json"
        assets = ImageAssets(asset_file)

        # Create test files
        test_image1 = tmp_path / "image_001.png"
        test_image2 = tmp_path / "image_002.png"
        test_image1.touch()
        test_image2.touch()

        assets.set_scene_image(0, test_image1)
        assets.set_scene_image(1, test_image2)

        assert len(assets) == 2
        assert assets[0] == test_image1
        assert assets[1] == test_image2
        assert assets[2] is None  # Out of bounds returns None