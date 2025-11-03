"""
Unit tests for garbage_collector module.
"""

import json

import pytest

from ai_video_creator.utils import VideoCreatorPaths
from ai_video_creator.utils.garbage_collector import internal_clean_unused_assets


class TestGarbageCollector:
    """Test garbage collector functionality."""

    @pytest.fixture
    def video_creator_paths(self, tmp_path):
        """Create VideoCreatorPaths object for testing."""
        user_folder = tmp_path
        story_name = "test_story"
        chapter_index = 0

        # Create the necessary directory structure
        story_folder = user_folder / "stories" / story_name
        story_folder.mkdir(parents=True)

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

        # Create VideoCreatorPaths object
        paths = VideoCreatorPaths(user_folder, story_name, chapter_index)

        # Create narrator recipe
        narrator_recipe = {
            "narrator_data": [
                {
                    "prompt": "Test narrator 1",
                    "clone_voice_path": "default_assets/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                },
                {
                    "prompt": "Test narrator 2",
                    "clone_voice_path": "default_assets/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                },
            ],
        }

        narrator_recipe_file = paths.narrator_recipe_file
        with open(narrator_recipe_file, "w", encoding="utf-8") as f:
            json.dump(narrator_recipe, f)

        # Create image recipe
        image_recipe = {
            "image_data": [
                {
                    "prompt": "Test prompt 1",
                    "seed": 12345,
                    "recipe_type": "FluxImageRecipeType",
                },
                {
                    "prompt": "Test prompt 2",
                    "seed": 54321,
                    "recipe_type": "FluxImageRecipeType",
                },
            ],
        }

        image_recipe_file = paths.image_recipe_file
        with open(image_recipe_file, "w", encoding="utf-8") as f:
            json.dump(image_recipe, f)

        # Create video recipe
        video_recipe = {
            "video_data": [
                [
                    {
                        "media_path": None,
                        "color_match_media_path": None,
                        "audio_path": None,
                        "duration": 5.0,
                    }
                ],
                [
                    {
                        "media_path": None,
                        "color_match_media_path": None,
                        "audio_path": None,
                        "duration": 5.0,
                    }
                ],
            ],
        }

        video_recipe_file = paths.sub_video_recipe_file
        with open(video_recipe_file, "w", encoding="utf-8") as f:
            json.dump(video_recipe, f)

        return paths, user_folder, story_name, chapter_index

    def test_cleanup_removes_unused_narrator_and_image_files(self, video_creator_paths):
        """Test that cleanup removes unused files from narrator and image folders."""
        paths, user_folder, story_name, chapter_index = video_creator_paths

        # Create some asset files that should be kept
        valid_narrator1 = paths.narrator_asset_folder / "chapter_001_narrator_001.mp3"
        valid_image1 = paths.image_asset_folder / "chapter_001_image_001.png"
        valid_narrator2 = paths.narrator_asset_folder / "chapter_001_narrator_002.mp3"

        # Create some files that should be deleted (any file not in the keep list)
        old_narrator = paths.narrator_asset_folder / "old_narrator.mp3"
        old_image = paths.image_asset_folder / "old_image.png"
        temp_narrator = paths.narrator_asset_folder / "temp_file.txt"

        # Create all files
        for file_path in [
            valid_narrator1,
            valid_image1,
            valid_narrator2,
            old_narrator,
            old_image,
            temp_narrator,
        ]:
            file_path.touch()

        # Create asset files to track what should be kept
        narrator_assets = {
            "assets": [
                {"index": 1, "narrator": f"assets/narrators/{valid_narrator1.name}"},
                {"index": 2, "narrator": f"assets/narrators/{valid_narrator2.name}"},
            ]
        }
        with open(paths.narrator_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_assets, f)

        image_assets = {
            "assets": [
                {"index": 1, "image": f"assets/images/{valid_image1.name}"},
                {"index": 2, "image": None},
            ]
        }
        with open(paths.image_asset_file, "w", encoding="utf-8") as f:
            json.dump(image_assets, f)

        # Create empty video assets and recipe files
        video_assets = {"assets": []}
        with open(paths.sub_video_asset_file, "w", encoding="utf-8") as f:
            json.dump(video_assets, f)

        video_recipe = {"video_data": []}
        with open(paths.sub_video_recipe_file, "w", encoding="utf-8") as f:
            json.dump(video_recipe, f)

        assembler_assets = {"assets": []}
        with open(paths.video_assembler_asset_file, "w", encoding="utf-8") as f:
            json.dump(assembler_assets, f)

        # Run cleanup
        internal_clean_unused_assets(user_folder, story_name, chapter_index)

        # Verify that valid assets are kept
        assert valid_narrator1.exists()
        assert valid_image1.exists()
        assert valid_narrator2.exists()

        # Verify that ALL unused files are deleted (not just pattern-matched ones)
        assert not old_narrator.exists()
        assert not old_image.exists()
        assert not temp_narrator.exists()

    def test_cleanup_removes_unused_video_files(self, video_creator_paths):
        """Test that cleanup removes unused files from video folders."""
        paths, user_folder, story_name, chapter_index = video_creator_paths

        # Create some video asset files that should be kept
        valid_video1 = paths.sub_videos_asset_folder / "chapter_001_video_001.mp4"
        valid_sub1 = paths.sub_videos_asset_folder / "chapter_001_sub_001_000.mp4"
        valid_sub2 = paths.sub_videos_asset_folder / "chapter_001_sub_001_001.mp4"
        valid_last_frame = paths.image_asset_folder / "last_frame_001.png"

        # Create some files that should be deleted
        old_video = paths.sub_videos_asset_folder / "old_video.mp4"
        old_sub = paths.sub_videos_asset_folder / "old_sub.mp4"
        temp_file = paths.sub_videos_asset_folder / "temp.txt"

        # Create all files
        for file_path in [
            valid_video1,
            valid_sub1,
            valid_sub2,
            valid_last_frame,
            old_video,
            old_sub,
            temp_file,
        ]:
            file_path.touch()

        # Create asset files to track what should be kept
        video_assets = {
            "assets": [
                {
                    "index": 1,
                    "video_asset": f"assets/sub_videos/{valid_video1.name}",
                    "sub_video_assets": [
                        f"assets/sub_videos/{valid_sub1.name}",
                        f"assets/sub_videos/{valid_sub2.name}",
                    ],
                },
                {"index": 2, "video_asset": None, "sub_video_assets": []},
            ]
        }
        with open(paths.sub_video_asset_file, "w", encoding="utf-8") as f:
            json.dump(video_assets, f)

        # Update video recipe with media paths (empty recipe)
        video_recipe = {"video_data": []}
        with open(paths.sub_video_recipe_file, "w", encoding="utf-8") as f:
            json.dump(video_recipe, f)

        # Create empty narrator and image assets
        narrator_assets = {"assets": [{"index": 1, "narrator": None}]}
        with open(paths.narrator_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_assets, f)

        image_assets = {"assets": [{"index": 1, "image": f"assets/images/{valid_last_frame.name}"}]}
        with open(paths.image_asset_file, "w", encoding="utf-8") as f:
            json.dump(image_assets, f)

        assembler_assets = {"assets": []}
        with open(paths.video_assembler_asset_file, "w", encoding="utf-8") as f:
            json.dump(assembler_assets, f)

        # Run cleanup
        internal_clean_unused_assets(user_folder, story_name, chapter_index)

        # Verify that valid assets are kept
        assert valid_video1.exists()
        assert valid_sub1.exists()
        assert valid_sub2.exists()
        assert valid_last_frame.exists()

        # Verify that unused files are deleted
        assert not old_video.exists()
        assert not old_sub.exists()
        assert not temp_file.exists()

    def test_cleanup_handles_none_values_in_assets(self, video_creator_paths):
        """Test that cleanup properly handles None values in asset lists."""
        paths, user_folder, story_name, chapter_index = video_creator_paths

        # Create some files
        valid_narrator = paths.narrator_asset_folder / "valid_narrator.mp3"
        invalid_narrator = paths.narrator_asset_folder / "invalid_narrator.mp3"
        invalid_image = paths.image_asset_folder / "invalid_image.png"

        valid_narrator.touch()
        invalid_narrator.touch()
        invalid_image.touch()

        # Set only one asset, leaving others as None
        narrator_assets = {
            "assets": [
                {"index": 1, "narrator": f"assets/narrators/{valid_narrator.name}"},
                {"index": 2, "narrator": None},
            ]
        }
        with open(paths.narrator_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_assets, f)

        image_assets = {
            "assets": [
                {"index": 1, "image": None},
                {"index": 2, "image": None},
            ]
        }
        with open(paths.image_asset_file, "w", encoding="utf-8") as f:
            json.dump(image_assets, f)

        # Create empty video assets
        video_assets = {"assets": [{"index": 1, "video_asset": None, "sub_video_assets": []}]}
        with open(paths.sub_video_asset_file, "w", encoding="utf-8") as f:
            json.dump(video_assets, f)

        # Create empty video recipe
        video_recipe = {"video_data": []}
        with open(paths.sub_video_recipe_file, "w", encoding="utf-8") as f:
            json.dump(video_recipe, f)

        # Create empty video assembler assets
        assembler_assets = {"assets": []}
        with open(paths.video_assembler_asset_file, "w", encoding="utf-8") as f:
            json.dump(assembler_assets, f)

        # Run cleanup
        internal_clean_unused_assets(user_folder, story_name, chapter_index)

        # Verify that the valid file is kept
        assert valid_narrator.exists()

        # Verify that the unused files are deleted
        assert not invalid_narrator.exists()
        assert not invalid_image.exists()

    def test_cleanup_preserves_directories(self, video_creator_paths):
        """Test that cleanup only removes files, not directories."""
        paths, user_folder, story_name, chapter_index = video_creator_paths

        # Create subdirectories in asset folders
        narrator_sub_dir = paths.narrator_asset_folder / "subdirectory"
        image_sub_dir = paths.image_asset_folder / "subdirectory"
        video_sub_dir = paths.sub_videos_asset_folder / "subdirectory"

        narrator_sub_dir.mkdir()
        image_sub_dir.mkdir()
        video_sub_dir.mkdir()

        # Create files inside the subdirectories
        file_in_narrator_subdir = narrator_sub_dir / "test.txt"
        file_in_image_subdir = image_sub_dir / "test.txt"
        file_in_video_subdir = video_sub_dir / "test.txt"

        file_in_narrator_subdir.touch()
        file_in_image_subdir.touch()
        file_in_video_subdir.touch()

        # Create files in the main assets folders
        main_narrator_file = paths.narrator_asset_folder / "main.txt"
        main_image_file = paths.image_asset_folder / "main.txt"
        main_video_file = paths.sub_videos_asset_folder / "main.txt"

        main_narrator_file.touch()
        main_image_file.touch()
        main_video_file.touch()

        # Create empty asset files
        narrator_assets = {"assets": []}
        with open(paths.narrator_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_assets, f)

        image_assets = {"assets": []}
        with open(paths.image_asset_file, "w", encoding="utf-8") as f:
            json.dump(image_assets, f)

        video_assets = {"assets": []}
        with open(paths.sub_video_asset_file, "w", encoding="utf-8") as f:
            json.dump(video_assets, f)

        # Create empty video recipe
        video_recipe = {"video_data": []}
        with open(paths.sub_video_recipe_file, "w", encoding="utf-8") as f:
            json.dump(video_recipe, f)

        # Create empty video assembler assets
        assembler_assets = {"assets": []}
        with open(paths.video_assembler_asset_file, "w", encoding="utf-8") as f:
            json.dump(assembler_assets, f)

        # Run cleanup with no assets set (all files should be deleted except directories)
        internal_clean_unused_assets(user_folder, story_name, chapter_index)

        # Verify that the subdirectories still exist
        assert narrator_sub_dir.exists()
        assert narrator_sub_dir.is_dir()
        assert image_sub_dir.exists()
        assert image_sub_dir.is_dir()
        assert video_sub_dir.exists()
        assert video_sub_dir.is_dir()

        # Verify that files in main folders are deleted
        assert not main_narrator_file.exists()
        assert not main_image_file.exists()
        assert not main_video_file.exists()

        # Note: files in subdirectories are preserved because cleanup only
        # processes files directly in the asset folders, not recursively

    def test_cleanup_with_empty_folders(self, video_creator_paths):
        """Test that cleanup handles empty asset folders gracefully."""
        paths, user_folder, story_name, chapter_index = video_creator_paths

        # Create empty asset files
        narrator_assets = {"assets": []}
        with open(paths.narrator_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_assets, f)

        image_assets = {"assets": []}
        with open(paths.image_asset_file, "w", encoding="utf-8") as f:
            json.dump(image_assets, f)

        video_assets = {"assets": []}
        with open(paths.sub_video_asset_file, "w", encoding="utf-8") as f:
            json.dump(video_assets, f)

        # Create empty video recipe
        video_recipe = {"video_data": []}
        with open(paths.sub_video_recipe_file, "w", encoding="utf-8") as f:
            json.dump(video_recipe, f)

        # Create empty video assembler assets
        assembler_assets = {"assets": []}
        with open(paths.video_assembler_asset_file, "w", encoding="utf-8") as f:
            json.dump(assembler_assets, f)

        # Run cleanup - should not raise any errors
        internal_clean_unused_assets(user_folder, story_name, chapter_index)

        # Verify folders still exist
        assert paths.narrator_asset_folder.exists()
        assert paths.image_asset_folder.exists()
        assert paths.sub_videos_asset_folder.exists()
        assert paths.video_assembler_asset_folder.exists()

    def test_cleanup_removes_files_from_all_folders(self, video_creator_paths):
        """Test that cleanup processes all asset folders."""
        paths, user_folder, story_name, chapter_index = video_creator_paths

        # Create files in all folders
        narrator_file = paths.narrator_asset_folder / "test_narrator.mp3"
        image_file = paths.image_asset_folder / "test_image.png"
        sub_video_file = paths.sub_videos_asset_folder / "test_video.mp4"
        assembler_file = paths.video_assembler_asset_folder / "test_final.mp4"

        narrator_file.touch()
        image_file.touch()
        sub_video_file.touch()
        assembler_file.touch()

        # Create empty asset files (nothing to keep)
        narrator_assets = {"assets": []}
        with open(paths.narrator_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_assets, f)

        image_assets = {"assets": []}
        with open(paths.image_asset_file, "w", encoding="utf-8") as f:
            json.dump(image_assets, f)

        video_assets = {"assets": []}
        with open(paths.sub_video_asset_file, "w", encoding="utf-8") as f:
            json.dump(video_assets, f)

        # Create empty video recipe
        video_recipe = {"video_data": []}
        with open(paths.sub_video_recipe_file, "w", encoding="utf-8") as f:
            json.dump(video_recipe, f)

        assembler_assets = {"assets": []}
        with open(paths.video_assembler_asset_file, "w", encoding="utf-8") as f:
            json.dump(assembler_assets, f)

        # Run cleanup
        internal_clean_unused_assets(user_folder, story_name, chapter_index)

        # Verify ALL files are deleted from ALL folders
        assert not narrator_file.exists()
        assert not image_file.exists()
        assert not sub_video_file.exists()
        assert not assembler_file.exists()
