"""
Unit tests for narrator_and_image_recipe_builder module.
"""

import json
from unittest.mock import patch

import pytest

from ai_video_creator.modules.narrator_and_image import (
    NarratorAndImageRecipeBuilder,
    NarratorAndImageRecipeDefaultSettings,
)


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
            with patch("ai_video_creator.modules.narrator_and_image.narrator_and_image_recipe_builder.begin_file_logging"):
                builder = NarratorAndImageRecipeBuilder(story_setup, 0)
                builder.create_narrator_and_image_recipes()

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
            with patch("ai_video_creator.modules.narrator_and_image.narrator_and_image_recipe_builder.begin_file_logging"):
                # Create first recipe
                builder1 = NarratorAndImageRecipeBuilder(story_setup, 0)
                builder1.create_narrator_and_image_recipes()

                recipe_file = builder1._paths.narrator_and_image_recipe_file

                # Load the original content
                with open(recipe_file, "r", encoding="utf-8") as f:
                    original_content = json.load(f)

                # Create second builder - should use existing recipe
                builder2 = NarratorAndImageRecipeBuilder(story_setup, 0)
                builder2.create_narrator_and_image_recipes()

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
            with patch("ai_video_creator.modules.narrator_and_image.narrator_and_image_recipe_builder.begin_file_logging"):
                builder = NarratorAndImageRecipeBuilder(story_folder, 0)
                builder.create_narrator_and_image_recipes()

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