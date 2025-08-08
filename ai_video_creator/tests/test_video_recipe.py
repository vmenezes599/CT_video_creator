"""
Unit tests for video_recipe module.
"""

import json
from unittest.mock import patch

import pytest

from ai_video_creator.generators import FluxImageRecipe, SparkTTSRecipe
from ai_video_creator.modules.video_recipe import (
    VideoRecipe,
    VideoRecipeBuilder,
    VideoRecipeDefaultSettings,
)


class TestVideoRecipeDefaultSettings:
    """Test VideoRecipeDefaultSettings class."""

    def test_default_settings(self):
        """Test that default settings have correct values."""
        assert (
            VideoRecipeDefaultSettings.NARRATOR_VOICE
            == "default-assets/voices/voice_002.mp3"
        )
        assert (
            VideoRecipeDefaultSettings.BACKGROUND_MUSIC
            == "default-assets/background_music.mp3"
        )


class TestVideoRecipe:
    """Test VideoRecipe class."""

    def test_empty_recipe_creation(self, tmp_path):
        """Test creating an empty recipe."""
        recipe_path = tmp_path / "test_recipe.json"
        recipe = VideoRecipe(recipe_path)

        assert recipe.recipe_path == recipe_path
        assert recipe.narrator_data == []
        assert recipe.image_data == []

    def test_recipe_with_data(self, tmp_path):
        """Test recipe with actual data - core functionality."""
        recipe_path = tmp_path / "test_recipe.json"
        recipe = VideoRecipe(recipe_path)

        # Add real data
        narrator_recipe = SparkTTSRecipe("Test narrator text", "voice.mp3")
        image_recipe = FluxImageRecipe("Test image prompt", 12345)

        recipe.add_narrator_data(narrator_recipe)
        recipe.add_image_data(image_recipe)

        # Verify data was added correctly
        assert len(recipe.narrator_data) == 1
        assert len(recipe.image_data) == 1
        assert recipe.narrator_data[0].prompt == "Test narrator text"
        assert recipe.image_data[0].prompt == "Test image prompt"
        assert recipe.image_data[0].seed == 12345

        # Verify file was created with correct structure
        assert recipe_path.exists()
        with open(recipe_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        expected_structure = {
            "narrator_data": [
                {
                    "prompt": "Test narrator text",
                    "clone_voice_path": "voice.mp3",
                    "recipe_type": "SparkTTSRecipeType",
                }
            ],
            "image_data": [
                {
                    "prompt": "Test image prompt",
                    "seed": 12345,
                    "recipe_type": "FluxImageRecipeType",
                }
            ],
        }

        assert saved_data == expected_structure

    def test_recipe_loading_from_file(self, tmp_path):
        """Test loading recipe from existing file."""
        recipe_path = tmp_path / "existing_recipe.json"

        # Create a test file
        test_data = {
            "narrator_data": [
                {
                    "prompt": "Loaded narrator text",
                    "clone_voice_path": "loaded_voice.mp3",
                    "recipe_type": "SparkTTSRecipeType",
                }
            ],
            "image_data": [
                {
                    "prompt": "Loaded image prompt",
                    "seed": 99999,
                    "recipe_type": "FluxImageRecipeType",
                }
            ],
        }

        with open(recipe_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # Load the recipe
        recipe = VideoRecipe(recipe_path)

        # Verify data was loaded correctly
        assert len(recipe.narrator_data) == 1
        assert len(recipe.image_data) == 1
        assert isinstance(recipe.narrator_data[0], SparkTTSRecipe)
        assert isinstance(recipe.image_data[0], FluxImageRecipe)
        assert recipe.narrator_data[0].prompt == "Loaded narrator text"
        assert recipe.image_data[0].seed == 99999


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

        return story_folder

    def test_recipe_builder_creates_correct_file(self, story_setup):
        """Test that VideoRecipeBuilder creates the correct JSON file structure."""
        # Mock only external dependencies
        with patch("logging_utils.logger"):
            with patch("ai_video_creator.modules.video_recipe.begin_console_logging"):
                builder = VideoRecipeBuilder(story_setup, 0)
                builder.create_video_recipe()

                # Verify recipe file was created
                recipe_file = builder._VideoRecipeBuilder__paths.recipe_file
                assert recipe_file.exists()

                # Load and verify the file structure
                with open(recipe_file, "r", encoding="utf-8") as f:
                    saved_recipe = json.load(f)

                # Verify correct structure
                assert "narrator_data" in saved_recipe
                assert "image_data" in saved_recipe
                assert len(saved_recipe["narrator_data"]) == 2
                assert len(saved_recipe["image_data"]) == 2

                # Verify narrator data
                assert (
                    saved_recipe["narrator_data"][0]["prompt"] == "First narrator text"
                )
                assert (
                    saved_recipe["narrator_data"][1]["prompt"] == "Second narrator text"
                )
                assert (
                    saved_recipe["narrator_data"][0]["recipe_type"]
                    == "SparkTTSRecipeType"
                )
                assert (
                    saved_recipe["narrator_data"][0]["clone_voice_path"]
                    == VideoRecipeDefaultSettings.NARRATOR_VOICE
                )

                # Verify image data
                assert saved_recipe["image_data"][0]["prompt"] == "First visual prompt"
                assert saved_recipe["image_data"][1]["prompt"] == "Second visual prompt"
                assert (
                    saved_recipe["image_data"][0]["recipe_type"]
                    == "FluxImageRecipeType"
                )
                assert "seed" in saved_recipe["image_data"][0]
                assert isinstance(saved_recipe["image_data"][0]["seed"], int)

    def test_recipe_builder_with_existing_valid_recipe(self, story_setup):
        """Test that builder doesn't recreate valid existing recipes."""
        with patch("logging_utils.logger"):
            with patch("ai_video_creator.modules.video_recipe.begin_console_logging"):
                # Create first recipe
                builder1 = VideoRecipeBuilder(story_setup, 0)
                builder1.create_video_recipe()

                recipe_file = builder1._VideoRecipeBuilder__paths.recipe_file
                original_mtime = recipe_file.stat().st_mtime

                # Create second builder - should use existing recipe
                builder2 = VideoRecipeBuilder(story_setup, 0)
                builder2.create_video_recipe()

                # File should not have been modified (same modification time)
                assert recipe_file.stat().st_mtime == original_mtime

                # Content should be the same
                with open(recipe_file, "r", encoding="utf-8") as f:
                    recipe_data = json.load(f)

                assert len(recipe_data["narrator_data"]) == 2
                assert len(recipe_data["image_data"]) == 2

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

        with patch("logging_utils.logger"):
            with patch("ai_video_creator.modules.video_recipe.begin_console_logging"):
                builder = VideoRecipeBuilder(story_folder, 0)
                builder.create_video_recipe()

                recipe_file = builder._VideoRecipeBuilder__paths.recipe_file
                with open(recipe_file, "r", encoding="utf-8") as f:
                    saved_recipe = json.load(f)

                # Should have 3 of each
                assert len(saved_recipe["narrator_data"]) == 3
                assert len(saved_recipe["image_data"]) == 3

                # Verify all prompts are correctly saved
                for i in range(3):
                    assert (
                        saved_recipe["narrator_data"][i]["prompt"] == f"Narrator {i+1}"
                    )
                    assert saved_recipe["image_data"][i]["prompt"] == f"Prompt {i+1}"
