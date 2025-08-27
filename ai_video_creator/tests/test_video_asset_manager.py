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
        assert assets.narrator_assets == []
        assert assets.image_assets == []

    def test_assets_with_data(self, tmp_path):
        """Test video assets with actual data - core functionality."""
        asset_file = tmp_path / "assets.json"
        assets = VideoAssets(asset_file)

        assets.set_scene_narrator(0, Path("/path/to/narrator1.mp3"))
        assets.set_scene_image(0, Path("/path/to/image1.jpg"))
        assets.set_scene_narrator(1, Path("/path/to/narrator2.mp3"))
        assets.set_scene_image(1, Path("/path/to/image2.jpg"))

        assert len(assets.narrator_assets) == 2
        assert len(assets.image_assets) == 2
        assert assets.narrator_assets[0] == Path("/path/to/narrator1.mp3")
        assert assets.narrator_assets[1] == Path("/path/to/narrator2.mp3")
        assert assets.image_assets[0] == Path("/path/to/image1.jpg")
        assert assets.image_assets[1] == Path("/path/to/image2.jpg")

        assets.save_assets_to_file()
        assert asset_file.exists()

        with open(asset_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        expected_structure = {
            "assets": [
                {"index": 0, "narrator": "/path/to/narrator1.mp3", "image": "/path/to/image1.jpg"},
                {"index": 1, "narrator": "/path/to/narrator2.mp3", "image": "/path/to/image2.jpg"},
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

        assert len(assets.narrator_assets) == 2
        assert len(assets.image_assets) == 2
        assert assets.narrator_assets[0] == Path("/loaded/narrator1.mp3")
        assert assets.image_assets[0] == Path("/loaded/image1.jpg")
        assert assets.narrator_assets[1] == Path("/loaded/narrator2.mp3")
        assert assets.image_assets[1] == Path("/loaded/image2.jpg")

    def test_asset_completion_checking(self, tmp_path):
        """Test asset completion and missing asset detection."""
        asset_file = tmp_path / "assets.json"
        assets = VideoAssets(asset_file)

        # Empty assets should be complete
        assert assets.is_complete()

        # Create actual files for testing
        narrator1_file = tmp_path / "narrator1.mp3"
        narrator2_file = tmp_path / "narrator2.mp3"
        image1_file = tmp_path / "image1.jpg"
        
        narrator1_file.write_text("fake audio")
        narrator2_file.write_text("fake audio")
        image1_file.write_text("fake image")

        assets.set_scene_narrator(0, narrator1_file)
        assets.set_scene_image(0, image1_file)
        assets.set_scene_narrator(1, narrator2_file)
        # Missing image for scene 1

        assert not assets.is_complete()

        missing = assets.get_missing_assets()
        assert missing["narrator"] == []  # All narrator files exist
        assert missing["image"] == [1]    # Image for scene 1 is missing

        # Add the missing image
        image2_file = tmp_path / "image2.jpg"
        image2_file.write_text("fake image")
        assets.set_scene_image(1, image2_file)

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
        assert len(assets.narrator_assets) == 6
        assert len(assets.image_assets) == 6

        assert assets.narrator_assets[5] == Path("/path/to/narrator5.mp3")
        assert assets.image_assets[3] == Path("/path/to/image3.jpg")

        assert assets.narrator_assets[0] is None
        assert assets.narrator_assets[1] is None
        assert assets.image_assets[0] is None


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

        # Create a test recipe file in video folder
        video_folder = story_folder / "video"
        video_folder.mkdir()
        recipe_file = video_folder / "test_story_chapter_001_recipe.json"

        test_recipe = {
            "narrator_data": [
                {
                    "prompt": "Test narrator 1",
                    "clone_voice_path": f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                },
                {
                    "prompt": "Test narrator 2",
                    "clone_voice_path": f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                },
            ],
            "image_data": [
                {
                    "prompt": "Test prompt 1",
                    "seed": 12345,
                    "recipe_type": "FluxImageRecipeType",
                },
                {
                    "prompt": "Test prompt 2",
                    "seed": 67890,
                    "recipe_type": "FluxImageRecipeType",
                },
            ],
        }

        with open(recipe_file, "w", encoding="utf-8") as f:
            json.dump(test_recipe, f)

        return story_folder

    def test_asset_manager_initialization(self, story_setup_with_recipe):
        """Test VideoAssetManager initialization with recipe synchronization."""
        with patch("logging_utils.logger"):
            manager = VideoAssetManager(story_setup_with_recipe, 0)

            assert len(manager.recipe.narrator_data) == 2
            assert len(manager.recipe.image_data) == 2

            assert len(manager.video_assets.narrator_assets) == 2
            assert len(manager.video_assets.image_assets) == 2

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

            assert manager.video_assets.narrator_assets[0] == Path("/existing/narrator1.mp3")
            assert manager.video_assets.image_assets[0] == Path("/existing/image1.jpg")
            assert manager.video_assets.narrator_assets[1] == Path("/existing/narrator2.mp3")
            assert manager.video_assets.image_assets[1] == Path("/existing/image2.jpg")

            assert not manager.video_assets.is_complete()

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

            assert len(manager.video_assets.narrator_assets) == 2
            assert len(manager.video_assets.image_assets) == 2

            assert manager.video_assets.narrator_assets[0] == Path("/existing/narrator1.mp3")
            assert manager.video_assets.image_assets[0] == Path("/existing/image1.jpg")

            assert manager.video_assets.narrator_assets[1] is None
            assert manager.video_assets.image_assets[1] is None

            assert not manager.video_assets.is_complete()
