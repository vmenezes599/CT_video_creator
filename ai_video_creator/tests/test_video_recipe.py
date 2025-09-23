"""
Unit tests for video_recipe module.
"""

import json

from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER
from ai_video_creator.generators import WanVideoRecipe
from ai_video_creator.modules.video import (
    SubVideoRecipe,
    SubVideoRecipeDefaultSettings,
)


class TestVideoRecipeDefaultSettings:
    """Test VideoRecipeDefaultSettings class."""

    def test_default_settings(self):
        """Test that default settings have correct values."""
        assert (
            SubVideoRecipeDefaultSettings.NARRATOR_VOICE
            == f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3"
        )
        assert (
            SubVideoRecipeDefaultSettings.BACKGROUND_MUSIC
            == f"{DEFAULT_ASSETS_FOLDER}/background_music.mp3"
        )


class TestVideoRecipeFile:
    """Test VideoRecipeFile class."""

    def test_empty_recipe_creation(self, tmp_path):
        """Test creating an empty recipe."""
        recipe_path = tmp_path / "test_recipe.json"
        recipe = SubVideoRecipe(recipe_path)

        assert recipe.recipe_path == recipe_path
        assert recipe.video_data == []

    def test_recipe_with_data(self, tmp_path):
        """Test recipe with actual data - core functionality."""
        recipe_path = tmp_path / "test_recipe.json"
        recipe = SubVideoRecipe(recipe_path)

        # Create test files within the tmp_path to satisfy path validation
        test_image = tmp_path / "image.jpg"
        test_color_match = tmp_path / "color_match_image.jpg"
        test_image.touch()
        test_color_match.touch()

        # Add real video recipe data
        video_recipe = WanVideoRecipe(
            prompt="Test video prompt",
            color_match_media_path=str(test_color_match),
            media_path=str(test_image),
            high_lora=[],  # Required parameter
            seed=12345,
        )

        recipe.add_video_data([video_recipe])

        # Verify data was added correctly
        assert len(recipe.video_data) == 1
        assert len(recipe.video_data[0]) == 1  # One recipe in the list
        assert recipe.video_data[0][0].prompt == "Test video prompt"
        assert str(recipe.video_data[0][0].media_path) == str(test_image)
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
        # Path should be stored as relative in JSON
        assert recipe_data["media_path"] == "image.jpg"
        assert recipe_data["color_match_media_path"] == "color_match_image.jpg"
        assert recipe_data["seed"] == 12345
        assert recipe_data["recipe_type"] == "WanVideoRecipeType"

    def test_recipe_loading_from_file(self, tmp_path):
        """Test loading recipe from existing file."""
        recipe_path = tmp_path / "existing_recipe.json"

        # Create test files within the tmp_path to satisfy path validation
        test_image = tmp_path / "image.jpg"
        test_color_match = tmp_path / "color_match.jpg"
        test_image.touch()
        test_color_match.touch()

        # Create a test file with relative paths
        test_data = {
            "video_data": [
                {
                    "index": 1,
                    "recipe_list": [
                        {
                            "prompt": "Loaded video prompt",
                            "media_path": "image.jpg",  # Relative path
                            "color_match_media_path": "color_match.jpg",  # Relative path
                            "high_lora": [],  # Required field
                            "seed": 99999,
                            "recipe_type": "WanVideoRecipeType",
                        }
                    ],
                    "extra_data": {},
                }
            ]
        }

        with open(recipe_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # Load the recipe
        recipe = SubVideoRecipe(recipe_path)

        # Verify data was loaded correctly
        assert len(recipe.video_data) == 1
        assert len(recipe.video_data[0]) == 1
        assert isinstance(recipe.video_data[0][0], WanVideoRecipe)
        assert recipe.video_data[0][0].prompt == "Loaded video prompt"
        # Internal paths should be absolute after loading
        assert str(recipe.video_data[0][0].media_path) == str(test_image)
        assert str(recipe.video_data[0][0].color_match_media_path) == str(test_color_match)
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
        recipe = SubVideoRecipe(recipe_path)

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
        recipe = SubVideoRecipe(recipe_path)

        # Create test files for multiple scenes
        scene_files = []
        for scene in range(3):
            color_match_file = tmp_path / f"scene_{scene}_color_match.jpg"
            image_file = tmp_path / f"scene_{scene}_image.jpg"
            color_match_file.touch()
            image_file.touch()
            scene_files.append((image_file, color_match_file))

        # Add multiple scenes with sub-videos
        for scene in range(3):
            video_recipes = []
            image_file, color_match_file = scene_files[scene]
            for sub_video in range(2):
                video_recipe = WanVideoRecipe(
                    prompt=f"Scene {scene} sub-video {sub_video}",
                    color_match_media_path=str(color_match_file),
                    media_path=str(image_file) if sub_video == 0 else None,
                    high_lora=[],  # Required parameter
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
