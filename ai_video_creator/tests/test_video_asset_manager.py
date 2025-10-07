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
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir()

        # Create narrator and image assets file (dependency)
        narrator_image_asset_file = chapter_folder / "narrator_and_image_assets.json"

        # Create asset files referenced in the recipe FIRST
        narrator_image_assets_folder = chapter_folder / "assets" / "narrator_and_image"
        narrator_image_assets_folder.mkdir(parents=True, exist_ok=True)

        # Create placeholder files
        (narrator_image_assets_folder / "narrator1.mp3").touch()
        (narrator_image_assets_folder / "narrator2.mp3").touch()
        (narrator_image_assets_folder / "image1.jpg").touch()
        (narrator_image_assets_folder / "image2.jpg").touch()
        (narrator_image_assets_folder / "color_match1.jpg").touch()
        (narrator_image_assets_folder / "color_match2.jpg").touch()

        # Use relative paths that point to the actual files we created
        narrator_image_data = {
            "assets": [
                {
                    "narrator": "assets/narrator_and_image/narrator1.mp3",
                    "image": "assets/narrator_and_image/image1.jpg",
                },
                {
                    "narrator": "assets/narrator_and_image/narrator2.mp3",
                    "image": "assets/narrator_and_image/image2.jpg",
                },
            ]
        }
        with open(narrator_image_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_image_data, f)

        # Create a test video recipe file
        recipe_file = chapter_folder / "sub_video_recipe.json"
        test_recipe = {
            "video_data": [
                {
                    "index": 1,
                    "extra_data": {},
                    "recipe_list": [
                        {
                            "prompt": "Test description 1",
                            "media_path": "assets/narrator_and_image/image1.jpg",
                            "color_match_media_path": "assets/narrator_and_image/color_match1.jpg",
                            "seed": 12345,
                            "recipe_type": "WanI2VRecipeType",
                        },
                        {
                            "prompt": "Test description 1",
                            "media_path": None,
                            "color_match_media_path": "assets/narrator_and_image/color_match1.jpg",
                            "seed": 67890,
                            "recipe_type": "WanT2VRecipeType",
                        },
                    ],
                },
                {
                    "index": 2,
                    "extra_data": {},
                    "recipe_list": [
                        {
                            "prompt": "Test description 2",
                            "media_path": "assets/narrator_and_image/image2.jpg",
                            "color_match_media_path": "assets/narrator_and_image/color_match2.jpg",
                            "seed": 11111,
                            "recipe_type": "WanI2VRecipeType",
                        },
                        {
                            "prompt": "Test description 2",
                            "media_path": None,
                            "color_match_media_path": "assets/narrator_and_image/color_match2.jpg",
                            "seed": 22222,
                            "recipe_type": "WanT2VRecipeType",
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
        manager = SubVideoAssetManager(story_setup_with_recipe, 0)

        assert len(manager.recipe.video_data) == 2
        assert len(manager.video_assets.assembled_sub_video) == 2
        assert len(manager.video_assets.sub_video_assets) == 2

        # Initially, no videos should exist
        missing = manager.video_assets.get_missing_videos()
        assert missing == [0, 1]

    def test_asset_manager_creates_asset_file(self, story_setup_with_recipe):
        """Test that VideoAssetManager creates and manages asset files properly."""
        manager = SubVideoAssetManager(story_setup_with_recipe, 0)

        # Create assets folder and test files within the allowed directory
        assets_folder = (
            story_setup_with_recipe / "video" / "chapter_001" / "assets" / "sub_videos"
        )
        assets_folder.mkdir(parents=True, exist_ok=True)

        test_video = assets_folder / "video_001.mp4"
        test_sub_video_1 = assets_folder / "sub_video_001_01.mp4"
        test_sub_video_2 = assets_folder / "sub_video_001_02.mp4"
        test_video.touch()
        test_sub_video_1.touch()
        test_sub_video_2.touch()

        manager.video_assets.set_scene_video(0, test_video)
        manager.video_assets.set_scene_sub_video(0, 0, test_sub_video_1)
        manager.video_assets.set_scene_sub_video(0, 1, test_sub_video_2)
        manager.video_assets.save_assets_to_file()

        asset_file = manager.video_assets.asset_file_path
        assert asset_file.exists()

        with open(asset_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert "assets" in saved_data
        assert len(saved_data["assets"]) == 2
        assert (
            saved_data["assets"][0]["video_asset"] == "assets/sub_videos/video_001.mp4"
        )
        assert len(saved_data["assets"][0]["sub_video_assets"]) == 2
        assert (
            saved_data["assets"][0]["sub_video_assets"][0]
            == "assets/sub_videos/sub_video_001_01.mp4"
        )
        assert (
            saved_data["assets"][0]["sub_video_assets"][1]
            == "assets/sub_videos/sub_video_001_02.mp4"
        )
        assert saved_data["assets"][1]["video_asset"] is None
        assert saved_data["assets"][1]["sub_video_assets"] == []

    def test_asset_manager_with_existing_assets(self, story_setup_with_recipe):
        """Test VideoAssetManager loading existing asset files."""
        video_folder = story_setup_with_recipe / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)
        asset_file = chapter_folder / "sub_video_assets.json"

        # Create actual asset files within the allowed directory
        assets_folder = chapter_folder / "assets" / "sub_videos"
        assets_folder.mkdir(parents=True, exist_ok=True)

        video1 = assets_folder / "video1.mp4"
        video2 = assets_folder / "video2.mp4"
        sub1 = assets_folder / "sub1.mp4"
        sub2 = assets_folder / "sub2.mp4"
        sub3 = assets_folder / "sub3.mp4"

        for file in [video1, video2, sub1, sub2, sub3]:
            file.touch()

        existing_data = {
            "assets": [
                {
                    "index": 1,
                    "video_asset": "assets/sub_videos/video1.mp4",
                    "sub_video_assets": [
                        "assets/sub_videos/sub1.mp4",
                        "assets/sub_videos/sub2.mp4",
                    ],
                },
                {
                    "index": 2,
                    "video_asset": "assets/sub_videos/video2.mp4",
                    "sub_video_assets": ["assets/sub_videos/sub3.mp4"],
                },
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f)

        manager = SubVideoAssetManager(story_setup_with_recipe, 0)

        assert manager.video_assets.assembled_sub_video[0] == video1
        assert manager.video_assets.assembled_sub_video[1] == video2
        assert len(manager.video_assets.sub_video_assets[0]) == 2
        assert manager.video_assets.sub_video_assets[0][0] == sub1
        assert manager.video_assets.sub_video_assets[0][1] == sub2
        assert len(manager.video_assets.sub_video_assets[1]) == 1
        assert manager.video_assets.sub_video_assets[1][0] == sub3

    def test_asset_synchronization_different_sizes(self, story_setup_with_recipe):
        """Test asset synchronization when asset file has different size than recipe."""
        video_folder = story_setup_with_recipe / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)
        asset_file = chapter_folder / "sub_video_assets.json"

        # Create actual asset files within the allowed directory
        assets_folder = chapter_folder / "assets" / "sub_videos"
        assets_folder.mkdir(parents=True, exist_ok=True)

        video1 = assets_folder / "video1.mp4"
        sub1 = assets_folder / "sub1.mp4"

        for file in [video1, sub1]:
            file.touch()

        existing_data = {
            "assets": [
                {
                    "index": 1,
                    "video_asset": "assets/sub_videos/video1.mp4",
                    "sub_video_assets": ["assets/sub_videos/sub1.mp4"],
                }
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f)

        manager = SubVideoAssetManager(story_setup_with_recipe, 0)

        assert len(manager.video_assets.assembled_sub_video) == 2
        assert len(manager.video_assets.sub_video_assets) == 2

        assert manager.video_assets.assembled_sub_video[0] == video1
        assert len(manager.video_assets.sub_video_assets[0]) == 1
        assert manager.video_assets.sub_video_assets[0][0] == sub1

        assert manager.video_assets.assembled_sub_video[1] is None
        assert manager.video_assets.sub_video_assets[1] == []

    def test_cleanup_assets_removes_unused_files(self, story_setup_with_recipe):
        """Test that cleanup_assets removes files not referenced in assets."""
        video_folder = story_setup_with_recipe / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)
        assets_folder = chapter_folder / "assets" / "sub_videos"
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
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)
        assets_folder = chapter_folder / "assets" / "sub_videos"
        assets_folder.mkdir(parents=True, exist_ok=True)

        # Create some files
        valid_file = assets_folder / "valid_asset.mp4"
        invalid_file = assets_folder / "should_be_deleted.mp4"

        valid_file.touch()
        invalid_file.touch()

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
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)
        assets_folder = chapter_folder / "assets" / "sub_videos"
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
        """Test the video asset generation workflow with minimal mocking."""
        # Create valid narrator and image assets first
        video_folder = story_setup_with_recipe / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)

        # Create separate narrator and image asset files for new architecture
        narrator_asset_file = chapter_folder / "narrator_assets.json"
        image_asset_file = chapter_folder / "image_assets.json"

        # Create actual asset files within the allowed directory
        narrator_image_folder = chapter_folder / "assets" / "narrator_and_image"
        narrator_image_folder.mkdir(parents=True, exist_ok=True)

        narrator1 = narrator_image_folder / "narrator1.mp3"
        narrator2 = narrator_image_folder / "narrator2.mp3"
        image1 = narrator_image_folder / "image1.jpg"
        image2 = narrator_image_folder / "image2.jpg"
        color_match1 = narrator_image_folder / "color_match1.jpg"
        color_match2 = narrator_image_folder / "color_match2.jpg"

        for temp_file in [
            narrator1,
            narrator2,
            image1,
            image2,
            color_match1,
            color_match2,
        ]:
            temp_file.write_text("fake content")

        # Create separate asset files using the paths that match the recipe
        narrator_data = {
            "assets": [
                {"index": 1, "narrator": "assets/narrator_and_image/narrator1.mp3"},
                {"index": 2, "narrator": "assets/narrator_and_image/narrator2.mp3"},
            ]
        }
        image_data = {
            "assets": [
                {"index": 1, "image": "assets/narrator_and_image/image1.jpg"},
                {"index": 2, "image": "assets/narrator_and_image/image2.jpg"},
            ]
        }

        with open(narrator_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_data, f)
        with open(image_asset_file, "w", encoding="utf-8") as f:
            json.dump(image_data, f)

        manager = SubVideoAssetManager(story_setup_with_recipe, 0)

        # Create a fake video generator that creates real files
        class FakeVideoGenerator:
            def generate_video(self, recipe, output_path):
                # Create actual file to test file operations
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(f"fake video for: {recipe.prompt}")
                return output_path

        # Mock only the generator creation, not the core business logic
        for scene_data in manager.recipe.video_data:
            for recipe in scene_data:
                recipe.GENERATOR = lambda: FakeVideoGenerator()

        # Also mock the concatenation function and FFmpeg operations since they require real video files
        with patch(
            "ai_video_creator.modules.video.sub_video_asset_manager.concatenate_videos_remove_last_frame_except_last"
        ) as mock_concat, patch(
            "ai_video_creator.modules.video.sub_video_asset_manager.extract_video_last_frame"
        ) as mock_extract:

            def fake_concat(input_videos, output_path):
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text("concatenated video")
                return output_path

            def fake_extract(video_path, last_frame_output_folder):
                # Create the output folder
                Path(last_frame_output_folder).mkdir(parents=True, exist_ok=True)
                # Create the actual output file path (like the real function does)
                video_stem = Path(video_path).stem
                last_frame_output_path = (
                    Path(last_frame_output_folder) / f"{video_stem}_last_frame.png"
                )
                last_frame_output_path.write_text("fake frame image")
                return last_frame_output_path

            mock_concat.side_effect = fake_concat
            mock_extract.side_effect = fake_extract

            # Test the actual workflow
            manager.generate_video_assets()

            # Verify business logic executed correctly
            missing_videos = manager.video_assets.get_missing_videos()
            assert len(missing_videos) == 0  # All videos should be generated

            # Verify files were actually created through the business logic
            assert len(manager.video_assets.assembled_sub_video) == 2
            assert len(manager.video_assets.sub_video_assets) == 2
            assert len(manager.video_assets.sub_video_assets[0]) > 0
            assert len(manager.video_assets.sub_video_assets[1]) > 0

            # Verify production code business logic worked correctly
            # Check that recipes were properly linked (next recipe should have media_path from previous)
            recipe_scene_1 = manager.recipe.video_data[0]
            recipe_scene_2 = manager.recipe.video_data[1]

            # Second recipe in each scene should have media_path set from first recipe's frame
            if len(recipe_scene_1) > 1:
                second_recipe = recipe_scene_1[1]
                assert hasattr(second_recipe, "media_path")
                assert second_recipe.media_path is not None
                # Should contain the generated frame path
                assert "_last_frame.png" in str(second_recipe.media_path)

            # Test that asset synchronization worked
            assert len(manager.video_assets.sub_video_assets) == len(
                manager.recipe.video_data
            )

            # Test that the asset files were created and have proper structure
            for scene_idx in range(2):
                scene_assets = manager.video_assets.sub_video_assets[scene_idx]
                assert (
                    len(scene_assets) > 0
                ), f"Scene {scene_idx} should have sub-video assets"

            # Test that assembled videos were created
            for scene_idx in range(2):
                assembled_video = manager.video_assets.assembled_sub_video[scene_idx]
                assert (
                    assembled_video is not None
                ), f"Scene {scene_idx} should have assembled video"

    def test_generate_video_assets_skips_when_assets_missing(
        self, story_setup_with_recipe
    ):
        """Test that video generation is skipped when narrator or image assets are missing."""
        video_folder = story_setup_with_recipe / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)

        # Create separate asset files with incomplete data
        narrator_asset_file = chapter_folder / "narrator_assets.json"
        image_asset_file = chapter_folder / "image_assets.json"

        # Create narrator assets folder and one file (incomplete)
        narrator_folder = chapter_folder / "assets" / "narrators"
        narrator_folder.mkdir(parents=True, exist_ok=True)
        narrator_file1 = narrator_folder / "narrator1.mp3"
        narrator_file1.write_text("narrator content 1")

        # Create only partial assets (missing second narrator and all images) using new format
        narrator_data = {
            "assets": [
                {"index": 1, "narrator": "assets/narrators/narrator1.mp3"},
                {"index": 2, "narrator": ""},  # Missing narrator
            ]
        }
        image_data = {
            "assets": [
                {"index": 1, "image": ""},  # Missing image
                {"index": 2, "image": ""},  # Missing image
            ]
        }

        with open(narrator_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_data, f)
        with open(image_asset_file, "w", encoding="utf-8") as f:
            json.dump(image_data, f)

        manager = SubVideoAssetManager(story_setup_with_recipe, 0)

        # Track if any video generation attempts were made
        generation_attempts = []

        class TrackingFakeGenerator:
            def generate_video(self, recipe, output_path):
                generation_attempts.append(f"Generated: {output_path.name}")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text("fake video")
                return output_path

        # Set up generator tracking without mocking core business logic
        for scene_data in manager.recipe.video_data:
            for recipe in scene_data:
                recipe.GENERATOR = lambda: TrackingFakeGenerator()

        # Test the actual business logic - should skip due to incomplete assets
        manager.generate_video_assets()

        # Verify no video generation occurred due to missing assets
        assert len(generation_attempts) == 0

        # Verify business logic correctly identified missing assets
        assert not manager._SubVideoAssetManager__narrator_assets.is_complete()
        assert not manager._SubVideoAssetManager__image_assets.is_complete()

        # Verify no video assets were created
        missing_videos = manager.video_assets.get_missing_videos()
        assert len(missing_videos) == 2  # Both scenes should still be missing

    def test_sub_video_file_path_generation(self, story_setup_with_recipe):
        """Test sub-video file path generation."""
        manager = SubVideoAssetManager(story_setup_with_recipe, 0)

        # Test path generation
        path1 = manager._generate_sub_video_file_path(0, 0)
        path2 = manager._generate_sub_video_file_path(1, 2)

        assert "chapter_001_sub_video_001_01.mp4" in str(path1)
        assert "chapter_001_sub_video_002_03.mp4" in str(path2)

    def test_video_file_path_generation(self, story_setup_with_recipe):
        """Test main video file path generation."""
        manager = SubVideoAssetManager(story_setup_with_recipe, 0)

        # Test path generation
        path1 = manager._generate_video_file_path(0)
        path2 = manager._generate_video_file_path(1)

        assert "chapter_001_video_001.mp4" in str(path1)
        assert "chapter_001_video_002.mp4" in str(path2)
