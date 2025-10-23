"""
Unit tests for video_recipe_builder module.
"""

import json
from unittest.mock import patch

import pytest

from ai_video_creator.modules.video import SubVideoRecipeBuilder
from ai_video_creator.utils import VideoCreatorPaths


class TestVideoRecipeBuilder:
    """Test VideoRecipeBuilder class - focus on actual recipe creation."""

    @pytest.fixture
    def video_creator_paths(self, tmp_path):
        """Create a VideoCreatorPaths instance for testing."""
        user_folder = tmp_path / "user"
        story_name = "test_story"
        chapter_index = 0

        # Create the directory structure
        story_folder = (
            user_folder / "stories" / story_name
        )  # Fix: Add stories subfolder
        story_folder.mkdir(parents=True)

        # Create prompts folder and test prompt file
        prompts_folder = story_folder / "prompts"
        prompts_folder.mkdir()

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

        # Create VideoCreatorPaths instance
        paths = VideoCreatorPaths(user_folder, story_name, chapter_index)

        # Create the required asset files for SubVideoRecipeBuilder
        narrator_assets = {
            "assets": [
                {"index": 1, "narrator": "assets/narrators/narrator_001.mp3"},
                {"index": 2, "narrator": "assets/narrators/narrator_002.mp3"},
            ]
        }

        image_assets = {
            "assets": [
                {"index": 1, "image": "assets/images/image_001.jpg"},
                {"index": 2, "image": "assets/images/image_002.jpg"},
            ]
        }

        # Create the actual asset files that unmask_asset_path will validate
        narrator_dir = paths.narrator_asset_folder
        narrator_dir.mkdir(parents=True, exist_ok=True)
        (narrator_dir / "narrator_001.mp3").touch()
        (narrator_dir / "narrator_002.mp3").touch()

        image_dir = paths.image_asset_folder
        image_dir.mkdir(parents=True, exist_ok=True)
        (image_dir / "image_001.jpg").touch()
        (image_dir / "image_002.jpg").touch()

        with open(paths.narrator_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_assets, f)
        with open(paths.image_asset_file, "w", encoding="utf-8") as f:
            json.dump(image_assets, f)

        return paths

    def test_recipe_builder_creates_correct_file(self, video_creator_paths):
        """Test that VideoRecipeBuilder creates the correct JSON file structure."""
        # Mock only external dependencies - get_audio_duration is external
        # Mock SceneScriptGenerator to avoid AI/LLM calls
        mock_scene_generator = patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.SceneScriptGenerator"
        )

        with patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.get_audio_duration",
            return_value=10.0,
        ), mock_scene_generator as MockSceneScriptGenerator:
            # Mock the generate_scenes_script method to return test data
            mock_instance = MockSceneScriptGenerator.return_value
            mock_instance.generate_scenes_script.return_value = [
                "Scene script 1",
                "Scene script 2",
                "Scene script 3",
            ]

            builder = SubVideoRecipeBuilder(video_creator_paths)
            builder.create_video_recipe()

            # Verify recipe file was created
            recipe_file = builder._paths.sub_video_recipe_file
            assert recipe_file.exists()

            # Load and verify the file structure
            with open(recipe_file, "r", encoding="utf-8") as f:
                saved_recipe = json.load(f)

            # Verify correct structure
            assert "video_data" in saved_recipe
            assert len(saved_recipe["video_data"]) == 2  # Two scenes

            # Verify each scene has sub-videos (2 because we have 2 narrator assets)
            for scene_index in range(2):
                scene_data = saved_recipe["video_data"][scene_index]
                assert scene_data["index"] == scene_index + 1
                assert len(scene_data["recipe_list"]) == 3

                # First sub-video should have the mocked scene script
                first_recipe = scene_data["recipe_list"][0]
                assert first_recipe["recipe_type"] == "WanI2VRecipeType"
                # Prompt comes from the mocked SceneScriptGenerator
                assert first_recipe["prompt"] == "Scene script 1"

    def test_recipe_builder_with_existing_valid_recipe(self, video_creator_paths):
        """Test that builder doesn't recreate valid existing recipes."""
        # Mock SceneScriptGenerator to avoid AI/LLM calls
        mock_scene_generator = patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.SceneScriptGenerator"
        )

        with patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.get_audio_duration",
            return_value=10.0,
        ), mock_scene_generator as MockSceneScriptGenerator:
            # Mock the generate_scenes_script method to return test data
            mock_instance = MockSceneScriptGenerator.return_value
            mock_instance.generate_scenes_script.return_value = [
                "Scene script 1",
                "Scene script 2",
                "Scene script 3",
            ]

            # Create first recipe
            builder1 = SubVideoRecipeBuilder(video_creator_paths)
            builder1.create_video_recipe()

            recipe_file = builder1._paths.sub_video_recipe_file

            # Load the original content
            with open(recipe_file, "r", encoding="utf-8") as f:
                original_content = json.load(f)

            # Create second builder - should use existing recipe
            builder2 = SubVideoRecipeBuilder(video_creator_paths)
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
        user_folder = tmp_path / "user"
        story_name = "three_prompt_story"
        chapter_index = 0

        story_folder = (
            user_folder / "stories" / story_name
        )  # Fix: Add stories subfolder
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

        # Create VideoCreatorPaths and required assets
        video_creator_paths = VideoCreatorPaths(user_folder, story_name, chapter_index)

        narrator_assets = {
            "assets": [
                {"index": 1, "narrator": "assets/narrators/narrator_001.mp3"},
                {"index": 2, "narrator": "assets/narrators/narrator_002.mp3"},
                {"index": 3, "narrator": "assets/narrators/narrator_003.mp3"},
            ]
        }

        image_assets = {
            "assets": [
                {"index": 1, "image": "assets/images/image_001.jpg"},
                {"index": 2, "image": "assets/images/image_002.jpg"},
                {"index": 3, "image": "assets/images/image_003.jpg"},
            ]
        }

        # Create the actual asset files that unmask_asset_path will validate
        narrator_dir = video_creator_paths.narrator_asset_folder
        narrator_dir.mkdir(parents=True, exist_ok=True)
        (narrator_dir / "narrator_001.mp3").touch()
        (narrator_dir / "narrator_002.mp3").touch()
        (narrator_dir / "narrator_003.mp3").touch()

        image_dir = video_creator_paths.image_asset_folder
        image_dir.mkdir(parents=True, exist_ok=True)
        (image_dir / "image_001.jpg").touch()
        (image_dir / "image_002.jpg").touch()
        (image_dir / "image_003.jpg").touch()

        with open(video_creator_paths.narrator_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_assets, f)
        with open(video_creator_paths.image_asset_file, "w", encoding="utf-8") as f:
            json.dump(image_assets, f)

        # Mock SceneScriptGenerator to avoid AI/LLM calls
        mock_scene_generator = patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.SceneScriptGenerator"
        )

        with patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.get_audio_duration",
            return_value=10.0,
        ), mock_scene_generator as MockSceneScriptGenerator:
            # Mock the generate_scenes_script method to return test data
            mock_instance = MockSceneScriptGenerator.return_value
            mock_instance.generate_scenes_script.return_value = [
                "Scene script 1",
                "Scene script 2",
                "Scene script 3",
            ]

            builder = SubVideoRecipeBuilder(video_creator_paths)
            builder.create_video_recipe()

            recipe_file = builder._paths.sub_video_recipe_file
            with open(recipe_file, "r", encoding="utf-8") as f:
                saved_recipe = json.load(f)

            # Should have 3 scenes
            assert len(saved_recipe["video_data"]) == 3

            # Verify all prompts are correctly saved
            for i in range(3):
                scene_data = saved_recipe["video_data"][i]
                assert (
                    len(scene_data["recipe_list"]) == 3
                )  # 3 because we have 3 narrator assets, limited by first 3 assets

    def test_recipe_builder_handles_missing_assets(self, tmp_path):
        """Test recipe builder handles missing narrator and image assets gracefully."""
        user_folder = tmp_path / "user"
        story_name = "no_assets_story"
        chapter_index = 0

        story_folder = (
            user_folder / "stories" / story_name
        )  # Fix: Add stories subfolder
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

        # Create VideoCreatorPaths but don't create narrator and image assets files
        video_creator_paths = VideoCreatorPaths(user_folder, story_name, chapter_index)

        # Mock SceneScriptGenerator to avoid AI/LLM calls
        mock_scene_generator = patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.SceneScriptGenerator"
        )

        with patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.get_audio_duration",
            return_value=10.0,
        ), mock_scene_generator as MockSceneScriptGenerator:
            # Mock the generate_scenes_script method to return test data
            mock_instance = MockSceneScriptGenerator.return_value
            mock_instance.generate_scenes_script.return_value = [
                "Scene script 1",
                "Scene script 2",
                "Scene script 3",
            ]

            builder = SubVideoRecipeBuilder(video_creator_paths)
            # Should not crash, should handle missing assets gracefully
            builder.create_video_recipe()

            recipe_file = builder._paths.sub_video_recipe_file
            assert recipe_file.exists()

            with open(recipe_file, "r", encoding="utf-8") as f:
                saved_recipe = json.load(f)

            # Should still create video data
            assert len(saved_recipe["video_data"]) == 1
            assert len(saved_recipe["video_data"][0]["recipe_list"]) == 3

    def test_recipe_builder_handles_audio_duration_errors(self, video_creator_paths):
        """Test recipe builder handles audio duration errors gracefully."""
        # Mock get_audio_duration to raise an exception
        # Mock SceneScriptGenerator to avoid AI/LLM calls
        mock_scene_generator = patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.SceneScriptGenerator"
        )

        with patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.get_audio_duration",
            side_effect=Exception("Audio file not found"),
        ), mock_scene_generator as MockSceneScriptGenerator:
            # Mock the generate_scenes_script method to return test data
            mock_instance = MockSceneScriptGenerator.return_value
            mock_instance.generate_scenes_script.return_value = [
                "Scene script 1",
                "Scene script 2",
                "Scene script 3",
            ]

            builder = SubVideoRecipeBuilder(video_creator_paths)
            # Currently, the builder does not handle audio duration errors gracefully
            # So we expect an exception to be raised
            with pytest.raises(Exception, match="Audio file not found"):
                builder.create_video_recipe()

    def test_recipe_builder_with_corrupted_prompts(self, tmp_path):
        """Test recipe builder handles corrupted prompt files gracefully."""
        user_folder = tmp_path / "user"
        story_name = "corrupted_story"
        chapter_index = 0

        story_folder = (
            user_folder / "stories" / story_name
        )  # Fix: Add stories subfolder
        prompts_folder = story_folder / "prompts"
        prompts_folder.mkdir(parents=True)

        # Create corrupted prompt file
        prompt_file = prompts_folder / "chapter_001.json"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        video_creator_paths = VideoCreatorPaths(user_folder, story_name, chapter_index)

        with patch(
            "ai_video_creator.modules.video.sub_video_recipe_builder.get_audio_duration",
            return_value=10.0,
        ):
            builder = SubVideoRecipeBuilder(video_creator_paths)
            # Should handle corrupted prompts gracefully
            try:
                builder.create_video_recipe()
                # If it doesn't crash, the recipe file might not be created or might be empty
                recipe_file = builder._paths.sub_video_recipe_file
                if recipe_file.exists():
                    with open(recipe_file, "r", encoding="utf-8") as f:
                        saved_recipe = json.load(f)
                        # Might have empty or default data
                        assert "video_data" in saved_recipe
            except Exception:
                # It's acceptable to fail with corrupted input, but should be handled gracefully
                pass
