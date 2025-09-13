"""
Unit tests for video_assets module.
"""

import json
from pathlib import Path

from ai_video_creator.modules.video import VideoAssets


class TestVideoAssetsFile:
    """Test VideoAssetsFile class - focuses on JSON file management."""

    def test_empty_assets_creation(self, tmp_path):
        """Test creating empty video assets."""
        asset_file = tmp_path / "assets.json"
        assets = VideoAssets(asset_file)

        assert assets.asset_file_path == asset_file
        assert assets.video_assets == []
        assert assets.sub_video_assets == []

    def test_assets_with_data(self, tmp_path):
        """Test video assets with actual data - core functionality."""
        asset_file = tmp_path / "assets.json"
        assets = VideoAssets(asset_file)

        assets.set_scene_video(0, Path("/path/to/video1.mp4"))
        assets.set_scene_sub_video(0, 0, Path("/path/to/sub_video1_0.mp4"))
        assets.set_scene_sub_video(0, 1, Path("/path/to/sub_video1_1.mp4"))
        assets.set_scene_video(1, Path("/path/to/video2.mp4"))
        assets.set_scene_sub_video(1, 0, Path("/path/to/sub_video2_0.mp4"))

        assert len(assets.video_assets) == 2
        assert len(assets.sub_video_assets) == 2
        assert assets.video_assets[0] == Path("/path/to/video1.mp4")
        assert assets.video_assets[1] == Path("/path/to/video2.mp4")
        assert len(assets.sub_video_assets[0]) == 2
        assert len(assets.sub_video_assets[1]) == 1
        assert assets.sub_video_assets[0][0] == Path("/path/to/sub_video1_0.mp4")
        assert assets.sub_video_assets[0][1] == Path("/path/to/sub_video1_1.mp4")
        assert assets.sub_video_assets[1][0] == Path("/path/to/sub_video2_0.mp4")

        assets.save_assets_to_file()
        assert asset_file.exists()

        with open(asset_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        expected_structure = {
            "assets": [
                {
                    "index": 1,
                    "video_asset": "/path/to/video1.mp4",
                    "sub_video_assets": [
                        "/path/to/sub_video1_0.mp4",
                        "/path/to/sub_video1_1.mp4",
                    ],
                },
                {
                    "index": 2,
                    "video_asset": "/path/to/video2.mp4",
                    "sub_video_assets": ["/path/to/sub_video2_0.mp4"],
                },
            ]
        }

        assert saved_data == expected_structure

    def test_assets_loading_from_file(self, tmp_path):
        """Test loading assets from existing file."""
        asset_file = tmp_path / "existing_assets.json"

        test_data = {
            "assets": [
                {
                    "video_asset": "/loaded/video1.mp4",
                    "sub_video_assets": ["/loaded/sub1.mp4", "/loaded/sub2.mp4"],
                },
                {
                    "video_asset": "/loaded/video2.mp4",
                    "sub_video_assets": ["/loaded/sub3.mp4"],
                },
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        assets = VideoAssets(asset_file)

        assert len(assets.video_assets) == 2
        assert len(assets.sub_video_assets) == 2
        assert assets.video_assets[0] == Path("/loaded/video1.mp4")
        assert assets.video_assets[1] == Path("/loaded/video2.mp4")
        assert len(assets.sub_video_assets[0]) == 2
        assert len(assets.sub_video_assets[1]) == 1
        assert assets.sub_video_assets[0][0] == Path("/loaded/sub1.mp4")
        assert assets.sub_video_assets[0][1] == Path("/loaded/sub2.mp4")
        assert assets.sub_video_assets[1][0] == Path("/loaded/sub3.mp4")

    def test_assets_loading_with_corrupted_json(self, tmp_path):
        """Test graceful handling when JSON file is corrupted."""
        asset_file = tmp_path / "corrupted_assets.json"
        old_asset_file = tmp_path / "corrupted_assets.json.old"

        # Create a corrupted JSON file
        corrupted_content = "{ invalid json content"
        with open(asset_file, "w", encoding="utf-8") as f:
            f.write(corrupted_content)

        # Load the assets - should handle error gracefully
        assets = VideoAssets(asset_file)

        # Should start with empty data
        assert assets.video_assets == []
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
        assets = VideoAssets(asset_file)

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
        assets = VideoAssets(asset_file)

        assets.set_scene_video(5, Path("/path/to/video5.mp4"))
        assets.set_scene_sub_video(3, 2, Path("/path/to/sub_video3_2.mp4"))

        # Both lists extend to max index + 1
        assert len(assets.video_assets) == 6
        assert len(assets.sub_video_assets) == 6

        assert assets.video_assets[5] == Path("/path/to/video5.mp4")
        assert len(assets.sub_video_assets[3]) == 3
        assert assets.sub_video_assets[3][2] == Path("/path/to/sub_video3_2.mp4")

        assert assets.video_assets[0] is None
        assert assets.video_assets[1] is None
        assert assets.sub_video_assets[0] == []

    def test_clear_scene_assets(self, tmp_path):
        """Test clearing assets for a specific scene."""
        asset_file = tmp_path / "assets.json"
        assets = VideoAssets(asset_file)

        # Set up some assets
        assets.set_scene_video(0, Path("/path/to/video.mp4"))
        assets.set_scene_sub_video(0, 0, Path("/path/to/sub1.mp4"))
        assets.set_scene_sub_video(0, 1, Path("/path/to/sub2.mp4"))

        # Verify they exist
        assert assets.video_assets[0] == Path("/path/to/video.mp4")
        assert len(assets.sub_video_assets[0]) == 2

        # Clear the scene
        assets.clear_scene_assets(0)

        # Video should be None, but sub_video_assets should remain
        assert assets.video_assets[0] is None
        assert (
            len(assets.sub_video_assets[0]) == 2
        )  # Sub-videos not cleared by clear_scene_assets