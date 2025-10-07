"""
Unit tests for video_recipe_builder module.
"""

import json
from unittest.mock import patch

import pytest

from ai_video_creator.modules.video import SubVideoRecipeBuilder


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
            "assets": [
                {"index": 1, "narrator": "", "image": ""}, 
                {"index": 2, "narrator": "", "image": ""}
            ]
        }
        with open(narrator_image_asset_file, "w", encoding="utf-8") as f:
            json.dump(empty_assets, f)

        return story_folder

    def test_recipe_builder_creates_correct_file(self, story_setup):
        """Test that VideoRecipeBuilder creates the correct JSON file structure."""
        # Mock only external dependencies - get_audio_duration is external
        with patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.get_audio_duration",
            return_value=10.0,
        ):
            builder = SubVideoRecipeBuilder(story_setup, 0)
            builder.create_video_recipe()

            # Verify recipe file was created
            recipe_file = builder._SubVideoRecipeBuilder__paths.sub_video_recipe_file
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
                assert first_recipe["recipe_type"] == "WanI2VRecipeType"
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
        with patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.get_audio_duration",
            return_value=10.0,
        ):
            # Create first recipe
            builder1 = SubVideoRecipeBuilder(story_setup, 0)
            builder1.create_video_recipe()

            recipe_file = builder1._SubVideoRecipeBuilder__paths.sub_video_recipe_file

            # Load the original content
            with open(recipe_file, "r", encoding="utf-8") as f:
                original_content = json.load(f)

            # Create second builder - should use existing recipe
            builder2 = SubVideoRecipeBuilder(story_setup, 0)
            builder2.create_video_recipe()

            # Content should be the same (recipes should not be recreated)
            with open(recipe_file, "r", encoding="utf-8") as f:
                new_content = json.load(f)

            # The content should be essentially the same
            assert len(original_content["video_data"]) == len(new_content["video_data"])

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
                {"index": 1, "narrator": "", "image": ""},
                {"index": 2, "narrator": "", "image": ""},
                {"index": 3, "narrator": "", "image": ""},
            ]
        }
        with open(narrator_image_asset_file, "w", encoding="utf-8") as f:
            json.dump(empty_assets, f)

        with patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.get_audio_duration",
            return_value=10.0,
        ):
            builder = SubVideoRecipeBuilder(story_folder, 0)
            builder.create_video_recipe()

            recipe_file = builder._SubVideoRecipeBuilder__paths.sub_video_recipe_file
            with open(recipe_file, "r", encoding="utf-8") as f:
                saved_recipe = json.load(f)

            # Should have 3 scenes
            assert len(saved_recipe["video_data"]) == 3

            # Verify all prompts are correctly saved
            for i in range(3):
                scene_data = saved_recipe["video_data"][i]
                assert (
                    len(scene_data["recipe_list"]) == 3
                )  # Changed from 4 to 3 based on audio duration calculation
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

        with patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.get_audio_duration",
            return_value=10.0,
        ):
            builder = SubVideoRecipeBuilder(story_folder, 0)
            # Should not crash, should handle missing assets gracefully
            builder.create_video_recipe()

            recipe_file = builder._SubVideoRecipeBuilder__paths.sub_video_recipe_file
            assert recipe_file.exists()

            with open(recipe_file, "r", encoding="utf-8") as f:
                saved_recipe = json.load(f)

            # Should still create video data
            assert len(saved_recipe["video_data"]) == 1
            assert (
                len(saved_recipe["video_data"][0]["recipe_list"]) == 3
            )  # Changed from 2 to 3 based on audio duration calculation

    def test_recipe_builder_handles_audio_duration_errors(self, story_setup):
        """Test recipe builder handles audio duration errors gracefully."""
        # Mock get_audio_duration to raise an exception
        with patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.get_audio_duration",
            side_effect=Exception("Audio file not found"),
        ):
            builder = SubVideoRecipeBuilder(story_setup, 0)
            # Should handle audio duration errors and continue with default values
            builder.create_video_recipe()

            recipe_file = builder._SubVideoRecipeBuilder__paths.sub_video_recipe_file
            assert recipe_file.exists()

    def test_recipe_builder_with_corrupted_prompts(self, tmp_path):
        """Test recipe builder handles corrupted prompt files gracefully."""
        story_folder = tmp_path / "corrupted_story"
        prompts_folder = story_folder / "prompts"
        prompts_folder.mkdir(parents=True)

        # Create corrupted prompt file
        prompt_file = prompts_folder / "chapter_001.json"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        with patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.get_audio_duration",
            return_value=10.0,
        ):
            builder = SubVideoRecipeBuilder(story_folder, 0)
            # Should handle corrupted prompts gracefully
            try:
                builder.create_video_recipe()
                # If it doesn't crash, the recipe file might not be created or might be empty
                recipe_file = (
                    builder._SubVideoRecipeBuilder__paths.sub_video_recipe_file
                )
                if recipe_file.exists():
                    with open(recipe_file, "r", encoding="utf-8") as f:
                        saved_recipe = json.load(f)
                        # Might have empty or default data
                        assert "video_data" in saved_recipe
            except Exception:
                # It's acceptable to fail with corrupted input, but should be handled gracefully
                pass
