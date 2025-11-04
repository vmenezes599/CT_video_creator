"""
Unit tests for video_assets module.
"""

import json
from pathlib import Path

import pytest

from ai_video_creator.modules.sub_video import SubVideoAssets
from ai_video_creator.utils.video_creator_paths import VideoCreatorPaths


class TestVideoAssetsFile:
    """Test VideoAssetsFile class - focuses on JSON file management."""

    def test_empty_assets_creation(self, tmp_path):
        """Test creating empty video assets."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = SubVideoAssets(paths)

        assert assets.assembled_sub_videos == []
        assert assets.sub_video_assets == []

    def test_assets_with_data(self, tmp_path):
        """Test video assets with actual data - core functionality."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = SubVideoAssets(paths)

        # Create paths within story assets folder
        video1_path = paths.sub_videos_asset_folder / "video1.mp4"
        sub_video1_0_path = paths.sub_videos_asset_folder / "sub_video1_0.mp4"
        sub_video1_1_path = paths.sub_videos_asset_folder / "sub_video1_1.mp4"
        video2_path = paths.sub_videos_asset_folder / "video2.mp4"
        sub_video2_0_path = paths.sub_videos_asset_folder / "sub_video2_0.mp4"

        assets.set_scene_video(0, video1_path)
        assets.set_scene_sub_video(0, 0, sub_video1_0_path)
        assets.set_scene_sub_video(0, 1, sub_video1_1_path)
        assets.set_scene_video(1, video2_path)
        assets.set_scene_sub_video(1, 0, sub_video2_0_path)

        assert len(assets.assembled_sub_videos) == 2
        assert len(assets.sub_video_assets) == 2
        assert assets.assembled_sub_videos[0] == video1_path.resolve()
        assert assets.assembled_sub_videos[1] == video2_path.resolve()
        assert len(assets.sub_video_assets[0]) == 2
        assert len(assets.sub_video_assets[1]) == 1
        assert assets.sub_video_assets[0][0] == sub_video1_0_path.resolve()
        assert assets.sub_video_assets[0][1] == sub_video1_1_path.resolve()
        assert assets.sub_video_assets[1][0] == sub_video2_0_path.resolve()

        assets.save_assets_to_file()
        asset_file = paths.sub_video_asset_file
        assert asset_file.exists()

        with open(asset_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        expected_structure = {
            "assets": [
                {
                    "index": 1,
                    "video_asset": "assets/sub_videos/video1.mp4",  # Stored as masked paths
                    "sub_video_assets": [
                        "assets/sub_videos/sub_video1_0.mp4",
                        "assets/sub_videos/sub_video1_1.mp4",
                    ],
                },
                {
                    "index": 2,
                    "video_asset": "assets/sub_videos/video2.mp4",
                    "sub_video_assets": ["assets/sub_videos/sub_video2_0.mp4"],
                },
            ]
        }

        assert saved_data == expected_structure

    def test_assets_loading_from_file(self, tmp_path):
        """Test loading assets from existing file with masked paths."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        asset_file = paths.sub_video_asset_file

        # Create test files in story assets folder
        loaded_folder = paths.sub_videos_asset_folder / "loaded"
        loaded_folder.mkdir(exist_ok=True)
        video1_file = loaded_folder / "video1.mp4"
        video2_file = loaded_folder / "video2.mp4"
        sub1_file = loaded_folder / "sub1.mp4"
        sub2_file = loaded_folder / "sub2.mp4"
        sub3_file = loaded_folder / "sub3.mp4"
        video1_file.touch()
        video2_file.touch()
        sub1_file.touch()
        sub2_file.touch()
        sub3_file.touch()

        # Use masked paths
        test_data = {
            "assets": [
                {
                    "video_asset": str(paths.mask_asset_path(video1_file)),
                    "sub_video_assets": [
                        str(paths.mask_asset_path(sub1_file)),
                        str(paths.mask_asset_path(sub2_file)),
                    ],
                },
                {
                    "video_asset": str(paths.mask_asset_path(video2_file)),
                    "sub_video_assets": [str(paths.mask_asset_path(sub3_file))],
                },
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        assets = SubVideoAssets(paths)

        assert len(assets.assembled_sub_videos) == 2
        assert len(assets.sub_video_assets) == 2
        assert assets.assembled_sub_videos[0] == video1_file.resolve()
        assert assets.assembled_sub_videos[1] == video2_file.resolve()
        assert len(assets.sub_video_assets[0]) == 2
        assert len(assets.sub_video_assets[1]) == 1
        assert assets.sub_video_assets[0][0] == sub1_file.resolve()
        assert assets.sub_video_assets[0][1] == sub2_file.resolve()
        assert assets.sub_video_assets[1][0] == sub3_file.resolve()

    def test_assets_loading_with_corrupted_json(self, tmp_path):
        """Test graceful handling when JSON file is corrupted."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        asset_file = paths.sub_video_asset_file
        old_asset_file = Path(str(asset_file) + ".old")

        # Create a corrupted JSON file
        corrupted_content = "{ invalid json content"
        with open(asset_file, "w", encoding="utf-8") as f:
            f.write(corrupted_content)

        # Load the assets - should handle error gracefully
        assets = SubVideoAssets(paths)

        # Should start with empty data
        assert assets.assembled_sub_videos == []
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
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = SubVideoAssets(paths)

        # Empty assets should not have missing videos (since there are no scenes)
        assert assets.get_missing_videos() == []

        # Create actual files for testing in story assets folder
        video1_file = paths.sub_videos_asset_folder / "video1.mp4"
        video2_file = paths.sub_videos_asset_folder / "video2.mp4"
        sub1_file = paths.sub_videos_asset_folder / "sub1.mp4"

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
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = SubVideoAssets(paths)

        # Create paths within story assets folder
        video5_path = paths.sub_videos_asset_folder / "video5.mp4"
        sub_video_path = paths.sub_videos_asset_folder / "sub_video3_2.mp4"

        assets.set_scene_video(5, video5_path)
        assets.set_scene_sub_video(3, 2, sub_video_path)

        # Both lists extend to max index + 1
        assert len(assets.assembled_sub_videos) == 6
        assert len(assets.sub_video_assets) == 6

        assert assets.assembled_sub_videos[5] == video5_path.resolve()
        assert len(assets.sub_video_assets[3]) == 3
        assert assets.sub_video_assets[3][2] == sub_video_path.resolve()

        assert assets.assembled_sub_videos[0] is None
        assert assets.assembled_sub_videos[1] is None
        assert assets.sub_video_assets[0] == []

    def test_clear_scene_assets(self, tmp_path):
        """Test clearing assets for a specific scene."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = SubVideoAssets(paths)

        # Create paths within story assets folder
        video_path = paths.sub_videos_asset_folder / "video.mp4"
        sub1_path = paths.sub_videos_asset_folder / "sub1.mp4"
        sub2_path = paths.sub_videos_asset_folder / "sub2.mp4"

        # Set up some assets
        assets.set_scene_video(0, video_path)
        assets.set_scene_sub_video(0, 0, sub1_path)
        assets.set_scene_sub_video(0, 1, sub2_path)

        # Verify they exist
        assert assets.assembled_sub_videos[0] == video_path.resolve()
        assert len(assets.sub_video_assets[0]) == 2

        # Clear the scene
        assets.clear_scene_assets(0)

        # Video should be None, but sub_video_assets should remain
        assert assets.assembled_sub_videos[0] is None
        assert len(assets.sub_video_assets[0]) == 2  # Sub-videos not cleared by clear_scene_assets

    def test_relative_path_storage_and_loading(self, tmp_path):
        """Test that paths are stored as masked and loaded correctly."""
        paths1 = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = SubVideoAssets(paths1)

        # Create actual files within story assets folder
        videos_folder = paths1.sub_videos_asset_folder / "videos"
        videos_folder.mkdir(exist_ok=True)
        video_file = videos_folder / "video1.mp4"
        sub_video1_file = videos_folder / "sub1.mp4"
        sub_video2_file = videos_folder / "sub2.mp4"
        video_file.write_text("fake video")
        sub_video1_file.write_text("fake sub video 1")
        sub_video2_file.write_text("fake sub video 2")

        # Set and save assets
        assets.set_scene_video(0, video_file)
        assets.set_scene_sub_video(0, 0, sub_video1_file)
        assets.set_scene_sub_video(0, 1, sub_video2_file)
        assets.save_assets_to_file()

        # Read the saved JSON file
        asset_file = paths1.sub_video_asset_file
        with open(asset_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        # Paths should be stored as masked paths
        assert saved_data["assets"][0]["video_asset"] == "assets/sub_videos/videos/video1.mp4"
        assert saved_data["assets"][0]["sub_video_assets"][0] == "assets/sub_videos/videos/sub1.mp4"
        assert saved_data["assets"][0]["sub_video_assets"][1] == "assets/sub_videos/videos/sub2.mp4"

        # Load fresh assets instance to test loading
        paths2 = VideoCreatorPaths(tmp_path, "test_story", 0)
        new_assets = SubVideoAssets(paths2)
        assert new_assets.assembled_sub_videos[0] == video_file.resolve()
        assert new_assets.sub_video_assets[0][0] == sub_video1_file.resolve()
        assert new_assets.sub_video_assets[0][1] == sub_video2_file.resolve()

    def test_path_validation_for_normal_usage(self, tmp_path):
        """Test basic path validation - only absolute paths are allowed."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = SubVideoAssets(paths)

        # Valid absolute paths within story assets folder should work
        valid_video = paths.sub_videos_asset_folder / "valid_video.mp4"
        valid_sub = paths.sub_videos_asset_folder / "valid_sub.mp4"
        valid_video.write_text("videos")
        valid_sub.write_text("sub video")

        assets.set_scene_video(0, valid_video)
        assets.set_scene_sub_video(0, 0, valid_sub)
        assert assets.assembled_sub_videos[0] == valid_video.resolve()
        assert assets.sub_video_assets[0][0] == valid_sub.resolve()

        # Valid absolute paths within subdirectories should work
        subdir = paths.sub_videos_asset_folder / "videos"
        subdir.mkdir()
        subdir_video = subdir / "subdir_video.mp4"
        subdir_sub = subdir / "subdir_sub.mp4"
        subdir_video.write_text("videos")
        subdir_sub.write_text("sub video")

        assets.set_scene_video(1, subdir_video)
        assets.set_scene_sub_video(1, 0, subdir_sub)
        assert assets.assembled_sub_videos[1] == subdir_video.resolve()
        assert assets.sub_video_assets[1][0] == subdir_sub.resolve()

        # Relative paths should raise ValueError
        relative_video = Path("relative_video.mp4")
        relative_sub = Path("relative_sub.mp4")

        with pytest.raises(ValueError, match="Asset path is not under known assets folders"):
            assets.set_scene_video(3, relative_video)

        with pytest.raises(ValueError, match="Asset path is not under known assets folders"):
            assets.set_scene_sub_video(3, 0, relative_sub)

        # Path traversal patterns with ".." should be rejected
        traversal_video = Path("/tmp/../etc/passwd")
        traversal_sub = Path("/home/../etc/passwd")

        with pytest.raises(ValueError, match="Asset path is not under known assets folders"):
            assets.set_scene_video(4, traversal_video)

        with pytest.raises(ValueError, match="Asset path is not under known assets folders"):
            assets.set_scene_sub_video(4, 0, traversal_sub)
