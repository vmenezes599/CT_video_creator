"""
Unit tests for narrator_and_image_recipe module.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER
from ai_video_creator.generators import FluxImageRecipe, ZonosTTSRecipe
from ai_video_creator.modules.narrator_and_image import (
    NarratorAndImageRecipe,
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
        recipe = NarratorAndImageRecipe(recipe_path)

        assert recipe.recipe_path == recipe_path
        assert recipe.narrator_data == []
        assert recipe.image_data == []

    def test_recipe_with_data(self, tmp_path):
        """Test recipe with actual data - core functionality."""
        recipe_path = tmp_path / "test_recipe.json"
        recipe = NarratorAndImageRecipe(recipe_path)

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
        recipe = NarratorAndImageRecipe(recipe_path)

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
        recipe = NarratorAndImageRecipe(recipe_path)

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
