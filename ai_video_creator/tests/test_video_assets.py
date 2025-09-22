"""
Unit tests for video_assets module.
"""

import json
from pathlib import Path

import pytest

from ai_video_creator.modules.video import SubVideoAssets


class TestVideoAssetsFile:
    """Test VideoAssetsFile class - focuses on JSON file management."""

    def test_empty_assets_creation(self, tmp_path):
        """Test creating empty video assets."""
        asset_file = tmp_path / "assets.json"
        assets = SubVideoAssets(asset_file)

        assert assets.asset_file_path == asset_file
        assert assets.assembled_sub_video == []
        assert assets.sub_video_assets == []

    def test_assets_with_data(self, tmp_path):
        """Test video assets with actual data - core functionality."""
        asset_file = tmp_path / "assets.json"
        assets = SubVideoAssets(asset_file)

        # Create paths within tmp_path for security compliance
        video1_path = tmp_path / "video1.mp4"
        sub_video1_0_path = tmp_path / "sub_video1_0.mp4"
        sub_video1_1_path = tmp_path / "sub_video1_1.mp4"
        video2_path = tmp_path / "video2.mp4"
        sub_video2_0_path = tmp_path / "sub_video2_0.mp4"

        assets.set_scene_video(0, video1_path)
        assets.set_scene_sub_video(0, 0, sub_video1_0_path)
        assets.set_scene_sub_video(0, 1, sub_video1_1_path)
        assets.set_scene_video(1, video2_path)
        assets.set_scene_sub_video(1, 0, sub_video2_0_path)

        assert len(assets.assembled_sub_video) == 2
        assert len(assets.sub_video_assets) == 2
        assert assets.assembled_sub_video[0] == video1_path.resolve()
        assert assets.assembled_sub_video[1] == video2_path.resolve()
        assert len(assets.sub_video_assets[0]) == 2
        assert len(assets.sub_video_assets[1]) == 1
        assert assets.sub_video_assets[0][0] == sub_video1_0_path.resolve()
        assert assets.sub_video_assets[0][1] == sub_video1_1_path.resolve()
        assert assets.sub_video_assets[1][0] == sub_video2_0_path.resolve()

        assets.save_assets_to_file()
        assert asset_file.exists()

        with open(asset_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        expected_structure = {
            "assets": [
                {
                    "index": 1,
                    "video_asset": "video1.mp4",  # Now stored as relative paths
                    "sub_video_assets": [
                        "sub_video1_0.mp4",
                        "sub_video1_1.mp4",
                    ],
                },
                {
                    "index": 2,
                    "video_asset": "video2.mp4",
                    "sub_video_assets": ["sub_video2_0.mp4"],
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
                {
                    "video_asset": "loaded/video1.mp4",
                    "sub_video_assets": ["loaded/sub1.mp4", "loaded/sub2.mp4"],
                },
                {
                    "video_asset": "loaded/video2.mp4",
                    "sub_video_assets": ["loaded/sub3.mp4"],
                },
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        assets = SubVideoAssets(asset_file)

        assert len(assets.assembled_sub_video) == 2
        assert len(assets.sub_video_assets) == 2
        # Paths should be resolved relative to tmp_path
        assert (
            assets.assembled_sub_video[0] == (tmp_path / "loaded/video1.mp4").resolve()
        )
        assert (
            assets.assembled_sub_video[1] == (tmp_path / "loaded/video2.mp4").resolve()
        )
        assert len(assets.sub_video_assets[0]) == 2
        assert len(assets.sub_video_assets[1]) == 1
        assert assets.sub_video_assets[0][0] == (tmp_path / "loaded/sub1.mp4").resolve()
        assert assets.sub_video_assets[0][1] == (tmp_path / "loaded/sub2.mp4").resolve()
        assert assets.sub_video_assets[1][0] == (tmp_path / "loaded/sub3.mp4").resolve()

    def test_assets_loading_with_corrupted_json(self, tmp_path):
        """Test graceful handling when JSON file is corrupted."""
        asset_file = tmp_path / "corrupted_assets.json"
        old_asset_file = tmp_path / "corrupted_assets.json.old"

        # Create a corrupted JSON file
        corrupted_content = "{ invalid json content"
        with open(asset_file, "w", encoding="utf-8") as f:
            f.write(corrupted_content)

        # Load the assets - should handle error gracefully
        assets = SubVideoAssets(asset_file)

        # Should start with empty data
        assert assets.assembled_sub_video == []
        assert assets.sub_video_assets == []

        # The original corrupted file should be renamed to .old
        assert old_asset_file.exists()
        with open(old_asset_file, "r", encoding="utf-8") as f:
            assert f.read() == corrupted_content

        # A new empty file should be created or the file should be valid JSON
        if asset_file.exists():
            with open(asset_file, "r", encoding="utf-8") as f:
                # Should be valid JSON now
                data = json.load(f)
                assert "assets" in data

    def test_asset_completion_checking(self, tmp_path):
        """Test video asset completion and missing asset detection."""
        asset_file = tmp_path / "assets.json"
        assets = SubVideoAssets(asset_file)

        # Empty assets should not have missing videos (since there are no scenes)
        assert assets.get_missing_videos() == []

        # Create actual files for testing
        video1_file = tmp_path / "video1.mp4"
        video2_file = tmp_path / "video2.mp4"
        sub1_file = tmp_path / "sub1.mp4"

        video1_file.write_text("fake video")
        video2_file.write_text("fake video")
        sub1_file.write_text("fake video")

        assets.set_scene_video(0, video1_file)
        assets.set_scene_sub_video(0, 0, sub1_file)
        assets.set_scene_video(1, video2_file)
        # Missing sub-video for scene 1

        # Check video existence
        assert assets.has_video(0) == True
        assert assets.has_video(1) == True
        assert assets.has_sub_videos(0, 0) == True
        assert assets.has_sub_videos(1, 0) == False  # No sub-video for scene 1

        missing = assets.get_missing_videos()
        assert missing == []  # All main videos exist

    def test_asset_index_management(self, tmp_path):
        """Test that assets can be set at non-sequential indices."""
        asset_file = tmp_path / "assets.json"
        assets = SubVideoAssets(asset_file)

        # Create paths within tmp_path for security compliance
        video5_path = tmp_path / "video5.mp4"
        sub_video_path = tmp_path / "sub_video3_2.mp4"

        assets.set_scene_video(5, video5_path)
        assets.set_scene_sub_video(3, 2, sub_video_path)

        # Both lists extend to max index + 1
        assert len(assets.assembled_sub_video) == 6
        assert len(assets.sub_video_assets) == 6

        assert assets.assembled_sub_video[5] == video5_path.resolve()
        assert len(assets.sub_video_assets[3]) == 3
        assert assets.sub_video_assets[3][2] == sub_video_path.resolve()

        assert assets.assembled_sub_video[0] is None
        assert assets.assembled_sub_video[1] is None
        assert assets.sub_video_assets[0] == []

    def test_clear_scene_assets(self, tmp_path):
        """Test clearing assets for a specific scene."""
        asset_file = tmp_path / "assets.json"
        assets = SubVideoAssets(asset_file)

        # Create paths within tmp_path for security compliance
        video_path = tmp_path / "video.mp4"
        sub1_path = tmp_path / "sub1.mp4"
        sub2_path = tmp_path / "sub2.mp4"

        # Set up some assets
        assets.set_scene_video(0, video_path)
        assets.set_scene_sub_video(0, 0, sub1_path)
        assets.set_scene_sub_video(0, 1, sub2_path)

        # Verify they exist
        assert assets.assembled_sub_video[0] == video_path.resolve()
        assert len(assets.sub_video_assets[0]) == 2

        # Clear the scene
        assets.clear_scene_assets(0)

        # Video should be None, but sub_video_assets should remain
        assert assets.assembled_sub_video[0] is None
        assert (
            len(assets.sub_video_assets[0]) == 2
        )  # Sub-videos not cleared by clear_scene_assets

    def test_relative_path_storage_and_loading(self, tmp_path):
        """Test that paths are stored as relative and loaded correctly."""
        asset_file = tmp_path / "assets.json"
        assets = SubVideoAssets(asset_file)

        # Create actual files within the tmp_path directory
        video_file = tmp_path / "videos" / "video1.mp4"
        sub_video1_file = tmp_path / "videos" / "sub1.mp4"
        sub_video2_file = tmp_path / "videos" / "sub2.mp4"
        video_file.parent.mkdir(exist_ok=True)
        video_file.write_text("fake video")
        sub_video1_file.write_text("fake sub video 1")
        sub_video2_file.write_text("fake sub video 2")

        # Set and save assets
        assets.set_scene_video(0, video_file)
        assets.set_scene_sub_video(0, 0, sub_video1_file)
        assets.set_scene_sub_video(0, 1, sub_video2_file)
        assets.save_assets_to_file()

        # Read the saved JSON file
        with open(asset_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        # Paths should be relative to asset_file_parent (tmp_path)
        assert saved_data["assets"][0]["video_asset"] == "videos/video1.mp4"
        assert saved_data["assets"][0]["sub_video_assets"][0] == "videos/sub1.mp4"
        assert saved_data["assets"][0]["sub_video_assets"][1] == "videos/sub2.mp4"

        # Load fresh assets instance to test loading
        new_assets = SubVideoAssets(asset_file)
        assert new_assets.assembled_sub_video[0] == video_file.resolve()
        assert new_assets.sub_video_assets[0][0] == sub_video1_file.resolve()
        assert new_assets.sub_video_assets[0][1] == sub_video2_file.resolve()

    def test_path_validation_for_normal_usage(self, tmp_path):
        """Test basic path validation for normal use cases."""
        asset_file = tmp_path / "assets.json"
        assets = SubVideoAssets(asset_file)

        # Valid paths within directory should work
        valid_video = tmp_path / "valid_video.mp4"
        valid_sub = tmp_path / "valid_sub.mp4"
        valid_video.write_text("video")
        valid_sub.write_text("sub video")

        assets.set_scene_video(0, valid_video)
        assets.set_scene_sub_video(0, 0, valid_sub)
        assert assets.assembled_sub_video[0] == valid_video.resolve()
        assert assets.sub_video_assets[0][0] == valid_sub.resolve()

        # Paths outside directory should be rejected
        outside_video = tmp_path.parent / "outside_video.mp4"
        outside_sub = tmp_path.parent / "outside_sub.mp4"
        outside_video.write_text("video")
        outside_sub.write_text("sub video")

        with pytest.raises(ValueError, match="Path traversal attempt detected"):
            assets.set_scene_video(1, outside_video)

        with pytest.raises(ValueError, match="Path traversal attempt detected"):
            assets.set_scene_sub_video(1, 0, outside_sub)
