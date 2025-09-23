"""
Unit tests for narrator_and_image_assets module.
"""

import json
from pathlib import Path

import pytest

from ai_video_creator.modules.narrator_and_image import NarratorAndImageAssets


class TestNarratorAndImageAssetsFile:
    """Test NarratorAndImageAssets class - focuses on JSON file management."""

    def test_empty_assets_creation(self, tmp_path):
        """Test creating empty video assets."""
        asset_file = tmp_path / "assets.json"
        assets = NarratorAndImageAssets(asset_file)

        assert assets.asset_file_path == asset_file
        assert assets.narrator_assets == []
        assert assets.image_assets == []

    def test_assets_with_data(self, tmp_path):
        """Test video assets with actual data - core functionality."""
        asset_file = tmp_path / "assets.json"
        assets = NarratorAndImageAssets(asset_file)

        # Create paths within the tmp_path directory for security compliance
        narrator1_path = tmp_path / "narrator1.mp3"
        image1_path = tmp_path / "image1.jpg"
        narrator2_path = tmp_path / "narrator2.mp3"
        image2_path = tmp_path / "image2.jpg"

        assets.set_scene_narrator(0, narrator1_path)
        assets.set_scene_image(0, image1_path)
        assets.set_scene_narrator(1, narrator2_path)
        assets.set_scene_image(1, image2_path)

        assert len(assets.narrator_assets) == 2
        assert len(assets.image_assets) == 2
        assert assets.narrator_assets[0] == narrator1_path.resolve()
        assert assets.narrator_assets[1] == narrator2_path.resolve()
        assert assets.image_assets[0] == image1_path.resolve()
        assert assets.image_assets[1] == image2_path.resolve()

        assets.save_assets_to_file()
        assert asset_file.exists()

        with open(asset_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        expected_structure = {
            "assets": [
                {
                    "index": 1,
                    "narrator": "narrator1.mp3",  # Now stored as relative paths
                    "image": "image1.jpg",
                },
                {
                    "index": 2,
                    "narrator": "narrator2.mp3",
                    "image": "image2.jpg",
                },
            ]
        }

        assert saved_data == expected_structure

    def test_assets_loading_from_file(self, tmp_path):
        """Test loading assets from existing file with relative paths."""
        asset_file = tmp_path / "existing_assets.json"

        # Use relative paths that will be resolved within tmp_path
        test_data = {
            "assets": [
                {"narrator": "loaded/narrator1.mp3", "image": "loaded/image1.jpg"},
                {"narrator": "loaded/narrator2.mp3", "image": "loaded/image2.jpg"},
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        assets = NarratorAndImageAssets(asset_file)

        assert len(assets.narrator_assets) == 2
        assert len(assets.image_assets) == 2
        # Paths should be resolved relative to tmp_path
        assert (
            assets.narrator_assets[0] == (tmp_path / "loaded/narrator1.mp3").resolve()
        )
        assert assets.image_assets[0] == (tmp_path / "loaded/image1.jpg").resolve()
        assert (
            assets.narrator_assets[1] == (tmp_path / "loaded/narrator2.mp3").resolve()
        )
        assert assets.image_assets[1] == (tmp_path / "loaded/image2.jpg").resolve()

    def test_asset_completion_checking(self, tmp_path):
        """Test asset completion and missing asset detection."""
        asset_file = tmp_path / "assets.json"
        assets = NarratorAndImageAssets(asset_file)

        # Empty assets should be complete
        assert assets.is_complete()

        # Create actual files for testing
        narrator1_file = tmp_path / "narrator1.mp3"
        narrator2_file = tmp_path / "narrator2.mp3"
        image1_file = tmp_path / "image1.jpg"

        narrator1_file.write_text("fake audio")
        narrator2_file.write_text("fake audio")
        image1_file.write_text("fake image")

        assets.set_scene_narrator(0, narrator1_file)
        assets.set_scene_image(0, image1_file)
        assets.set_scene_narrator(1, narrator2_file)
        # Missing image for scene 1

        assert not assets.is_complete()

        missing = assets.get_missing_narrator_and_image_assets()
        assert missing["narrator"] == []  # All narrator files exist
        assert missing["image"] == [1]  # Image for scene 1 is missing

        # Add the missing image
        image2_file = tmp_path / "image2.jpg"
        image2_file.write_text("fake image")
        assets.set_scene_image(1, image2_file)

        assert assets.is_complete()
        missing = assets.get_missing_narrator_and_image_assets()
        assert missing["narrator"] == []
        assert missing["image"] == []

    def test_asset_index_management(self, tmp_path):
        """Test that assets can be set at non-sequential indices."""
        asset_file = tmp_path / "assets.json"
        assets = NarratorAndImageAssets(asset_file)

        # Use paths within tmp_path for security compliance
        narrator5_path = tmp_path / "narrator5.mp3"
        image3_path = tmp_path / "image3.jpg"

        assets.set_scene_narrator(5, narrator5_path)
        assets.set_scene_image(3, image3_path)

        # Both lists extend to max index + 1 due to _ensure_index_exists behavior
        assert len(assets.narrator_assets) == 6
        assert len(assets.image_assets) == 6

        assert assets.narrator_assets[5] == narrator5_path.resolve()
        assert assets.image_assets[3] == image3_path.resolve()

        assert assets.narrator_assets[0] is None
        assert assets.narrator_assets[1] is None
        assert assets.image_assets[0] is None

    def test_assets_loading_with_corrupted_json(self, tmp_path):
        """Test graceful handling when JSON file is corrupted."""
        asset_file = tmp_path / "corrupted_assets.json"
        old_asset_file = tmp_path / "corrupted_assets.json.old"

        # Create a corrupted JSON file
        corrupted_content = "{ invalid json content"
        with open(asset_file, "w", encoding="utf-8") as f:
            f.write(corrupted_content)

        # Load the assets - should handle error gracefully
        assets = NarratorAndImageAssets(asset_file)

        # Should start with empty data
        assert assets.narrator_assets == []
        assert assets.image_assets == []

        # The original corrupted file should be renamed to .old
        assert old_asset_file.exists()
        with open(old_asset_file, "r", encoding="utf-8") as f:
            assert f.read() == corrupted_content

        # A new empty file should be created with valid JSON
        assert asset_file.exists()
        with open(asset_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "assets" in data
            assert data["assets"] == []

    def test_relative_path_storage_and_loading(self, tmp_path):
        """Test that paths are stored as relative and loaded correctly."""
        asset_file = tmp_path / "assets.json"
        assets = NarratorAndImageAssets(asset_file)

        # Create actual files within the tmp_path directory
        narrator_file = tmp_path / "narrators" / "narrator1.mp3"
        image_file = tmp_path / "images" / "image1.jpg"
        narrator_file.parent.mkdir(exist_ok=True)
        image_file.parent.mkdir(exist_ok=True)
        narrator_file.write_text("fake audio")
        image_file.write_text("fake image")

        # Set and save assets
        assets.set_scene_narrator(0, narrator_file)
        assets.set_scene_image(0, image_file)
        assets.save_assets_to_file()

        # Read the saved JSON file
        with open(asset_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        # Paths should be relative to asset_file_parent (tmp_path)
        assert saved_data["assets"][0]["narrator"] == "narrators/narrator1.mp3"
        assert saved_data["assets"][0]["image"] == "images/image1.jpg"

        # Load fresh assets instance to test loading
        new_assets = NarratorAndImageAssets(asset_file)
        assert new_assets.narrator_assets[0] == narrator_file.resolve()
        assert new_assets.image_assets[0] == image_file.resolve()

    def test_path_validation_for_normal_usage(self, tmp_path):
        """Test basic path validation for normal use cases."""
        asset_file = tmp_path / "assets.json"
        assets = NarratorAndImageAssets(asset_file)

        # Valid path within directory should work
        valid_file = tmp_path / "valid_narrator.mp3"
        valid_file.write_text("audio")
        assets.set_scene_narrator(0, valid_file)
        assert assets.narrator_assets[0] == valid_file.resolve()

        # Paths outside directory are now allowed since we trust absolute paths
        outside_file = tmp_path.parent / "outside.mp3"
        outside_file.write_text("audio")

        # This should work since it's a valid absolute path
        assets.set_scene_narrator(1, outside_file)
        assert assets.narrator_assets[1] == outside_file.resolve()

        # Only path traversal patterns with ".." should be rejected
        traversal_file = Path("/tmp/../etc/passwd")

        with pytest.raises(ValueError, match="Path traversal attempt detected"):
            assets.set_scene_narrator(2, traversal_file)

        # Test relative paths are rejected
        relative_file = Path("relative/path.mp3")

        with pytest.raises(ValueError, match="Path must be absolute"):
            assets.set_scene_narrator(3, relative_file)
