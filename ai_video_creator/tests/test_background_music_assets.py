"""
Unit tests for background_music_assets module.
"""

import json

from ai_video_creator.modules.background_music.background_music_assets import (
    BackgroundMusicAssets,
    BackgroundMusicAsset,
)
from ai_video_creator.utils.video_creator_paths import VideoCreatorPaths


class TestBackgroundMusicAssets:
    """Test BackgroundMusicAssets class."""

    def test_background_music_assets_initialization(self, tmp_path):
        """Test BackgroundMusicAssets initialization with empty file."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = BackgroundMusicAssets(paths)

        assert len(assets.background_music_assets) == 0

    def test_background_music_assets_load_existing_file(self, tmp_path):
        """Test loading existing background music assets file."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        asset_file = paths.background_music_asset_file

        # Create test asset files in story assets folder
        test_music1 = paths.background_music_asset_folder / "music_001.mp3"
        test_music2 = paths.background_music_asset_folder / "music_002.mp3"
        test_music1.touch()
        test_music2.touch()

        test_data = {
            "background_music_assets": [
                {"index": 1, "asset": str(paths.mask_asset_path(test_music1)), "volume": 0.8, "skip": False},
                {"index": 2, "asset": str(paths.mask_asset_path(test_music2)), "volume": 0.6, "skip": False},
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        assets = BackgroundMusicAssets(paths)

        assert len(assets.background_music_assets) == 2
        assert assets.background_music_assets[0].asset == test_music1
        assert assets.background_music_assets[0].volume == 0.8
        assert assets.background_music_assets[1].asset == test_music2
        assert assets.background_music_assets[1].volume == 0.6

    def test_background_music_assets_set_scene_music(self, tmp_path):
        """Test setting background music asset for a scene."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = BackgroundMusicAssets(paths)

        # Create test music file in story assets folder
        test_music = paths.background_music_asset_folder / "music_001.mp3"
        test_music.touch()

        # Set music using BackgroundMusicAsset object
        music_asset = BackgroundMusicAsset(asset=test_music, volume=0.7, skip=False)
        assets.background_music_assets.append(music_asset)
        assets.save_assets_to_file()

        assert len(assets.background_music_assets) == 1
        assert assets.background_music_assets[0].asset == test_music
        assert assets.background_music_assets[0].volume == 0.7

    def test_background_music_assets_has_music(self, tmp_path):
        """Test checking if background music exists for a scene."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = BackgroundMusicAssets(paths)

        # Create test music file in story assets folder
        test_music = paths.background_music_asset_folder / "music_001.mp3"
        test_music.touch()

        # Initially no music
        assert not assets.has_background_music(0)

        # After setting music
        assets.background_music_assets.append(BackgroundMusicAsset(asset=test_music, volume=0.5, skip=False))
        assets.save_assets_to_file()
        assert assets.has_background_music(0)

        # Set to None
        assets.background_music_assets[0] = None
        assert not assets.has_background_music(0)

    def test_background_music_assets_get_missing_assets(self, tmp_path):
        """Test getting missing background music assets."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = BackgroundMusicAssets(paths)

        # Create some test files in story assets folder
        test_music1 = paths.background_music_asset_folder / "music_001.mp3"
        test_music1.touch()

        # Set up mixed scenario - has_background_music only checks for None, not file existence
        assets.background_music_assets.append(BackgroundMusicAsset(asset=test_music1, volume=0.5, skip=False))  # Exists - not missing
        assets.background_music_assets.append(None)  # No asset set - missing

        missing = assets.get_missing_background_music()

        assert len(missing) == 1
        assert 1 in missing  # None asset

    def test_background_music_assets_is_complete(self, tmp_path):
        """Test checking if all background music assets are complete."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = BackgroundMusicAssets(paths)

        # Create test files
        test_music1 = paths.background_music_asset_folder / "music_001.mp3"
        test_music2 = paths.background_music_asset_folder / "music_002.mp3"
        test_music1.touch()
        test_music2.touch()

        # Complete scenario - all files exist
        assets.background_music_assets.append(BackgroundMusicAsset(asset=test_music1, volume=0.5, skip=False))
        assets.background_music_assets.append(BackgroundMusicAsset(asset=test_music2, volume=0.5, skip=False))
        assert assets.is_complete()

        # Incomplete scenario - missing file
        assets.background_music_assets.append(None)
        assert not assets.is_complete()

    def test_background_music_assets_save_and_reload(self, tmp_path):
        """Test saving and reloading background music assets."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets1 = BackgroundMusicAssets(paths)

        # Create and set test music files
        test_music1 = paths.background_music_asset_folder / "music_001.mp3"
        test_music2 = paths.background_music_asset_folder / "music_002.mp3"
        test_music1.touch()
        test_music2.touch()

        assets1.background_music_assets.append(BackgroundMusicAsset(asset=test_music1, volume=0.5, skip=False))
        assets1.background_music_assets.append(BackgroundMusicAsset(asset=test_music2, volume=0.5, skip=False))
        assets1.save_assets_to_file()

        # Load new instance
        assets2 = BackgroundMusicAssets(paths)

        # Verify data was loaded
        assert len(assets2.background_music_assets) == 2
        assert assets2.background_music_assets[0].asset == test_music1
        assert assets2.background_music_assets[1].asset == test_music2

    def test_background_music_assets_corrupted_file_handling(self, tmp_path):
        """Test handling of corrupted asset files."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)

        # Create corrupted JSON file
        with open(paths.background_music_asset_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        # Should handle corrupted file gracefully and start fresh
        assets = BackgroundMusicAssets(paths)
        assert len(assets.background_music_assets) == 0

        # Verify backup was created (backup_file_to_old creates .json.old, not .old)
        backup_file = paths.background_music_asset_file.parent / (
            paths.background_music_asset_file.name + ".old"
        )
        assert backup_file.exists()

    def test_background_music_assets_invalid_data_structure(self, tmp_path):
        """Test handling of files with invalid data structure."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)

        # Create file with invalid structure
        invalid_data = {"wrong_key": ["some", "data"]}
        with open(paths.background_music_asset_file, "w", encoding="utf-8") as f:
            json.dump(invalid_data, f)

        # Should handle invalid structure gracefully
        assets = BackgroundMusicAssets(paths)
        assert len(assets.background_music_assets) == 0

    def test_background_music_assets_get_used_assets_list(self, tmp_path):
        """Test getting list of used background music assets."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = BackgroundMusicAssets(paths)

        # Create test files
        test_music1 = paths.background_music_asset_folder / "music_001.mp3"
        test_music2 = paths.background_music_asset_folder / "music_002.mp3"
        test_music1.touch()
        test_music2.touch()

        assets.background_music_assets.append(BackgroundMusicAsset(asset=test_music1, volume=0.5, skip=False))
        assets.background_music_assets.append(BackgroundMusicAsset(asset=test_music2, volume=0.5, skip=False))
        assets.background_music_assets.append(None)  # Unused slot

        used_assets = assets.get_used_assets_list()

        assert len(used_assets) == 2
        assert test_music1 in used_assets
        assert test_music2 in used_assets

    def test_background_music_assets_path_masking(self, tmp_path):
        """Test that paths are properly masked when saved."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = BackgroundMusicAssets(paths)

        # Create test file
        test_music = paths.background_music_asset_folder / "music_001.mp3"
        test_music.touch()

        assets.background_music_assets.append(BackgroundMusicAsset(asset=test_music, volume=0.5, skip=False))
        assets.save_assets_to_file()

        # Read saved file directly
        with open(paths.background_music_asset_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        # Check that path is masked (relative, not absolute)
        saved_path = saved_data["background_music_assets"][0]["asset"]
        assert not saved_path.startswith("/")
        assert saved_path.startswith("assets/")

    def test_background_music_assets_empty_list_initialization(self, tmp_path):
        """Test that assets can handle empty initialization."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)

        # Create file with empty assets list
        test_data = {"background_music_assets": []}
        with open(paths.background_music_asset_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        assets = BackgroundMusicAssets(paths)
        assert len(assets.background_music_assets) == 0
        assert assets.is_complete()  # Empty is complete

    def test_background_music_assets_multiple_scenes_same_file(self, tmp_path):
        """Test using the same music file for multiple scenes."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        assets = BackgroundMusicAssets(paths)

        # Create single test file
        test_music = paths.background_music_asset_folder / "music_001.mp3"
        test_music.touch()

        # Use same file for multiple scenes
        assets.background_music_assets.append(BackgroundMusicAsset(asset=test_music, volume=0.5, skip=False))
        assets.background_music_assets.append(BackgroundMusicAsset(asset=test_music, volume=0.5, skip=False))
        assets.background_music_assets.append(BackgroundMusicAsset(asset=test_music, volume=0.5, skip=False))

        assert len(assets.background_music_assets) == 3
        assert assets.background_music_assets[0].asset == test_music
        assert assets.background_music_assets[1].asset == test_music
        assert assets.background_music_assets[2].asset == test_music
        assert assets.is_complete()
