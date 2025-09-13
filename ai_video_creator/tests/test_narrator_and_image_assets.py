"""
Unit tests for narrator_and_image_assets module.
"""

import json
from pathlib import Path

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

        assets.set_scene_narrator(0, Path("/path/to/narrator1.mp3"))
        assets.set_scene_image(0, Path("/path/to/image1.jpg"))
        assets.set_scene_narrator(1, Path("/path/to/narrator2.mp3"))
        assets.set_scene_image(1, Path("/path/to/image2.jpg"))

        assert len(assets.narrator_assets) == 2
        assert len(assets.image_assets) == 2
        assert assets.narrator_assets[0] == Path("/path/to/narrator1.mp3")
        assert assets.narrator_assets[1] == Path("/path/to/narrator2.mp3")
        assert assets.image_assets[0] == Path("/path/to/image1.jpg")
        assert assets.image_assets[1] == Path("/path/to/image2.jpg")

        assets.save_assets_to_file()
        assert asset_file.exists()

        with open(asset_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        expected_structure = {
            "assets": [
                {
                    "index": 1,
                    "narrator": "/path/to/narrator1.mp3",
                    "image": "/path/to/image1.jpg",
                },
                {
                    "index": 2,
                    "narrator": "/path/to/narrator2.mp3",
                    "image": "/path/to/image2.jpg",
                },
            ]
        }

        assert saved_data == expected_structure

    def test_assets_loading_from_file(self, tmp_path):
        """Test loading assets from existing file."""
        asset_file = tmp_path / "existing_assets.json"

        test_data = {
            "assets": [
                {"narrator": "/loaded/narrator1.mp3", "image": "/loaded/image1.jpg"},
                {"narrator": "/loaded/narrator2.mp3", "image": "/loaded/image2.jpg"},
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        assets = NarratorAndImageAssets(asset_file)

        assert len(assets.narrator_assets) == 2
        assert len(assets.image_assets) == 2
        assert assets.narrator_assets[0] == Path("/loaded/narrator1.mp3")
        assert assets.image_assets[0] == Path("/loaded/image1.jpg")
        assert assets.narrator_assets[1] == Path("/loaded/narrator2.mp3")
        assert assets.image_assets[1] == Path("/loaded/image2.jpg")

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

        assets.set_scene_narrator(5, Path("/path/to/narrator5.mp3"))
        assets.set_scene_image(3, Path("/path/to/image3.jpg"))

        # Both lists extend to max index + 1 due to _ensure_index_exists behavior
        assert len(assets.narrator_assets) == 6
        assert len(assets.image_assets) == 6

        assert assets.narrator_assets[5] == Path("/path/to/narrator5.mp3")
        assert assets.image_assets[3] == Path("/path/to/image3.jpg")

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
