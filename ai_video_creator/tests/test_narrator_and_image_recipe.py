"""
Unit tests for video_recipe module.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER
from ai_video_creator.generators import FluxImageRecipe, ZonosTTSRecipe
from ai_video_creator.modules.narrator_and_image_recipe import (
    NarratorAndImageRecipeFile,
    NarratorAndImageRecipeBuilder,
    NarratorAndImageRecipeDefaultSettings,
)


class TestNarratorAndImageRecipeDefaultSettings:
    """Test NarratorAndImageRecipeDefaultSettings class."""

    def test_default_settings(self):
        """Test that default settings have correct values."""
        assert (
            NarratorAndImageRecipeDefaultSettings.NARRATOR_VOICE
            == f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3"
        )
        assert (
            NarratorAndImageRecipeDefaultSettings.BACKGROUND_MUSIC
            == f"{DEFAULT_ASSETS_FOLDER}/background_music.mp3"
        )


class TestNarratorAndImageRecipe:
    """Test NarratorAndImageRecipe class."""

    def test_empty_recipe_creation(self, tmp_path):
        """Test creating an empty recipe."""
        recipe_path = tmp_path / "test_recipe.json"
        recipe = NarratorAndImageRecipeFile(recipe_path)

        assert recipe.recipe_path == recipe_path
        assert recipe.narrator_data == []
        assert recipe.image_data == []

    def test_recipe_with_data(self, tmp_path):
        """Test recipe with actual data - core functionality."""
        recipe_path = tmp_path / "test_recipe.json"
        recipe = NarratorAndImageRecipeFile(recipe_path)

        # Mock ComfyUIRequests to avoid network calls that might affect seed generation
        with patch(
            "ai_video_creator.generators.image_generator.ComfyUIRequests"
        ) as mock_requests_class:
            mock_requests_instance = MagicMock()
            mock_requests_instance.comfyui_get_available_loras.return_value = []
            mock_requests_class.return_value = mock_requests_instance

            # Add real data
            narrator_recipe = ZonosTTSRecipe("Test narrator text", "voice.mp3")
            image_recipe = FluxImageRecipe("Test image prompt", seed=12345)

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

        # Check basic structure and key values
        assert "narrator_data" in saved_data
        assert "image_data" in saved_data
        assert len(saved_data["narrator_data"]) == 1
        assert len(saved_data["image_data"]) == 1

        # Check narrator data
        narrator = saved_data["narrator_data"][0]
        assert narrator["prompt"] == "Test narrator text"
        assert narrator["clone_voice_path"] == "voice.mp3"
        assert narrator["recipe_type"] == "ZonosTTSRecipeType"
        assert "index" in narrator
        assert "seed" in narrator

        # Check image data
        image = saved_data["image_data"][0]
        assert image["prompt"] == "Test image prompt"
        assert image["seed"] == 12345  # This should be preserved
        assert image["recipe_type"] == "FluxImageRecipeType"
        assert "index" in image
        assert "lora" in image
        assert "available_loras" in image

    def test_recipe_loading_from_file(self, tmp_path):
        """Test loading recipe from existing file."""
        recipe_path = tmp_path / "existing_recipe.json"

        # Create a test file
        test_data = {
            "narrator_data": [
                {
                    "prompt": "Loaded narrator text",
                    "clone_voice_path": "loaded_voice.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
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
        recipe = NarratorAndImageRecipeFile(recipe_path)

        # Verify data was loaded correctly
        assert len(recipe.narrator_data) == 1
        assert len(recipe.image_data) == 1
        assert isinstance(recipe.narrator_data[0], ZonosTTSRecipe)
        assert isinstance(recipe.image_data[0], FluxImageRecipe)
        assert recipe.narrator_data[0].prompt == "Loaded narrator text"
        assert recipe.image_data[0].seed == 99999

    def test_recipe_loading_with_invalid_json(self, tmp_path):
        """Test graceful handling when JSON file is corrupted."""
        recipe_path = tmp_path / "corrupted_recipe.json"
        old_recipe_path = tmp_path / "corrupted_recipe.json.old"

        # Create a corrupted JSON file
        corrupted_content = "{ invalid json content"
        with open(recipe_path, "w", encoding="utf-8") as f:
            f.write(corrupted_content)

        # Load the recipe - should handle error gracefully
        recipe = NarratorAndImageRecipeFile(recipe_path)

        # Should start with empty data
        assert recipe.narrator_data == []
        assert recipe.image_data == []
        
        # The original corrupted file should be renamed to .old
        assert old_recipe_path.exists()
        with open(old_recipe_path, "r", encoding="utf-8") as f:
            assert f.read() == corrupted_content
            
        # A new empty file should be created with valid JSON
        if recipe_path.exists():
            with open(recipe_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert "narrator_data" in data
                assert "image_data" in data


class TestNarratorAndImageRecipeBuilder:
    """Test NarratorAndImageRecipeBuilder class - focus on actual recipe creation."""

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
        """Test that NarratorAndImageRecipeBuilder creates the correct JSON file structure."""
        # Mock only external dependencies
        with patch("logging_utils.logger"):
            with patch("ai_video_creator.modules.video_recipe.begin_file_logging"):
                builder = NarratorAndImageRecipeBuilder(story_setup, 0)
                builder.create_narrator_and_image_recipe()

                # Verify recipe file was created
                recipe_file = builder._paths.narrator_and_image_recipe_file
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
                    == "ZonosTTSRecipeType"
                )
                assert (
                    saved_recipe["narrator_data"][0]["clone_voice_path"]
                    == NarratorAndImageRecipeDefaultSettings.NARRATOR_VOICE
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
            with patch("ai_video_creator.modules.video_recipe.begin_file_logging"):
                # Create first recipe
                builder1 = NarratorAndImageRecipeBuilder(story_setup, 0)
                builder1.create_narrator_and_image_recipe()

                recipe_file = builder1._paths.narrator_and_image_recipe_file

                # Load the original content
                with open(recipe_file, "r", encoding="utf-8") as f:
                    original_content = json.load(f)

                # Create second builder - should use existing recipe
                builder2 = NarratorAndImageRecipeBuilder(story_setup, 0)
                builder2.create_narrator_and_image_recipe()

                # Content should be the same (recipes should not be recreated)
                with open(recipe_file, "r", encoding="utf-8") as f:
                    new_content = json.load(f)

                # The content should be essentially the same
                assert len(original_content["narrator_data"]) == len(
                    new_content["narrator_data"]
                )
                assert len(original_content["image_data"]) == len(
                    new_content["image_data"]
                )

                # Check that prompts are the same (main content unchanged)
                for i in range(len(original_content["narrator_data"])):
                    assert (
                        original_content["narrator_data"][i]["prompt"]
                        == new_content["narrator_data"][i]["prompt"]
                    )
                for i in range(len(original_content["image_data"])):
                    assert (
                        original_content["image_data"][i]["prompt"]
                        == new_content["image_data"][i]["prompt"]
                    )

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
            with patch("ai_video_creator.modules.video_recipe.begin_file_logging"):
                builder = NarratorAndImageRecipeBuilder(story_folder, 0)
                builder.create_narrator_and_image_recipe()

                recipe_file = builder._paths.narrator_and_image_recipe_file
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

    def test_recipe_loading_with_invalid_json(self, tmp_path):
        """Test graceful handling when JSON file is corrupted."""
        recipe_path = tmp_path / "corrupted_recipe.json"
        old_recipe_path = tmp_path / "corrupted_recipe.json.old"

        # Create a corrupted JSON file
        corrupted_content = "{ invalid json content"
        with open(recipe_path, "w", encoding="utf-8") as f:
            f.write(corrupted_content)

        # Load the recipe - should handle error gracefully
        recipe = NarratorAndImageRecipeFile(recipe_path)

        # Should start with empty data
        assert recipe.narrator_data == []
        assert recipe.image_data == []
        
        # The original corrupted file should be renamed to .old
        assert old_recipe_path.exists()
        with open(old_recipe_path, "r", encoding="utf-8") as f:
            assert f.read() == corrupted_content
            
        # A new empty file should be created with valid JSON
        if recipe_path.exists():
            with open(recipe_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert "narrator_data" in data
                assert "image_data" in data
