"""
Unit tests for video_recipe module.
"""

import json
from unittest.mock import patch

import pytest

from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER
from ai_video_creator.generators import WanVideoRecipe
from ai_video_creator.modules.video_recipe import (
    VideoRecipeFile,
    VideoRecipeBuilder,
    VideoRecipeDefaultSettings,
)


class TestVideoRecipeDefaultSettings:
    """Test VideoRecipeDefaultSettings class."""

    def test_default_settings(self):
        """Test that default settings have correct values."""
        assert (
            VideoRecipeDefaultSettings.NARRATOR_VOICE
            == f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3"
        )
        assert (
            VideoRecipeDefaultSettings.BACKGROUND_MUSIC
            == f"{DEFAULT_ASSETS_FOLDER}/background_music.mp3"
        )


class TestVideoRecipeFile:
    """Test VideoRecipeFile class."""

    def test_empty_recipe_creation(self, tmp_path):
        """Test creating an empty recipe."""
        recipe_path = tmp_path / "test_recipe.json"
        recipe = VideoRecipeFile(recipe_path)

        assert recipe.recipe_path == recipe_path
        assert recipe.video_data == []

    def test_recipe_with_data(self, tmp_path):
        """Test recipe with actual data - core functionality."""
        recipe_path = tmp_path / "test_recipe.json"
        recipe = VideoRecipeFile(recipe_path)

        # Add real video recipe data
        video_recipe = WanVideoRecipe(
            prompt="Test video prompt", media_path="/path/to/image.jpg", seed=12345
        )

        recipe.add_video_data([video_recipe])

        # Verify data was added correctly
        assert len(recipe.video_data) == 1
        assert len(recipe.video_data[0]) == 1  # One recipe in the list
        assert recipe.video_data[0][0].prompt == "Test video prompt"
        assert str(recipe.video_data[0][0].media_path) == "/path/to/image.jpg"
        assert recipe.video_data[0][0].seed == 12345

        # Verify file was created with correct structure
        assert recipe_path.exists()
        with open(recipe_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        # Check basic structure and key values
        assert "video_data" in saved_data
        assert len(saved_data["video_data"]) == 1

        # Check video data structure
        video = saved_data["video_data"][0]
        assert "index" in video
        assert "recipe_list" in video
        assert len(video["recipe_list"]) == 1

        recipe_data = video["recipe_list"][0]
        assert recipe_data["prompt"] == "Test video prompt"
        assert recipe_data["media_path"] == "/path/to/image.jpg"
        assert recipe_data["seed"] == 12345
        assert recipe_data["recipe_type"] == "WanVideoRecipeType"

    def test_recipe_loading_from_file(self, tmp_path):
        """Test loading recipe from existing file."""
        recipe_path = tmp_path / "existing_recipe.json"

        # Create a test file
        test_data = {
            "video_data": [
                {
                    "index": 1,
                    "recipe_list": [
                        {
                            "prompt": "Loaded video prompt",
                            "media_path": "/loaded/image.jpg",
                            "seed": 99999,
                            "recipe_type": "WanVideoRecipeType",
                        }
                    ],
                }
            ]
        }

        with open(recipe_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # Load the recipe
        recipe = VideoRecipeFile(recipe_path)

        # Verify data was loaded correctly
        assert len(recipe.video_data) == 1
        assert len(recipe.video_data[0]) == 1
        assert isinstance(recipe.video_data[0][0], WanVideoRecipe)
        assert recipe.video_data[0][0].prompt == "Loaded video prompt"
        assert str(recipe.video_data[0][0].media_path) == "/loaded/image.jpg"
        assert recipe.video_data[0][0].seed == 99999

    def test_recipe_loading_with_invalid_json(self, tmp_path):
        """Test graceful handling when JSON file is corrupted."""
        recipe_path = tmp_path / "corrupted_recipe.json"
        old_recipe_path = tmp_path / "corrupted_recipe.json.old"

        # Create a corrupted JSON file
        corrupted_content = "{ invalid json content"
        with open(recipe_path, "w", encoding="utf-8") as f:
            f.write(corrupted_content)

        # Load the recipe - should handle error gracefully
        recipe = VideoRecipeFile(recipe_path)

        # Should start with empty data
        assert recipe.video_data == []

        # The original corrupted file should be renamed to .old
        assert old_recipe_path.exists()
        with open(old_recipe_path, "r", encoding="utf-8") as f:
            assert f.read() == corrupted_content

        # A new empty file should be created or the file should be valid JSON
        if recipe_path.exists():
            with open(recipe_path, "r", encoding="utf-8") as f:
                # Should be valid JSON now
                data = json.load(f)
                assert "video_data" in data

    def test_recipe_with_multiple_video_scenes(self, tmp_path):
        """Test recipe with multiple video scenes."""
        recipe_path = tmp_path / "multi_scene_recipe.json"
        recipe = VideoRecipeFile(recipe_path)

        # Add multiple scenes with sub-videos
        for scene in range(3):
            video_recipes = []
            for sub_video in range(2):
                video_recipe = WanVideoRecipe(
                    prompt=f"Scene {scene} sub-video {sub_video}",
                    media_path=(
                        f"/path/to/scene_{scene}_image.jpg" if sub_video == 0 else None
                    ),
                    seed=scene * 100 + sub_video,
                )
                video_recipes.append(video_recipe)
            recipe.add_video_data(video_recipes)

        # Verify structure
        assert len(recipe.video_data) == 3
        for scene in range(3):
            assert len(recipe.video_data[scene]) == 2
            assert recipe.video_data[scene][0].prompt == f"Scene {scene} sub-video 0"
            assert recipe.video_data[scene][1].prompt == f"Scene {scene} sub-video 1"

        # Verify file structure
        with open(recipe_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert len(saved_data["video_data"]) == 3
        for scene in range(3):
            scene_data = saved_data["video_data"][scene]
            assert scene_data["index"] == scene + 1
            assert len(scene_data["recipe_list"]) == 2


class TestVideoRecipeBuilder:
    """Test VideoRecipeBuilder class - focus on actual recipe creation."""

    @pytest.fixture
    def story_setup(self, tmp_path):
        """Create a real story folder structure."""
        story_folder = tmp_path / "test_story"
        prompts_folder = story_folder / "prompts"
        prompts_folder.mkdir(parents=True)

        # Create real prompt file
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

        # Create narrator and image assets folder structure
        video_folder = story_folder / "video"
        video_folder.mkdir()

        # Create empty narrator and image asset file for dependency
        narrator_image_asset_file = (
            video_folder / "test_story_chapter_001_narrator_and_image_assets.json"
        )
        empty_assets = {
            "assets": [{"narrator": "", "image": ""}, {"narrator": "", "image": ""}]
        }
        with open(narrator_image_asset_file, "w", encoding="utf-8") as f:
            json.dump(empty_assets, f)

        return story_folder

    def test_recipe_builder_creates_correct_file(self, story_setup):
        """Test that VideoRecipeBuilder creates the correct JSON file structure."""
        # Mock only external dependencies
        with patch("logging_utils.logger"):
            with patch("ai_video_creator.modules.video_recipe.begin_file_logging"):
                builder = VideoRecipeBuilder(story_setup, 0)
                builder.create_video_recipe(sub_videos_length=3)

                # Verify recipe file was created
                recipe_file = builder._VideoRecipeBuilder__paths.video_recipe_file
                assert recipe_file.exists()

                # Load and verify the file structure
                with open(recipe_file, "r", encoding="utf-8") as f:
                    saved_recipe = json.load(f)

                # Verify correct structure
                assert "video_data" in saved_recipe
                assert len(saved_recipe["video_data"]) == 2  # Two scenes

                # Verify each scene has 3 sub-videos
                for scene_index in range(2):
                    scene_data = saved_recipe["video_data"][scene_index]
                    assert scene_data["index"] == scene_index + 1
                    assert len(scene_data["recipe_list"]) == 3

                    # First sub-video should have image path, others should not
                    first_recipe = scene_data["recipe_list"][0]
                    assert first_recipe["recipe_type"] == "WanVideoRecipeType"
                    assert (
                        first_recipe["prompt"] == f"First visual description"
                        if scene_index == 0
                        else "Second visual description"
                    )

                    for sub_video_index in range(1, 3):
                        sub_recipe = scene_data["recipe_list"][sub_video_index]
                        assert sub_recipe["media_path"] is None

    def test_recipe_builder_with_existing_valid_recipe(self, story_setup):
        """Test that builder doesn't recreate valid existing recipes."""
        with patch("logging_utils.logger"):
            with patch("ai_video_creator.modules.video_recipe.begin_file_logging"):
                # Create first recipe
                builder1 = VideoRecipeBuilder(story_setup, 0)
                builder1.create_video_recipe(sub_videos_length=2)

                recipe_file = builder1._VideoRecipeBuilder__paths.video_recipe_file

                # Load the original content
                with open(recipe_file, "r", encoding="utf-8") as f:
                    original_content = json.load(f)

                # Create second builder - should use existing recipe
                builder2 = VideoRecipeBuilder(story_setup, 0)
                builder2.create_video_recipe(sub_videos_length=2)

                # Content should be the same (recipes should not be recreated)
                with open(recipe_file, "r", encoding="utf-8") as f:
                    new_content = json.load(f)

                # The content should be essentially the same
                assert len(original_content["video_data"]) == len(
                    new_content["video_data"]
                )

                # Check that prompts are the same (main content unchanged)
                for i in range(len(original_content["video_data"])):
                    original_recipes = original_content["video_data"][i]["recipe_list"]
                    new_recipes = new_content["video_data"][i]["recipe_list"]
                    assert len(original_recipes) == len(new_recipes)
                    for j in range(len(original_recipes)):
                        assert original_recipes[j]["prompt"] == new_recipes[j]["prompt"]

    def test_recipe_builder_with_different_story_data(self, tmp_path):
        """Test recipe builder with different story structures."""
        # Create story with 3 prompts
        story_folder = tmp_path / "three_prompt_story"
        prompts_folder = story_folder / "prompts"
        prompts_folder.mkdir(parents=True)

        chapter_prompt = {
            "prompts": [
                {
                    "narrator": "Narrator 1",
                    "visual_description": "Visual 1",
                    "visual_prompt": "Prompt 1",
                },
                {
                    "narrator": "Narrator 2",
                    "visual_description": "Visual 2",
                    "visual_prompt": "Prompt 2",
                },
                {
                    "narrator": "Narrator 3",
                    "visual_description": "Visual 3",
                    "visual_prompt": "Prompt 3",
                },
            ]
        }

        prompt_file = prompts_folder / "chapter_001.json"
        with open(prompt_file, "w", encoding="utf-8") as f:
            json.dump(chapter_prompt, f)

        # Create video folder and asset dependencies
        video_folder = story_folder / "video"
        video_folder.mkdir()

        narrator_image_asset_file = (
            video_folder
            / "three_prompt_story_chapter_001_narrator_and_image_assets.json"
        )
        empty_assets = {
            "assets": [
                {"narrator": "", "image": ""},
                {"narrator": "", "image": ""},
                {"narrator": "", "image": ""},
            ]
        }
        with open(narrator_image_asset_file, "w", encoding="utf-8") as f:
            json.dump(empty_assets, f)

        with patch("logging_utils.logger"):
            with patch("ai_video_creator.modules.video_recipe.begin_file_logging"):
                builder = VideoRecipeBuilder(story_folder, 0)
                builder.create_video_recipe(sub_videos_length=4)

                recipe_file = builder._VideoRecipeBuilder__paths.video_recipe_file
                with open(recipe_file, "r", encoding="utf-8") as f:
                    saved_recipe = json.load(f)

                # Should have 3 scenes
                assert len(saved_recipe["video_data"]) == 3

                # Verify all prompts are correctly saved
                for i in range(3):
                    scene_data = saved_recipe["video_data"][i]
                    assert len(scene_data["recipe_list"]) == 4
                    # All recipes in a scene should have the same prompt (visual description)
                    expected_prompt = f"Visual {i+1}"
                    for recipe in scene_data["recipe_list"]:
                        assert recipe["prompt"] == expected_prompt

    def test_recipe_builder_handles_missing_assets(self, tmp_path):
        """Test recipe builder handles missing narrator and image assets gracefully."""
        story_folder = tmp_path / "no_assets_story"
        prompts_folder = story_folder / "prompts"
        prompts_folder.mkdir(parents=True)

        chapter_prompt = {
            "prompts": [
                {
                    "narrator": "Test narrator",
                    "visual_description": "Test visual description",
                    "visual_prompt": "Test visual prompt",
                }
            ]
        }

        prompt_file = prompts_folder / "chapter_001.json"
        with open(prompt_file, "w", encoding="utf-8") as f:
            json.dump(chapter_prompt, f)

        # Don't create narrator and image assets file

        with patch("logging_utils.logger"):
            with patch("ai_video_creator.modules.video_recipe.begin_file_logging"):
                builder = VideoRecipeBuilder(story_folder, 0)
                # Should not crash, should handle missing assets gracefully
                builder.create_video_recipe(sub_videos_length=2)

                recipe_file = builder._VideoRecipeBuilder__paths.video_recipe_file
                assert recipe_file.exists()

                with open(recipe_file, "r", encoding="utf-8") as f:
                    saved_recipe = json.load(f)

                # Should still create video data
                assert len(saved_recipe["video_data"]) == 1
                assert len(saved_recipe["video_data"][0]["recipe_list"]) == 2
