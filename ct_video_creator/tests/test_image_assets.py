"""
Unit tests for image_assets module.
"""

import json
import os
import stat


from ct_video_creator.modules.image.image_assets import ImageAssets
from ct_video_creator.utils.video_creator_paths import VideoCreatorPaths


class TestImageAssets:
    """Test ImageAssets class."""

    def test_image_assets_initialization(self, tmp_path):
        """Test ImageAssets initialization with empty file."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = ImageAssets(paths)

        assert len(assets.image_assets) == 0

    def test_image_assets_load_existing_file(self, tmp_path):
        """Test loading existing image assets file."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        asset_file = paths.image_asset_file

        # Create test asset files in story assets folder
        test_image1 = paths.image_asset_folder / "image_001.png"
        test_image2 = paths.image_asset_folder / "image_002.png"
        test_image1.touch()
        test_image2.touch()

        test_data = {
            "assets": [
                {"image": str(paths.mask_asset_path(test_image1))},
                {"image": str(paths.mask_asset_path(test_image2))},
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        assets = ImageAssets(paths)

        assert len(assets.image_assets) == 2
        assert assets.image_assets[0] == test_image1
        assert assets.image_assets[1] == test_image2

    def test_image_assets_set_scene_image(self, tmp_path):
        """Test setting image asset for a scene."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = ImageAssets(paths)

        # Create test image file in story assets folder
        test_image = paths.image_asset_folder / "image_001.png"
        test_image.touch()

        assets.set_scene_image(0, test_image)

        assert len(assets.image_assets) == 1
        assert assets.image_assets[0] == test_image

    def test_image_assets_has_image(self, tmp_path):
        """Test checking if image exists for a scene."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = ImageAssets(paths)

        # Create test image file in story assets folder
        test_image = paths.image_asset_folder / "image_001.png"
        test_image.touch()

        # Initially no image
        assert not assets.has_image(0)

        # After setting image
        assets.set_scene_image(0, test_image)
        assert assets.has_image(0)

        # File doesn't exist
        assets.image_assets[0] = paths.image_asset_folder / "nonexistent.png"
        assert not assets.has_image(0)

    def test_image_assets_get_missing_assets(self, tmp_path):
        """Test getting missing image assets."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = ImageAssets(paths)

        # Create some test files in story assets folder
        test_image1 = paths.image_asset_folder / "image_001.png"
        test_image1.touch()

        # Set up mixed scenario
        assets.set_scene_image(0, test_image1)  # Exists
        # For nonexistent file, we need to bypass validation by setting directly
        assets.ensure_index_exists(1)
        assets.image_assets[1] = (
            paths.image_asset_folder / "nonexistent.png"
        )  # Doesn't exist
        assets.image_assets.append(None)  # No asset set

        missing = assets.get_missing_image_assets()

        assert 0 not in missing  # Has valid file
        assert 1 in missing  # File doesn't exist
        assert 2 in missing  # No asset set

    def test_image_assets_save_and_load(self, tmp_path):
        """Test saving and loading image assets."""
        paths1 = VideoCreatorPaths(tmp_path, "test_story", 0)

        # Create test image files in story assets folder
        test_image1 = paths1.image_asset_folder / "image_001.png"
        test_image2 = paths1.image_asset_folder / "image_002.png"
        test_image1.touch()
        test_image2.touch()

        # Create and save assets
        assets1 = ImageAssets(paths1)
        assets1.set_scene_image(0, test_image1)
        assets1.set_scene_image(1, test_image2)
        assets1.save_assets_to_file()

        # Load in new instance with same paths
        paths2 = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets2 = ImageAssets(paths2)

        assert len(assets2.image_assets) == 2
        assert assets2.image_assets[0] == test_image1
        assert assets2.image_assets[1] == test_image2

    def test_image_assets_is_complete(self, tmp_path):
        """Test checking if all image assets are complete."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = ImageAssets(paths)

        # Initially complete (empty)
        assert assets.is_complete()

        # Create test files in story assets folder
        test_image1 = paths.image_asset_folder / "image_001.png"
        test_image1.touch()

        # Add valid asset
        assets.set_scene_image(0, test_image1)
        assert assets.is_complete()

        # Add invalid asset by bypassing validation
        assets.ensure_index_exists(1)
        assets.image_assets[1] = paths.image_asset_folder / "nonexistent.png"
        assert not assets.is_complete()

    def test_image_assets_len_and_getitem(self, tmp_path):
        """Test __len__ and __getitem__ methods."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = ImageAssets(paths)

        # Create test files in story assets folder
        test_image1 = paths.image_asset_folder / "image_001.png"
        test_image2 = paths.image_asset_folder / "image_002.png"
        test_image1.touch()
        test_image2.touch()

        assets.set_scene_image(0, test_image1)
        assets.set_scene_image(1, test_image2)

        assert len(assets) == 2
        assert assets[0] == test_image1
        assert assets[1] == test_image2
        assert assets[2] is None  # Out of bounds returns None

    def test_image_assets_corrupted_file_handling(self, tmp_path):
        """Test handling of corrupted asset files."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        asset_file = paths.image_asset_file

        # Create corrupted JSON file
        with open(asset_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        # Should handle corrupted file gracefully and start fresh
        assets = ImageAssets(paths)
        assert len(assets.image_assets) == 0

    def test_image_assets_invalid_file_structure(self, tmp_path):
        """Test handling of files with invalid structure."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        asset_file = paths.image_asset_file

        # Create file with invalid structure
        invalid_data = {"wrong_key": ["some", "data"]}
        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(invalid_data, f)

        # Should handle invalid structure gracefully
        assets = ImageAssets(paths)
        assert len(assets.image_assets) == 0

    def test_image_assets_file_permission_error(self, tmp_path):
        """Test handling of file permission errors."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = ImageAssets(paths)

        # Create test file in story assets folder
        test_image = paths.image_asset_folder / "image_001.png"
        test_image.touch()
        assets.set_scene_image(0, test_image)

        # Make the video_chapter_folder read-only to trigger permission error
        video_chapter_folder = paths.video_chapter_folder
        try:
            os.chmod(video_chapter_folder, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

            # Should handle permission error gracefully
            # This won't raise an exception, just fail silently or log
            assets.save_assets_to_file()

        finally:
            # Restore permissions for cleanup
            os.chmod(video_chapter_folder, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    def test_image_assets_large_asset_list(self, tmp_path):
        """Test handling of large numbers of assets."""
        paths1 = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = ImageAssets(paths1)

        # Create many test files in story assets folder
        test_files = []
        for i in range(100):
            test_file = paths1.image_asset_folder / f"image_{i:03d}.png"
            test_file.touch()
            test_files.append(test_file)
            assets.set_scene_image(i, test_file)

        # Verify all assets are properly managed
        assert len(assets) == 100
        assert assets.is_complete()

        # Save and reload
        assets.save_assets_to_file()
        paths2 = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets2 = ImageAssets(paths2)
        assert len(assets2) == 100
        assert assets2.is_complete()

        # Verify specific assets
        assert assets2[0] == test_files[0]
        assert assets2[50] == test_files[50]
        assert assets2[99] == test_files[99]
