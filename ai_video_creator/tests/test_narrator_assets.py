"""
Unit tests for narrator_assets module.
"""

import json
import os
import stat
from pathlib import Path

import pytest

from ai_video_creator.modules.narrator.narrator_assets import NarratorAssets


class TestNarratorAssets:
    """Test NarratorAssets class."""

    def test_narrator_assets_initialization(self, tmp_path):
        """Test NarratorAssets initialization with empty file."""
        asset_file = tmp_path / "test_narrator_assets.json"
        assets = NarratorAssets(asset_file)

        assert assets.asset_file_path == asset_file
        assert len(assets.narrator_assets) == 0

    def test_narrator_assets_load_existing_file(self, tmp_path):
        """Test loading existing narrator assets file."""
        asset_file = tmp_path / "test_narrator_assets.json"
        # Create test asset files
        test_narrator1 = tmp_path / "narrator_001.mp3"
        test_narrator2 = tmp_path / "narrator_002.mp3"
        test_narrator1.touch()
        test_narrator2.touch()

        test_data = {
            "assets": [
                {"narrator": str(test_narrator1.relative_to(tmp_path))},
                {"narrator": str(test_narrator2.relative_to(tmp_path))},
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        assets = NarratorAssets(asset_file)

        assert len(assets.narrator_assets) == 2
        assert assets.narrator_assets[0] == test_narrator1
        assert assets.narrator_assets[1] == test_narrator2

    def test_narrator_assets_set_scene_narrator(self, tmp_path):
        """Test setting narrator asset for a scene."""
        asset_file = tmp_path / "test_narrator_assets.json"
        assets = NarratorAssets(asset_file)

        # Create test narrator file
        test_narrator = tmp_path / "narrator_001.mp3"
        test_narrator.touch()

        assets.set_scene_narrator(0, test_narrator)

        assert len(assets.narrator_assets) == 1
        assert assets.narrator_assets[0] == test_narrator

    def test_narrator_assets_has_narrator(self, tmp_path):
        """Test checking if narrator exists for a scene."""
        asset_file = tmp_path / "test_narrator_assets.json"
        assets = NarratorAssets(asset_file)

        # Create test narrator file
        test_narrator = tmp_path / "narrator_001.mp3"
        test_narrator.touch()

        # Initially no narrator
        assert not assets.has_narrator(0)

        # After setting narrator
        assets.set_scene_narrator(0, test_narrator)
        assert assets.has_narrator(0)

        # File doesn't exist
        assets.narrator_assets[0] = tmp_path / "nonexistent.mp3"
        assert not assets.has_narrator(0)

    def test_narrator_assets_get_missing_assets(self, tmp_path):
        """Test getting missing narrator assets."""
        asset_file = tmp_path / "test_narrator_assets.json"
        assets = NarratorAssets(asset_file)

        # Create some test files
        test_narrator1 = tmp_path / "narrator_001.mp3"
        test_narrator1.touch()

        # Set up mixed scenario
        assets.set_scene_narrator(0, test_narrator1)  # Exists
        assets.set_scene_narrator(1, tmp_path / "nonexistent.mp3")  # Doesn't exist
        assets.narrator_assets.append(None)  # No asset set

        missing = assets.get_missing_narrator_assets()

        assert 0 not in missing  # Has valid file
        assert 1 in missing  # File doesn't exist
        assert 2 in missing  # No asset set

    def test_narrator_assets_save_and_load(self, tmp_path):
        """Test saving and loading narrator assets."""
        asset_file = tmp_path / "test_narrator_assets.json"

        # Create test narrator files
        test_narrator1 = tmp_path / "narrator_001.mp3"
        test_narrator2 = tmp_path / "narrator_002.mp3"
        test_narrator1.touch()
        test_narrator2.touch()

        # Create and save assets
        assets1 = NarratorAssets(asset_file)
        assets1.set_scene_narrator(0, test_narrator1)
        assets1.set_scene_narrator(1, test_narrator2)
        assets1.save_assets_to_file()

        # Load in new instance
        assets2 = NarratorAssets(asset_file)

        assert len(assets2.narrator_assets) == 2
        assert assets2.narrator_assets[0] == test_narrator1
        assert assets2.narrator_assets[1] == test_narrator2

    def test_narrator_assets_is_complete(self, tmp_path):
        """Test checking if all narrator assets are complete."""
        asset_file = tmp_path / "test_narrator_assets.json"
        assets = NarratorAssets(asset_file)

        # Initially complete (empty)
        assert assets.is_complete()

        # Create test files
        test_narrator1 = tmp_path / "narrator_001.mp3"
        test_narrator1.touch()

        # Add valid asset
        assets.set_scene_narrator(0, test_narrator1)
        assert assets.is_complete()

        # Add invalid asset
        assets.set_scene_narrator(1, tmp_path / "nonexistent.mp3")
        assert not assets.is_complete()

    def test_narrator_assets_len_and_getitem(self, tmp_path):
        """Test __len__ and __getitem__ methods."""
        asset_file = tmp_path / "test_narrator_assets.json"
        assets = NarratorAssets(asset_file)

        # Create test files
        test_narrator1 = tmp_path / "narrator_001.mp3"
        test_narrator2 = tmp_path / "narrator_002.mp3"
        test_narrator1.touch()
        test_narrator2.touch()

        assets.set_scene_narrator(0, test_narrator1)
        assets.set_scene_narrator(1, test_narrator2)

        assert len(assets) == 2
        assert assets[0] == test_narrator1
        assert assets[1] == test_narrator2
        assert assets[2] is None  # Out of bounds returns None

    def test_narrator_assets_corrupted_file_handling(self, tmp_path):
        """Test handling of corrupted asset files."""
        asset_file = tmp_path / "test_narrator_assets.json"

        # Create corrupted JSON file
        with open(asset_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        # Should handle corrupted file gracefully and start fresh
        assets = NarratorAssets(asset_file)
        assert len(assets.narrator_assets) == 0

    def test_narrator_assets_invalid_file_structure(self, tmp_path):
        """Test handling of files with invalid structure."""
        asset_file = tmp_path / "test_narrator_assets.json"

        # Create file with invalid structure
        invalid_data = {"wrong_key": ["some", "data"]}
        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(invalid_data, f)

        # Should handle invalid structure gracefully
        assets = NarratorAssets(asset_file)
        assert len(assets.narrator_assets) == 0

    def test_narrator_assets_file_permission_error(self, tmp_path):
        """Test handling of file permission errors."""
        asset_file = tmp_path / "test_narrator_assets.json"
        assets = NarratorAssets(asset_file)

        # Create test file
        test_narrator = tmp_path / "narrator_001.mp3"
        test_narrator.touch()
        assets.set_scene_narrator(0, test_narrator)

        # Make the parent directory read-only to trigger permission error
        try:
            os.chmod(tmp_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

            # Should handle permission error gracefully
            # This won't raise an exception, just fail silently or log
            assets.save_assets_to_file()

        finally:
            # Restore permissions for cleanup
            os.chmod(tmp_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    def test_narrator_assets_large_asset_list(self, tmp_path):
        """Test handling of large numbers of assets."""
        asset_file = tmp_path / "test_narrator_assets.json"
        assets = NarratorAssets(asset_file)

        # Create many test files
        test_files = []
        for i in range(100):
            test_file = tmp_path / f"narrator_{i:03d}.mp3"
            test_file.touch()
            test_files.append(test_file)
            assets.set_scene_narrator(i, test_file)

        # Verify all assets are properly managed
        assert len(assets) == 100
        assert assets.is_complete()

        # Save and reload
        assets.save_assets_to_file()
        assets2 = NarratorAssets(asset_file)
        assert len(assets2) == 100
        assert assets2.is_complete()

        # Verify specific assets
        assert assets2[0] == test_files[0]
        assert assets2[50] == test_files[50]
        assert assets2[99] == test_files[99]
