"""
Integration tests for AI Video Creator workflows.

These tests focus on testing complete workflows with minimal mocking,
using fake implementations for external dependencies only.
"""

import importlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

sub_video_i2v_module = importlib.import_module(
    "ai_video_creator.modules.sub_video.sub_video_recipe_builder"
)
from ct_video_creator.modules.narrator_and_image import NarratorAndImageAssetManager
from ct_video_creator.modules.sub_video import SubVideoAssetManager, SubVideoI2VRecipeBuilder
from ct_video_creator.utils import VideoCreatorPaths
from .test_fakes import TrackingFakeGenerators


class TestVideoCreationWorkflow:
    """Integration tests for complete video creation workflows."""

    @pytest.fixture
    def video_creator_paths(self, tmp_path):
        """Create VideoCreatorPaths object for integration testing."""
        user_folder = tmp_path
        story_name = "integration_story"
        chapter_index = 0

        # Create the necessary directory structure
        story_folder = user_folder / "stories" / story_name
        story_folder.mkdir(parents=True)

        # Create prompts folder and chapter prompt file
        prompts_folder = story_folder / "prompts"
        prompts_folder.mkdir()

        # Create a realistic chapter prompt
        chapter_prompt = {
            "prompts": [
                {
                    "narrator": "Once upon a time, in a distant galaxy, there was a brave explorer.",
                    "visual_description": "A vast galaxy with twinkling stars and nebulae",
                    "visual_prompt": "space galaxy stars nebulae cosmic explorer",
                },
                {
                    "narrator": "The explorer discovered a mysterious planet with strange creatures.",
                    "visual_description": "An alien planet with bizarre flora and fauna",
                    "visual_prompt": "alien planet creatures bizarre flora fauna",
                },
                {
                    "narrator": "With courage and determination, the explorer ventured into the unknown.",
                    "visual_description": "A heroic figure walking into mysterious terrain",
                    "visual_prompt": "heroic explorer courage determination unknown terrain",
                },
            ]
        }

        chapter_prompt_file = prompts_folder / "chapter_001.json"
        with open(chapter_prompt_file, "w", encoding="utf-8") as f:
            json.dump(chapter_prompt, f)

        # Create VideoCreatorPaths object
        paths = VideoCreatorPaths(user_folder, story_name, chapter_index)

        return paths

    @pytest.fixture
    def complete_story_setup(self, video_creator_paths):
        """Create a complete story structure for integration testing."""
        return video_creator_paths.story_folder

    def test_complete_narrator_and_image_workflow(self, video_creator_paths):
        """Test the complete narrator and image generation workflow."""
        # Use tracking generators to verify the workflow
        tracking = TrackingFakeGenerators()

        # Create and test recipe building
        video_folder = video_creator_paths.video_folder
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)

        # Create recipe files manually to test asset manager
        narrator_recipe_file = chapter_folder / "narrator_recipe.json"
        image_recipe_file = chapter_folder / "image_recipe.json"

        # Create realistic recipe structures
        narrator_recipe = {
            "narrator_data": [
                {
                    "prompt": "Once upon a time, in a distant galaxy, there was a brave explorer.",
                    "clone_voice_path": "default_assets/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                },
                {
                    "prompt": "The explorer discovered a mysterious planet with strange creatures.",
                    "clone_voice_path": "default_assets/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                },
                {
                    "prompt": "Together, they embarked on an incredible adventure through time and space.",
                    "clone_voice_path": "default_assets/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                },
            ]
        }

        image_recipe = {
            "image_data": [
                {
                    "prompt": "space galaxy stars nebulae cosmic explorer",
                    "width": 848,
                    "height": 480,
                    "seed": 12345,
                    "recipe_type": "FluxImageRecipeType",
                },
                {
                    "prompt": "alien planet strange creatures exotic plants",
                    "width": 848,
                    "height": 480,
                    "seed": 67890,
                    "recipe_type": "FluxImageRecipeType",
                },
                {
                    "prompt": "time portal energy swirling cosmic adventure",
                    "width": 848,
                    "height": 480,
                    "seed": 11111,
                    "recipe_type": "FluxImageRecipeType",
                },
            ]
        }

        with open(narrator_recipe_file, "w", encoding="utf-8") as f:
            json.dump(narrator_recipe, f)
        with open(image_recipe_file, "w", encoding="utf-8") as f:
            json.dump(image_recipe, f)

        # Test the asset manager workflow
        asset_manager = NarratorAndImageAssetManager(video_creator_paths)

        # Replace generators with fake implementations
        for recipe in asset_manager.narrator_builder.recipe.narrator_data:
            recipe.GENERATOR_TYPE = tracking.get_audio_generator
        for recipe in asset_manager.image_builder.recipe.recipes_data:
            recipe.GENERATOR_TYPE = tracking.get_image_generator

        # Test the complete workflow
        asset_manager.generate_narrator_and_image_assets()

        # Verify the workflow executed correctly
        assert tracking.get_call_count() == 6  # 3 audio + 3 image generations
        assert len(tracking.get_calls_by_type("audio")) == 3
        assert len(tracking.get_calls_by_type("image")) == 3

        # Verify actual files were created
        narrator_folder = chapter_folder / "assets" / "narrators"
        image_folder = chapter_folder / "assets" / "images"

        assert narrator_folder.exists()
        assert image_folder.exists()

        # Check that specific files exist
        narrator_files = list(narrator_folder.glob("*.mp3"))
        image_files = list(image_folder.glob("*.png"))

        assert len(narrator_files) == 3
        assert len(image_files) == 3

        # Verify content is correctly generated (check any of the files since we don't control order)
        narrator_contents = [f.read_text() for f in narrator_files]
        assert any(
            "distant galaxy" in content
            or "brave explorer" in content
            or "adventure" in content
            for content in narrator_contents
        )

        # Verify asset manager state
        assert asset_manager.narrator_builder.narrator_assets.is_complete()
        assert asset_manager.image_builder.image_assets.is_complete()

    def test_complete_video_generation_workflow(self, video_creator_paths):
        """Test the complete video generation workflow."""
        # Setup prerequisite assets first
        video_folder = video_creator_paths.video_folder
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)

        # Create narrator and image assets
        narrator_folder = chapter_folder / "assets" / "narrator"
        image_folder = chapter_folder / "assets" / "image"
        narrator_folder.mkdir(parents=True, exist_ok=True)
        image_folder.mkdir(parents=True, exist_ok=True)

        # Create fake asset files
        for i in range(3):
            narrator_file = narrator_folder / f"chapter_001_narrator_{i+1:03}.mp3"
            image_file = image_folder / f"chapter_001_image_{i+1:03}.png"
            narrator_file.write_text(f"Fake narrator audio {i+1}")
            image_file.write_text(f"Fake image data {i+1}")

        # Create asset reference files
        narrator_asset_file = chapter_folder / "narrator_assets.json"
        image_asset_file = chapter_folder / "image_assets.json"

        narrator_data = {
            "assets": [
                {
                    "index": i + 1,
                    "narrator": f"assets/narrator/chapter_001_narrator_{i+1:03}.mp3",
                }
                for i in range(3)
            ]
        }
        image_data = {
            "assets": [
                {
                    "index": i + 1,
                    "image": f"assets/image/chapter_001_image_{i+1:03}.png",
                }
                for i in range(3)
            ]
        }

        with open(narrator_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_data, f)
        with open(image_asset_file, "w", encoding="utf-8") as f:
            json.dump(image_data, f)

        # Create image recipe file that SubVideoI2VRecipeBuilder needs
        image_recipe_file = chapter_folder / "image_recipe.json"
        image_recipe = {
            "image_data": [
                {
                    "prompt": f"Test image prompt {i+1}",
                    "width": 848,
                    "height": 480,
                    "seed": 12345 + i,
                    "recipe_type": "FluxImageRecipeType",
                }
                for i in range(3)
            ]
        }
        with open(image_recipe_file, "w", encoding="utf-8") as f:
            json.dump(image_recipe, f)

        # Test recipe builder
        # Mock SceneScriptGenerator to avoid AI/LLM calls
        mock_scene_generator = patch.object(
            sub_video_i2v_module,
            "SceneScriptGenerator",
        )

        with patch.object(
            sub_video_i2v_module,
            "get_media_duration",
            return_value=5.0,
        ), mock_scene_generator as MockSceneScriptGenerator:
            # Mock the generate_scenes_script method to return test data
            mock_instance = MockSceneScriptGenerator.return_value
            mock_instance.generate_scenes_script.return_value = [
                "Scene script 1",
                "Scene script 2",
                "Scene script 3",
            ]

            recipe_builder = SubVideoI2VRecipeBuilder(video_creator_paths)
            recipe_builder.create_sub_video_recipe()

        # Verify recipe was created
        recipe_file = chapter_folder / "sub_video_recipe.json"
        assert recipe_file.exists()

        with open(recipe_file, "r", encoding="utf-8") as f:
            recipe_data = json.load(f)

        assert "video_data" in recipe_data
        assert len(recipe_data["video_data"]) == 3  # 3 scenes

        # Test video asset manager
        tracking = TrackingFakeGenerators()
        video_manager = SubVideoAssetManager(video_creator_paths)

        for scene_data in video_manager.recipe.video_data:
            for recipe in scene_data:
                recipe.GENERATOR_TYPE = tracking.get_video_generator

        # Mock the concatenation function and FFmpeg operations since they require real video files
        # Mock FlorenceGenerator to avoid AI/LLM calls
        with patch(
            "ai_video_creator.modules.sub_video.sub_video_asset_manager.concatenate_videos_remove_last_frame_except_last"
        ) as mock_concat, patch(
            "ai_video_creator.modules.sub_video.sub_video_asset_manager.extract_video_last_frame"
        ) as mock_extract, patch(
            "ai_video_creator.modules.sub_video.sub_video_asset_manager.FlorenceGenerator"
        ) as MockFlorenceGenerator:

            def fake_concat(input_videos, output_path):
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(
                    f"Concatenated video from {len(input_videos)} sources"
                )
                return output_path

            def fake_extract(video_path, last_frame_output_folder):
                # Create the output folder
                Path(last_frame_output_folder).mkdir(parents=True, exist_ok=True)
                # Create the actual output file path
                video_stem = Path(video_path).stem
                last_frame_output_path = (
                    Path(last_frame_output_folder) / f"{video_stem}_last_frame.png"
                )
                last_frame_output_path.write_text("fake frame image")
                return last_frame_output_path

            mock_concat.side_effect = fake_concat
            mock_extract.side_effect = fake_extract

            # Mock FlorenceGenerator.generate_description to return test data
            mock_florence_instance = MockFlorenceGenerator.return_value
            mock_florence_instance.generate_description.return_value = (
                "Generated description from Florence"
            )

            # Test the workflow
            video_manager.generate_video_assets()

        # Verify video generation occurred
        assert tracking.get_call_count() > 0
        video_calls = tracking.get_calls_by_type("video")
        assert len(video_calls) > 0

        # Verify video assets were created
        video_assets_file = chapter_folder / "sub_video_assets.json"
        assert video_assets_file.exists()

        # Verify no missing videos
        missing_videos = video_manager.video_assets.get_missing_videos()
        assert len(missing_videos) == 0

    def test_error_handling_in_workflow(self, video_creator_paths):
        """Test error handling in the video creation workflow."""
        # Create recipe files first so we have scenes to process
        video_folder = video_creator_paths.video_folder
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)

        # Create recipe files with test data
        narrator_recipe_file = chapter_folder / "narrator_recipe.json"
        image_recipe_file = chapter_folder / "image_recipe.json"

        narrator_recipe = {
            "narrator_data": [
                {
                    "prompt": "Test narrator 1",
                    "clone_voice_path": "default_assets/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                },
                {
                    "prompt": "Test narrator 2",
                    "clone_voice_path": "default_assets/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                },
            ]
        }

        image_recipe = {
            "image_data": [
                {
                    "prompt": "Test image 1",
                    "width": 848,
                    "height": 480,
                    "seed": 12345,
                    "recipe_type": "FluxImageRecipeType",
                },
                {
                    "prompt": "Test image 2",
                    "width": 848,
                    "height": 480,
                    "seed": 67890,
                    "recipe_type": "FluxImageRecipeType",
                },
            ]
        }

        with open(narrator_recipe_file, "w", encoding="utf-8") as f:
            json.dump(narrator_recipe, f)
        with open(image_recipe_file, "w", encoding="utf-8") as f:
            json.dump(image_recipe, f)

        # Now create asset manager with recipes
        asset_manager = NarratorAndImageAssetManager(video_creator_paths)

        # Create broken generators that simulate failures
        class FailingAudioGenerator:
            def clone_text_to_speech(self, recipe, output_file_path):
                raise IOError("Simulated TTS service failure")

        class FailingImageGenerator:
            def text_to_image(self, recipe, output_file_path):
                raise RuntimeError("Simulated image generation failure")

        # Replace generators with failing ones
        for recipe in asset_manager.narrator_builder.recipe.narrator_data:
            recipe.GENERATOR_TYPE = FailingAudioGenerator
        for recipe in asset_manager.image_builder.recipe.recipes_data:
            recipe.GENERATOR_TYPE = FailingImageGenerator

        # Test that errors are handled gracefully
        try:
            asset_manager.generate_narrator_and_image_assets()
        except (IOError, RuntimeError):
            # These specific errors might propagate, which is acceptable
            pass

        # Verify that the system remains in a consistent state
        assert not asset_manager.narrator_builder.narrator_assets.is_complete()
        assert not asset_manager.image_builder.image_assets.is_complete()

    def test_workflow_with_existing_partial_assets(self, video_creator_paths):
        """Test workflow behavior when some assets already exist."""
        video_folder = video_creator_paths.video_folder
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)

        # Create recipe files first so we have scenes to process
        narrator_recipe_file = chapter_folder / "narrator_recipe.json"
        image_recipe_file = chapter_folder / "image_recipe.json"

        narrator_recipe = {
            "narrator_data": [
                {
                    "prompt": "Test narrator 1",
                    "clone_voice_path": "default_assets/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                },
                {
                    "prompt": "Test narrator 2",
                    "clone_voice_path": "default_assets/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                },
                {
                    "prompt": "Test narrator 3",
                    "clone_voice_path": "default_assets/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                },
            ]
        }

        image_recipe = {
            "image_data": [
                {
                    "prompt": "Test image 1",
                    "width": 848,
                    "height": 480,
                    "seed": 12345,
                    "recipe_type": "FluxImageRecipeType",
                },
                {
                    "prompt": "Test image 2",
                    "width": 848,
                    "height": 480,
                    "seed": 67890,
                    "recipe_type": "FluxImageRecipeType",
                },
                {
                    "prompt": "Test image 3",
                    "width": 848,
                    "height": 480,
                    "seed": 11111,
                    "recipe_type": "FluxImageRecipeType",
                },
            ]
        }

        with open(narrator_recipe_file, "w", encoding="utf-8") as f:
            json.dump(narrator_recipe, f)
        with open(image_recipe_file, "w", encoding="utf-8") as f:
            json.dump(image_recipe, f)

        # Create partial existing assets
        narrator_folder = chapter_folder / "assets" / "narrator"
        image_folder = chapter_folder / "assets" / "image"
        narrator_folder.mkdir(parents=True, exist_ok=True)
        image_folder.mkdir(parents=True, exist_ok=True)

        # Create only first narrator and image (partial completion)
        existing_narrator = narrator_folder / "existing_narrator_001.mp3"
        existing_image = image_folder / "existing_image_001.png"
        existing_narrator.write_text("Existing narrator content")
        existing_image.write_text("Existing image content")

        # Create asset manager and set existing assets
        asset_manager = NarratorAndImageAssetManager(video_creator_paths)
        asset_manager.narrator_builder.narrator_assets.set_scene_narrator(
            0, existing_narrator
        )
        asset_manager.image_builder.image_assets.set_scene_image(0, existing_image)

        # Track what gets generated
        tracking = TrackingFakeGenerators()

        # Replace generators for remaining assets
        for i, recipe in enumerate(asset_manager.narrator_builder.recipe.narrator_data):
            recipe.GENERATOR_TYPE = tracking.get_audio_generator
        for i, recipe in enumerate(asset_manager.image_builder.recipe.recipes_data):
            recipe.GENERATOR_TYPE = tracking.get_image_generator

        # Run generation
        asset_manager.generate_narrator_and_image_assets()

        # Verify only missing assets were generated (should be 4: 2 narrator + 2 image)
        assert tracking.get_call_count() == 4

        # Verify existing assets weren't overwritten
        assert existing_narrator.read_text() == "Existing narrator content"
        assert existing_image.read_text() == "Existing image content"

        # Verify completion
        assert asset_manager.narrator_builder.narrator_assets.is_complete()
        assert asset_manager.image_builder.image_assets.is_complete()
