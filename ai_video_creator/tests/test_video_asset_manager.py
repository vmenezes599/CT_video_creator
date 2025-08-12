"""
Unit tests for video_asset_manager module.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_video_creator.modules.video_asset_manager import VideoAssets, VideoAssetManager
from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER


class TestVideoAssets:
    """Test VideoAssets class - focuses on JSON file management."""

    def test_empty_assets_creation(self, tmp_path):
        """Test creating empty video assets."""
        asset_file = tmp_path / "assets.json"
        assets = VideoAssets(asset_file)

        assert assets.asset_file_path == asset_file
        assert assets.narrator_list == []
        assert assets.image_list == []

    def test_assets_with_data(self, tmp_path):
        """Test video assets with actual data - core functionality."""
        asset_file = tmp_path / "assets.json"
        assets = VideoAssets(asset_file)

        assets.set_scene_narrator(0, Path("/path/to/narrator1.mp3"))
        assets.set_scene_image(0, Path("/path/to/image1.jpg"))
        assets.set_scene_narrator(1, Path("/path/to/narrator2.mp3"))
        assets.set_scene_image(1, Path("/path/to/image2.jpg"))

        assert len(assets.narrator_list) == 2
        assert len(assets.image_list) == 2
        assert assets.narrator_list[0] == "/path/to/narrator1.mp3"
        assert assets.image_list[0] == "/path/to/image1.jpg"
        assert assets.narrator_list[1] == "/path/to/narrator2.mp3"
        assert assets.image_list[1] == "/path/to/image2.jpg"

        assets.save_assets_to_file()
        assert asset_file.exists()

        with open(asset_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        expected_structure = {
            "assets": [
                {"narrator": "/path/to/narrator1.mp3", "image": "/path/to/image1.jpg"},
                {"narrator": "/path/to/narrator2.mp3", "image": "/path/to/image2.jpg"},
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

        assets = VideoAssets(asset_file)

        assert len(assets.narrator_list) == 2
        assert len(assets.image_list) == 2
        assert assets.narrator_list[0] == "/loaded/narrator1.mp3"
        assert assets.image_list[0] == "/loaded/image1.jpg"
        assert assets.narrator_list[1] == "/loaded/narrator2.mp3"
        assert assets.image_list[1] == "/loaded/image2.jpg"

    def test_asset_completion_checking(self, tmp_path):
        """Test asset completion and missing asset detection."""
        asset_file = tmp_path / "assets.json"
        assets = VideoAssets(asset_file)

        # Empty assets should be complete
        assert assets.is_complete()

        assets.set_scene_narrator(0, Path("/path/to/narrator1.mp3"))
        assets.set_scene_image(0, Path("/path/to/image1.jpg"))
        assets.set_scene_narrator(1, Path("/path/to/narrator2.mp3"))
        # Missing image for scene 1

        assert not assets.is_complete()

        missing = assets.get_missing_assets()
        assert missing["narrator"] == []
        assert missing["image"] == [1]

        assets.set_scene_image(1, Path("/path/to/image2.jpg"))

        assert assets.is_complete()
        missing = assets.get_missing_assets()
        assert missing["narrator"] == []
        assert missing["image"] == []

    def test_asset_index_management(self, tmp_path):
        """Test that assets can be set at non-sequential indices."""
        asset_file = tmp_path / "assets.json"
        assets = VideoAssets(asset_file)

        assets.set_scene_narrator(5, Path("/path/to/narrator5.mp3"))
        assets.set_scene_image(3, Path("/path/to/image3.jpg"))

        # Both lists extend to max index + 1 due to _ensure_index_exists behavior
        assert len(assets.narrator_list) == 6
        assert len(assets.image_list) == 6

        assert assets.narrator_list[5] == "/path/to/narrator5.mp3"
        assert assets.image_list[3] == "/path/to/image3.jpg"

        assert assets.narrator_list[0] == ""
        assert assets.narrator_list[1] == ""
        assert assets.image_list[0] == ""


class TestVideoAssetManager:
    """Test VideoAssetManager class - focuses on asset generation coordination."""

    @pytest.fixture
    def story_setup_with_recipe(self, tmp_path):
        """Create a story folder with recipe file."""
        story_folder = tmp_path / "test_story"
        prompts_folder = story_folder / "prompts"
        recipes_folder = story_folder / "recipes"
        prompts_folder.mkdir(parents=True)
        recipes_folder.mkdir(parents=True)

        chapter_prompt = {
            "prompts": [
                {
                    "narrator": "First narrator text",
                    "visual_description": "First visual description",
                    "visual_prompt": "First visual prompt",
                },
                {
                    "narrator": "Second narrator text",
                    "visual_description": "Second visual description",
                    "visual_prompt": "Second visual prompt",
                },
            ]
        }

        prompt_file = prompts_folder / "chapter_001.json"
        with open(prompt_file, "w", encoding="utf-8") as f:
            json.dump(chapter_prompt, f)

        recipe_data = {
            "narrator_data": [
                {
                    "prompt": "First narrator text",
                    "clone_voice_path": f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3",
                    "recipe_type": "SparkTTSRecipeType",
                },
                {
                    "prompt": "Second narrator text",
                    "clone_voice_path": f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3",
                    "recipe_type": "SparkTTSRecipeType",
                },
            ],
            "image_data": [
                {
                    "prompt": "First visual prompt",
                    "seed": 12345,
                    "recipe_type": "FluxImageRecipeType",
                },
                {
                    "prompt": "Second visual prompt",
                    "seed": 67890,
                    "recipe_type": "FluxImageRecipeType",
                },
            ],
        }

        video_folder = story_folder / "video"
        video_folder.mkdir(parents=True)
        recipe_file = video_folder / "test_story_chapter_001_recipe.json"
        with open(recipe_file, "w", encoding="utf-8") as f:
            json.dump(recipe_data, f)

        return story_folder

    def test_asset_manager_initialization(self, story_setup_with_recipe):
        """Test VideoAssetManager initialization with recipe synchronization."""
        with patch("logging_utils.logger"):
            manager = VideoAssetManager(story_setup_with_recipe, 0)

            assert len(manager.recipe.narrator_data) == 2
            assert len(manager.recipe.image_data) == 2

            assert len(manager.video_assets.narrator_list) == 2
            assert len(manager.video_assets.image_list) == 2

            assert not manager.video_assets.is_complete()
            missing = manager.video_assets.get_missing_assets()
            assert missing["narrator"] == [0, 1]
            assert missing["image"] == [0, 1]

    def test_asset_manager_creates_asset_file(self, story_setup_with_recipe):
        """Test that VideoAssetManager creates and manages asset files properly."""
        with patch("logging_utils.logger"):
            manager = VideoAssetManager(story_setup_with_recipe, 0)

            manager.video_assets.set_scene_narrator(
                0, Path("/generated/narrator_001.mp3")
            )
            manager.video_assets.set_scene_image(0, Path("/generated/image_001.jpg"))
            manager.video_assets.save_assets_to_file()

            asset_file = manager.video_assets.asset_file_path
            assert asset_file.exists()

            with open(asset_file, "r", encoding="utf-8") as f:
                saved_data = json.load(f)

            assert "assets" in saved_data
            assert len(saved_data["assets"]) == 2
            assert saved_data["assets"][0]["narrator"] == "/generated/narrator_001.mp3"
            assert saved_data["assets"][0]["image"] == "/generated/image_001.jpg"
            assert saved_data["assets"][1]["narrator"] == ""
            assert saved_data["assets"][1]["image"] == ""

    def test_asset_manager_with_existing_assets(self, story_setup_with_recipe):
        """Test VideoAssetManager loading existing asset files."""
        video_folder = story_setup_with_recipe / "video"
        video_folder.mkdir(parents=True, exist_ok=True)
        asset_file = video_folder / "test_story_chapter_001_video_assets.json"

        existing_data = {
            "assets": [
                {
                    "narrator": "/existing/narrator1.mp3",
                    "image": "/existing/image1.jpg",
                },
                {
                    "narrator": "/existing/narrator2.mp3",
                    "image": "/existing/image2.jpg",
                },
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f)

        with patch("logging_utils.logger"):
            manager = VideoAssetManager(story_setup_with_recipe, 0)

            assert manager.video_assets.narrator_list[0] == "/existing/narrator1.mp3"
            assert manager.video_assets.image_list[0] == "/existing/image1.jpg"
            assert manager.video_assets.narrator_list[1] == "/existing/narrator2.mp3"
            assert manager.video_assets.image_list[1] == "/existing/image2.jpg"

            assert manager.video_assets.is_complete()

    def test_asset_synchronization_different_sizes(self, story_setup_with_recipe):
        """Test asset synchronization when asset file has different size than recipe."""
        video_folder = story_setup_with_recipe / "video"
        video_folder.mkdir(parents=True, exist_ok=True)
        asset_file = video_folder / "test_story_chapter_001_video_assets.json"

        existing_data = {
            "assets": [
                {"narrator": "/existing/narrator1.mp3", "image": "/existing/image1.jpg"}
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f)

        with patch("logging_utils.logger"):
            manager = VideoAssetManager(story_setup_with_recipe, 0)

            assert len(manager.video_assets.narrator_list) == 2
            assert len(manager.video_assets.image_list) == 2

            assert manager.video_assets.narrator_list[0] == "/existing/narrator1.mp3"
            assert manager.video_assets.image_list[0] == "/existing/image1.jpg"

            assert manager.video_assets.narrator_list[1] == ""
            assert manager.video_assets.image_list[1] == ""

            assert not manager.video_assets.is_complete()
            missing = manager.video_assets.get_missing_assets()
            assert missing["narrator"] == [1]
            assert missing["image"] == [1]
