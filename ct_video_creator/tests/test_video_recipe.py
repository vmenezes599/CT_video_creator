"""
Unit tests for video_recipe module.
"""

import json

from ct_video_creator.generators import WanI2VRecipe, WanT2VRecipe
from ct_video_creator.modules.sub_video import SubVideoRecipe
from ct_video_creator.utils import VideoCreatorPaths


class TestVideoRecipeFile:
    """Test VideoRecipeFile class."""

    def test_empty_recipe_creation(self, tmp_path):
        """Test creating an empty recipe."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        recipe = SubVideoRecipe(paths)

        assert recipe.recipe_path == paths.sub_video_recipe_file
        assert not recipe.video_data

    def test_recipe_with_data(self, tmp_path):
        """Test recipe with actual data - core functionality."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        recipe = SubVideoRecipe(paths)

        # Create test files within the story assets folder
        test_image = paths.sub_videos_asset_folder / "image.jpg"
        test_color_match = paths.sub_videos_asset_folder / "color_match_image.jpg"
        test_image.touch()
        test_color_match.touch()

        video_recipe = WanI2VRecipe(
            prompt="Test video prompt",
            width=848,
            height=480,
            color_match_media_path=str(test_color_match),
            media_path=str(test_image),
            high_lora=[],
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
        assert paths.sub_video_recipe_file.exists()
        with open(paths.sub_video_recipe_file, "r", encoding="utf-8") as f:
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
        # Path should be stored as relative in JSON using the mask prefix
        assert recipe_data["media_path"] == "assets/sub_videos/image.jpg"
        assert recipe_data["color_match_media_path"] == "assets/sub_videos/color_match_image.jpg"
        assert recipe_data["seed"] == 12345
        assert recipe_data["recipe_type"] == "WanI2VRecipeType"

    def test_recipe_loading_from_file(self, tmp_path):
        """Test loading recipe from existing file."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)

        # Create test files within the story assets folder
        test_image = paths.sub_videos_asset_folder / "image.jpg"
        test_color_match = paths.sub_videos_asset_folder / "color_match.jpg"
        test_image.parent.mkdir(parents=True, exist_ok=True)
        test_image.touch()
        test_color_match.touch()

        test_data = {
            "video_data": [
                {
                    "index": 1,
                    "recipe_list": [
                        {
                            "prompt": "Loaded video prompt",
                            "width": 848,
                            "height": 480,
                            "media_path": "assets/sub_videos/image.jpg",
                            "color_match_media_path": "assets/sub_videos/color_match.jpg",
                            "high_lora": [],
                            "seed": 99999,
                            "recipe_type": "WanI2VRecipeType",
                        }
                    ],
                    "extra_data": {},
                }
            ]
        }

        paths.sub_video_recipe_file.parent.mkdir(parents=True, exist_ok=True)
        with open(paths.sub_video_recipe_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # Load the recipe
        recipe = SubVideoRecipe(paths)

        # Verify data was loaded correctly
        assert len(recipe.video_data) == 1
        assert len(recipe.video_data[0]) == 1
        assert isinstance(recipe.video_data[0][0], WanI2VRecipe)
        assert recipe.video_data[0][0].prompt == "Loaded video prompt"
        # Internal paths should be absolute after loading
        assert str(recipe.video_data[0][0].media_path) == str(test_image)
        assert str(recipe.video_data[0][0].color_match_media_path) == str(test_color_match)
        assert recipe.video_data[0][0].seed == 99999

    def test_recipe_loading_with_invalid_json(self, tmp_path):
        """Test graceful handling when JSON file is corrupted."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        paths.sub_video_recipe_file.parent.mkdir(parents=True, exist_ok=True)
        old_recipe_path = paths.sub_video_recipe_file.with_suffix(".json.old")

        # Create a corrupted JSON file
        corrupted_content = "{ invalid json content"
        with open(paths.sub_video_recipe_file, "w", encoding="utf-8") as f:
            f.write(corrupted_content)

        # Load the recipe - should handle error gracefully
        recipe = SubVideoRecipe(paths)

        # Should start with empty data
        assert not recipe.video_data

        # The original corrupted file should be renamed to .old
        assert old_recipe_path.exists()
        with open(old_recipe_path, "r", encoding="utf-8") as f:
            assert f.read() == corrupted_content

        # A new empty file should be created or the file should be valid JSON
        if paths.sub_video_recipe_file.exists():
            with open(paths.sub_video_recipe_file, "r", encoding="utf-8") as f:
                # Should be valid JSON now
                data = json.load(f)
                assert "video_data" in data

    def test_recipe_with_multiple_video_scenes(self, tmp_path):
        """Test recipe with multiple video scenes."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        recipe = SubVideoRecipe(paths)

        # Create test files for multiple scenes in story assets folder
        scene_files = []
        paths.sub_videos_asset_folder.mkdir(parents=True, exist_ok=True)
        for scene in range(3):
            color_match_file = paths.sub_videos_asset_folder / f"scene_{scene}_color_match.jpg"
            image_file = paths.sub_videos_asset_folder / f"scene_{scene}_image.jpg"
            color_match_file.touch()
            image_file.touch()
            scene_files.append((image_file, color_match_file))

        # Add multiple scenes with sub-videos
        for scene in range(3):
            video_recipes = []
            image_file, color_match_file = scene_files[scene]
            for sub_video in range(2):
                if sub_video == 0:
                    video_recipe = WanI2VRecipe(
                        prompt=f"Scene {scene} sub-video {sub_video}",
                        width=848,
                        height=480,
                        color_match_media_path=str(color_match_file),
                        media_path=str(image_file),
                        high_lora=[],
                        seed=scene * 100 + sub_video,
                    )
                else:
                    video_recipe = WanT2VRecipe(
                        prompt=f"Scene {scene} sub-video {sub_video}",
                        width=848,
                        height=480,
                        color_match_media_path=str(color_match_file),
                        high_lora=[],
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
        with open(paths.sub_video_recipe_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert len(saved_data["video_data"]) == 3
        for scene in range(3):
            scene_data = saved_data["video_data"][scene]
            assert scene_data["index"] == scene + 1
            assert len(scene_data["recipe_list"]) == 2
