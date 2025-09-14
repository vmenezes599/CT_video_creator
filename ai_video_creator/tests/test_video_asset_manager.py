"""
Unit tests for video_asset_manager module.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_video_creator.modules.video import SubVideoAssetManager


class TestVideoAssetManager:
    """Test VideoAssetManager class - focuses on asset generation coordination."""

    @pytest.fixture
    def story_setup_with_recipe(self, tmp_path):
        """Create a story folder with recipe file."""
        story_folder = tmp_path / "test_story"
        story_folder.mkdir()

        # Create prompts folder and file
        prompts_folder = story_folder / "prompts"
        prompts_folder.mkdir()

        # Create a test chapter prompt
        chapter_prompt = {
            "prompts": [
                {
                    "narrator": "Test narrator 1",
                    "visual_description": "Test description 1",
                    "visual_prompt": "Test prompt 1",
                },
                {
                    "narrator": "Test narrator 2",
                    "visual_description": "Test description 2",
                    "visual_prompt": "Test prompt 2",
                },
            ]
        }

        prompt_file = prompts_folder / "chapter_001.json"
        with open(prompt_file, "w", encoding="utf-8") as f:
            json.dump(chapter_prompt, f)

        # Create video folder and necessary files
        video_folder = story_folder / "video"
        video_folder.mkdir()

        # Create narrator and image assets file (dependency)
        narrator_image_asset_file = (
            video_folder / "test_story_chapter_001_narrator_and_image_assets.json"
        )
        narrator_image_data = {
            "assets": [
                {"narrator": "/path/to/narrator1.mp3", "image": "/path/to/image1.jpg"},
                {"narrator": "/path/to/narrator2.mp3", "image": "/path/to/image2.jpg"},
            ]
        }
        with open(narrator_image_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_image_data, f)

        # Create a test video recipe file
        recipe_file = video_folder / "test_story_chapter_001_video_recipe.json"
        test_recipe = {
            "video_data": [
                {
                    "index": 1,
                    "recipe_list": [
                        {
                            "prompt": "Test description 1",
                            "media_path": "/path/to/image1.jpg",
                            "seed": 12345,
                            "recipe_type": "WanVideoRecipeType",
                        },
                        {
                            "prompt": "Test description 1",
                            "media_path": None,
                            "seed": 67890,
                            "recipe_type": "WanVideoRecipeType",
                        },
                    ],
                },
                {
                    "index": 2,
                    "recipe_list": [
                        {
                            "prompt": "Test description 2",
                            "media_path": "/path/to/image2.jpg",
                            "seed": 11111,
                            "recipe_type": "WanVideoRecipeType",
                        },
                        {
                            "prompt": "Test description 2",
                            "media_path": None,
                            "seed": 22222,
                            "recipe_type": "WanVideoRecipeType",
                        },
                    ],
                },
            ]
        }

        with open(recipe_file, "w", encoding="utf-8") as f:
            json.dump(test_recipe, f)

        return story_folder

    def test_asset_manager_initialization(self, story_setup_with_recipe):
        """Test VideoAssetManager initialization with recipe synchronization."""
        with patch("logging_utils.logger"):
            manager = SubVideoAssetManager(story_setup_with_recipe, 0)

            assert len(manager.recipe.video_data) == 2
            assert len(manager.video_assets.assembled_sub_video) == 2
            assert len(manager.video_assets.sub_video_assets) == 2

            # Initially, no videos should exist
            missing = manager.video_assets.get_missing_videos()
            assert missing == [0, 1]

    def test_asset_manager_creates_asset_file(self, story_setup_with_recipe):
        """Test that VideoAssetManager creates and manages asset files properly."""
        with patch("logging_utils.logger"):
            manager = SubVideoAssetManager(story_setup_with_recipe, 0)

            manager.video_assets.set_scene_video(0, Path("/generated/video_001.mp4"))
            manager.video_assets.set_scene_sub_video(
                0, 0, Path("/generated/sub_video_001_01.mp4")
            )
            manager.video_assets.set_scene_sub_video(
                0, 1, Path("/generated/sub_video_001_02.mp4")
            )
            manager.video_assets.save_assets_to_file()

            asset_file = manager.video_assets.asset_file_path
            assert asset_file.exists()

            with open(asset_file, "r", encoding="utf-8") as f:
                saved_data = json.load(f)

            assert "assets" in saved_data
            assert len(saved_data["assets"]) == 2
            assert saved_data["assets"][0]["video_asset"] == "/generated/video_001.mp4"
            assert len(saved_data["assets"][0]["sub_video_assets"]) == 2
            assert (
                saved_data["assets"][0]["sub_video_assets"][0]
                == "/generated/sub_video_001_01.mp4"
            )
            assert (
                saved_data["assets"][0]["sub_video_assets"][1]
                == "/generated/sub_video_001_02.mp4"
            )
            assert saved_data["assets"][1]["video_asset"] is None
            assert saved_data["assets"][1]["sub_video_assets"] == []

    def test_asset_manager_with_existing_assets(self, story_setup_with_recipe):
        """Test VideoAssetManager loading existing asset files."""
        video_folder = story_setup_with_recipe / "video"
        video_folder.mkdir(parents=True, exist_ok=True)
        asset_file = video_folder / "test_story_chapter_001_video_assets.json"

        existing_data = {
            "assets": [
                {
                    "video_asset": "/existing/video1.mp4",
                    "sub_video_assets": ["/existing/sub1.mp4", "/existing/sub2.mp4"],
                },
                {
                    "video_asset": "/existing/video2.mp4",
                    "sub_video_assets": ["/existing/sub3.mp4"],
                },
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f)

        with patch("logging_utils.logger"):
            manager = SubVideoAssetManager(story_setup_with_recipe, 0)

            assert manager.video_assets.assembled_sub_video[0] == Path("/existing/video1.mp4")
            assert manager.video_assets.assembled_sub_video[1] == Path("/existing/video2.mp4")
            assert len(manager.video_assets.sub_video_assets[0]) == 2
            assert manager.video_assets.sub_video_assets[0][0] == Path(
                "/existing/sub1.mp4"
            )
            assert manager.video_assets.sub_video_assets[0][1] == Path(
                "/existing/sub2.mp4"
            )
            assert len(manager.video_assets.sub_video_assets[1]) == 1
            assert manager.video_assets.sub_video_assets[1][0] == Path(
                "/existing/sub3.mp4"
            )

    def test_asset_synchronization_different_sizes(self, story_setup_with_recipe):
        """Test asset synchronization when asset file has different size than recipe."""
        video_folder = story_setup_with_recipe / "video"
        video_folder.mkdir(parents=True, exist_ok=True)
        asset_file = video_folder / "test_story_chapter_001_video_assets.json"

        existing_data = {
            "assets": [
                {
                    "video_asset": "/existing/video1.mp4",
                    "sub_video_assets": ["/existing/sub1.mp4"],
                }
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f)

        with patch("logging_utils.logger"):
            manager = SubVideoAssetManager(story_setup_with_recipe, 0)

            assert len(manager.video_assets.assembled_sub_video) == 2
            assert len(manager.video_assets.sub_video_assets) == 2

            assert manager.video_assets.assembled_sub_video[0] == Path("/existing/video1.mp4")
            assert len(manager.video_assets.sub_video_assets[0]) == 1
            assert manager.video_assets.sub_video_assets[0][0] == Path(
                "/existing/sub1.mp4"
            )

            assert manager.video_assets.assembled_sub_video[1] is None
            assert manager.video_assets.sub_video_assets[1] == []

    def test_cleanup_assets_removes_unused_files(self, story_setup_with_recipe):
        """Test that cleanup_assets removes files not referenced in assets."""
        video_folder = story_setup_with_recipe / "video"
        video_folder.mkdir(parents=True, exist_ok=True)
        assets_folder = video_folder / "assets" / "video"
        assets_folder.mkdir(parents=True, exist_ok=True)

        # Create some asset files that should be kept
        valid_video1 = assets_folder / "chapter_001_video_001.mp4"
        valid_sub1 = assets_folder / "chapter_001_sub_video_001_01.mp4"
        valid_sub2 = assets_folder / "chapter_001_sub_video_001_02.mp4"

        # Create some files that should be deleted
        old_video = assets_folder / "old_video.mp4"
        old_sub = assets_folder / "old_sub.mp4"
        temp_file = assets_folder / "temp.txt"

        # Create all files
        for file_path in [
            valid_video1,
            valid_sub1,
            valid_sub2,
            old_video,
            old_sub,
            temp_file,
        ]:
            file_path.touch()

        with patch("logging_utils.logger"):
            manager = SubVideoAssetManager(story_setup_with_recipe, 0)

            # Set up some assets to be kept
            manager.video_assets.set_scene_video(0, valid_video1)
            manager.video_assets.set_scene_sub_video(0, 0, valid_sub1)
            manager.video_assets.set_scene_sub_video(0, 1, valid_sub2)
            # Note: scene 1 has no assets (None)

            # Run cleanup
            manager.clean_unused_assets()

            # Verify that valid assets are kept
            assert valid_video1.exists()
            assert valid_sub1.exists()
            assert valid_sub2.exists()

            # Verify that unused files are deleted
            assert not old_video.exists()
            assert not old_sub.exists()
            assert not temp_file.exists()

    def test_cleanup_assets_handles_none_values_in_assets(
        self, story_setup_with_recipe
    ):
        """Test that cleanup_assets properly handles None values in asset lists."""
        video_folder = story_setup_with_recipe / "video"
        video_folder.mkdir(parents=True, exist_ok=True)
        assets_folder = video_folder / "assets" / "video"
        assets_folder.mkdir(parents=True, exist_ok=True)

        # Create some files
        valid_file = assets_folder / "valid_asset.mp4"
        invalid_file = assets_folder / "should_be_deleted.mp4"

        valid_file.touch()
        invalid_file.touch()

        with patch("logging_utils.logger"):
            manager = SubVideoAssetManager(story_setup_with_recipe, 0)

            # Set only one asset, leaving others as None
            manager.video_assets.set_scene_video(0, valid_file)
            # manager.video_assets.video_assets[1] is None
            # manager.video_assets.sub_video_assets[0] and [1] are empty lists

            # Run cleanup
            manager.clean_unused_assets()

            # Verify that the valid file is kept
            assert valid_file.exists()

            # Verify that the unused file is deleted
            assert not invalid_file.exists()

    def test_cleanup_assets_preserves_directories(self, story_setup_with_recipe):
        """Test that cleanup_assets only removes files, not directories."""
        video_folder = story_setup_with_recipe / "video"
        video_folder.mkdir(parents=True, exist_ok=True)
        assets_folder = video_folder / "assets" / "video"
        assets_folder.mkdir(parents=True, exist_ok=True)

        # Create a subdirectory
        sub_dir = assets_folder / "subdirectory"
        sub_dir.mkdir()

        # Create a file inside the subdirectory
        file_in_subdir = sub_dir / "file.txt"
        file_in_subdir.touch()

        # Create a file in the main assets folder
        main_file = assets_folder / "main_file.txt"
        main_file.touch()

        with patch("logging_utils.logger"):
            manager = SubVideoAssetManager(story_setup_with_recipe, 0)

            # Run cleanup with no assets set (all should be deleted except directories)
            manager.clean_unused_assets()

            # Verify that the subdirectory still exists
            assert sub_dir.exists()
            assert sub_dir.is_dir()

            # Verify that files are deleted
            assert not main_file.exists()
            # Note: file_in_subdir should still exist because cleanup only processes
            # files directly in assets_folder, not in subdirectories

    def test_generate_video_assets_workflow(self, story_setup_with_recipe):
        """Test the video asset generation workflow."""
        # Create valid narrator and image assets first
        video_folder = story_setup_with_recipe / "video"
        narrator_image_asset_file = (
            video_folder / "test_story_chapter_001_narrator_and_image_assets.json"
        )

        # Create temp files to simulate existing assets
        temp_narrator1 = story_setup_with_recipe / "temp_narrator1.mp3"
        temp_narrator2 = story_setup_with_recipe / "temp_narrator2.mp3"
        temp_image1 = story_setup_with_recipe / "temp_image1.jpg"
        temp_image2 = story_setup_with_recipe / "temp_image2.jpg"

        for temp_file in [temp_narrator1, temp_narrator2, temp_image1, temp_image2]:
            temp_file.write_text("fake content")

        complete_narrator_image_data = {
            "assets": [
                {"narrator": str(temp_narrator1), "image": str(temp_image1)},
                {"narrator": str(temp_narrator2), "image": str(temp_image2)},
            ]
        }
        with open(narrator_image_asset_file, "w", encoding="utf-8") as f:
            json.dump(complete_narrator_image_data, f)

        with patch("logging_utils.logger"):
            manager = SubVideoAssetManager(story_setup_with_recipe, 0)

            # Mock the video generation process
            with patch.object(manager, "_generate_video_asset") as mock_generate:
                manager.generate_video_assets()

                # Should attempt to generate videos for missing scenes
                missing_videos = manager.video_assets.get_missing_videos()
                assert mock_generate.call_count == len(missing_videos)

    def test_generate_video_assets_skips_when_image_assets_missing(
        self, story_setup_with_recipe
    ):
        """Test that video generation is skipped when image assets are missing."""
        with patch("logging_utils.logger"):
            manager = SubVideoAssetManager(story_setup_with_recipe, 0)

            # The default setup has incomplete narrator and image assets
            # Should skip video generation
            with patch.object(manager, "_generate_video_asset") as mock_generate:
                manager.generate_video_assets()

                # Should not attempt to generate any videos
                mock_generate.assert_not_called()

    def test_sub_video_file_path_generation(self, story_setup_with_recipe):
        """Test sub-video file path generation."""
        with patch("logging_utils.logger"):
            manager = SubVideoAssetManager(story_setup_with_recipe, 0)

            # Test path generation
            path1 = manager._generate_sub_video_file_path(0, 0)
            path2 = manager._generate_sub_video_file_path(1, 2)

            assert "chapter_001_sub_video_001_01.mp4" in str(path1)
            assert "chapter_001_sub_video_002_03.mp4" in str(path2)

    def test_video_file_path_generation(self, story_setup_with_recipe):
        """Test main video file path generation."""
        with patch("logging_utils.logger"):
            manager = SubVideoAssetManager(story_setup_with_recipe, 0)

            # Test path generation
            path1 = manager._generate_video_file_path(0)
            path2 = manager._generate_video_file_path(1)

            assert "chapter_001_video_001.mp4" in str(path1)
            assert "chapter_001_video_002.mp4" in str(path2)
