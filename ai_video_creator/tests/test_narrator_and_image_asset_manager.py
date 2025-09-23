"""
Unit tests for narrator_and_image_asset_manager module.
"""

import json
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from ai_video_creator.modules.narrator_and_image import NarratorAndImageAssetManager
from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER


class TestNarratorAndImageAssetManager:
    """Test VideoAssetManager class - focuses on asset generation coordination."""

    @pytest.fixture
    def story_setup_with_recipe(self, tmp_path):
        """Create a story folder with recipe file."""
        story_folder = tmp_path / "test_story"
        story_folder.mkdir()

        # Create prompts folder and file
        prompts_folder = story_folder / "prompts"
        prompts_folder.mkdir()

        # Create a test chapter prompt
        chapter_prompt = {
            "prompts": [
                {
                    "narrator": "Test narrator 1",
                    "visual_description": "Test description 1",
                    "visual_prompt": "Test prompt 1",
                },
                {
                    "narrator": "Test narrator 2",
                    "visual_description": "Test description 2",
                    "visual_prompt": "Test prompt 2",
                },
            ]
        }

        prompt_file = prompts_folder / "chapter_001.json"
        with open(prompt_file, "w", encoding="utf-8") as f:
            json.dump(chapter_prompt, f)

        # Create a test recipe file in video folder
        video_folder = story_folder / "video"
        video_folder.mkdir()
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir()
        recipe_file = chapter_folder / "narrator_and_image_recipe.json"

        test_recipe = {
            "narrator_data": [
                {
                    "prompt": "Test narrator 1",
                    "clone_voice_path": f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                },
                {
                    "prompt": "Test narrator 2",
                    "clone_voice_path": f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                },
            ],
            "image_data": [
                {
                    "prompt": "Test prompt 1",
                    "seed": 12345,
                    "recipe_type": "FluxImageRecipeType",
                },
                {
                    "prompt": "Test prompt 2",
                    "seed": 67890,
                    "recipe_type": "FluxImageRecipeType",
                },
            ],
        }

        with open(recipe_file, "w", encoding="utf-8") as f:
            json.dump(test_recipe, f)

        return story_folder

    def test_asset_manager_initialization(self, story_setup_with_recipe):
        """Test VideoAssetManager initialization with recipe synchronization."""
        with patch("logging_utils.logger"):
            manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

            assert len(manager.recipe.narrator_data) == 2
            assert len(manager.recipe.image_data) == 2

            assert len(manager.video_assets.narrator_assets) == 2
            assert len(manager.video_assets.image_assets) == 2

            assert not manager.video_assets.is_complete()
            missing = manager.video_assets.get_missing_narrator_and_image_assets()
            assert missing["narrator"] == [0, 1]
            assert missing["image"] == [0, 1]

    def test_asset_manager_creates_asset_file(self, story_setup_with_recipe):
        """Test that VideoAssetManager creates and manages asset files properly."""
        with patch("logging_utils.logger"):
            manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

            # Create assets folder and test files within the allowed directory
            assets_folder = (
                story_setup_with_recipe
                / "video"
                / "chapter_001"
                / "assets"
                / "narrator_and_image"
            )
            assets_folder.mkdir(parents=True, exist_ok=True)

            test_narrator = assets_folder / "narrator_001.mp3"
            test_image = assets_folder / "image_001.jpg"
            test_narrator.touch()
            test_image.touch()

            manager.video_assets.set_scene_narrator(0, test_narrator)
            manager.video_assets.set_scene_image(0, test_image)
            manager.video_assets.save_assets_to_file()

            asset_file = manager.video_assets.asset_file_path
            assert asset_file.exists()

            with open(asset_file, "r", encoding="utf-8") as f:
                saved_data = json.load(f)

            assert "assets" in saved_data
            assert len(saved_data["assets"]) == 2
            assert (
                saved_data["assets"][0]["narrator"]
                == "assets/narrator_and_image/narrator_001.mp3"
            )
            assert (
                saved_data["assets"][0]["image"]
                == "assets/narrator_and_image/image_001.jpg"
            )
            assert saved_data["assets"][1]["narrator"] == ""
            assert saved_data["assets"][1]["image"] == ""

    def test_asset_manager_with_existing_assets(self, story_setup_with_recipe):
        """Test VideoAssetManager loading existing asset files."""
        video_folder = story_setup_with_recipe / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)
        asset_file = chapter_folder / "narrator_and_image_assets.json"

        # Create actual asset files within the allowed directory
        assets_folder = chapter_folder / "assets" / "narrator_and_image"
        assets_folder.mkdir(parents=True, exist_ok=True)

        narrator1 = assets_folder / "narrator1.mp3"
        narrator2 = assets_folder / "narrator2.mp3"
        image1 = assets_folder / "image1.jpg"
        image2 = assets_folder / "image2.jpg"

        for file in [narrator1, narrator2, image1, image2]:
            file.touch()

        existing_data = {
            "assets": [
                {
                    "narrator": "assets/narrator_and_image/narrator1.mp3",
                    "image": "assets/narrator_and_image/image1.jpg",
                },
                {
                    "narrator": "assets/narrator_and_image/narrator2.mp3",
                    "image": "assets/narrator_and_image/image2.jpg",
                },
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f)

        with patch("logging_utils.logger"):
            manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

            assert manager.video_assets.narrator_assets[0] == narrator1
            assert manager.video_assets.image_assets[0] == image1
            assert manager.video_assets.narrator_assets[1] == narrator2
            assert manager.video_assets.image_assets[1] == image2

            assert manager.video_assets.is_complete()

    def test_asset_synchronization_different_sizes(self, story_setup_with_recipe):
        """Test asset synchronization when asset file has different size than recipe."""
        video_folder = story_setup_with_recipe / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)
        asset_file = chapter_folder / "narrator_and_image_assets.json"

        # Create actual asset files within the allowed directory
        assets_folder = chapter_folder / "assets" / "narrator_and_image"
        assets_folder.mkdir(parents=True, exist_ok=True)

        narrator1 = assets_folder / "narrator1.mp3"
        image1 = assets_folder / "image1.jpg"

        for file in [narrator1, image1]:
            file.touch()

        existing_data = {
            "assets": [
                {
                    "narrator": "assets/narrator_and_image/narrator1.mp3",
                    "image": "assets/narrator_and_image/image1.jpg",
                }
            ]
        }

        with open(asset_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f)

        with patch("logging_utils.logger"):
            manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

            assert len(manager.video_assets.narrator_assets) == 2
            assert len(manager.video_assets.image_assets) == 2

            assert manager.video_assets.narrator_assets[0] == narrator1
            assert manager.video_assets.image_assets[0] == image1

            assert manager.video_assets.narrator_assets[1] is None
            assert manager.video_assets.image_assets[1] is None

            assert not manager.video_assets.is_complete()

    def test_cleanup_assets_removes_unused_files(self, story_setup_with_recipe):
        """Test that cleanup_assets removes files not referenced in assets."""
        video_folder = story_setup_with_recipe / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)
        assets_folder = chapter_folder / "assets" / "narrator_and_image"
        assets_folder.mkdir(parents=True, exist_ok=True)

        # Create some asset files that should be kept
        valid_narrator1 = assets_folder / "chapter_001_narrator_001.mp3"
        valid_image1 = assets_folder / "chapter_001_image_001.png"
        valid_narrator2 = assets_folder / "chapter_001_narrator_002.mp3"

        # Create some files that should be deleted
        old_narrator = assets_folder / "old_narrator.mp3"
        old_image = assets_folder / "old_image.png"
        temp_file = assets_folder / "temp.txt"

        # Create all files
        for file_path in [
            valid_narrator1,
            valid_image1,
            valid_narrator2,
            old_narrator,
            old_image,
            temp_file,
        ]:
            file_path.touch()

        with patch("logging_utils.logger"):
            manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

            # Set up some assets to be kept - use relative paths from chapter folder
            manager.video_assets.set_scene_narrator(
                0, Path("assets/narrator_and_image/chapter_001_narrator_001.mp3")
            )
            manager.video_assets.set_scene_image(
                0, Path("assets/narrator_and_image/chapter_001_image_001.png")
            )
            manager.video_assets.set_scene_narrator(
                1, Path("assets/narrator_and_image/chapter_001_narrator_002.mp3")
            )
            # Note: scene 1 has no image asset (None)

            # Run cleanup
            manager.clean_unused_assets()

            # Verify that valid assets are kept
            assert valid_narrator1.exists()
            assert valid_image1.exists()
            assert valid_narrator2.exists()

            # Verify that unused files are deleted
            assert not old_narrator.exists()
            assert not old_image.exists()
            assert not temp_file.exists()

    def test_cleanup_assets_handles_none_values_in_assets(
        self, story_setup_with_recipe
    ):
        """Test that cleanup_assets properly handles None values in asset lists."""
        video_folder = story_setup_with_recipe / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)
        assets_folder = chapter_folder / "assets" / "narrator_and_image"
        assets_folder.mkdir(parents=True, exist_ok=True)

        # Create some files
        valid_file = assets_folder / "valid_asset.mp3"
        invalid_file = assets_folder / "should_be_deleted.mp3"

        valid_file.touch()
        invalid_file.touch()

        with patch("logging_utils.logger"):
            manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

            # Set only one asset, leaving others as None - use relative path
            manager.video_assets.set_scene_narrator(
                0, Path("assets/narrator_and_image/valid_asset.mp3")
            )
            # manager.video_assets.narrator_assets[1] is None
            # manager.video_assets.image_assets[0] and [1] are None

            # Run cleanup
            manager.clean_unused_assets()

            # Verify that the valid file is kept
            assert valid_file.exists()

            # Verify that the unused file is deleted
            assert not invalid_file.exists()

    def test_cleanup_assets_preserves_directories(self, story_setup_with_recipe):
        """Test that cleanup_assets only removes files, not directories."""
        video_folder = story_setup_with_recipe / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)
        assets_folder = chapter_folder / "assets" / "narrator_and_image"
        assets_folder.mkdir(parents=True, exist_ok=True)

        # Create a subdirectory
        sub_dir = assets_folder / "subdirectory"
        sub_dir.mkdir()

        # Create a file inside the subdirectory
        file_in_subdir = sub_dir / "file.txt"
        file_in_subdir.touch()

        # Create a file in the main assets folder
        main_file = assets_folder / "main_file.txt"
        main_file.touch()

        with patch("logging_utils.logger"):
            manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

            # Run cleanup with no assets set (all should be deleted except directories)
            manager.clean_unused_assets()

            # Verify that the subdirectory still exists
            assert sub_dir.exists()
            assert sub_dir.is_dir()

            # Verify that files are deleted
            assert not main_file.exists()
            # Note: file_in_subdir should still exist because cleanup only processes
            # files directly in assets_folder, not in subdirectories

    @patch(
        "ai_video_creator.modules.narrator_and_image.narrator_and_image_asset_manager.begin_file_logging"
    )
    def test_generate_narrator_and_image_assets_success(
        self, mock_logging, story_setup_with_recipe
    ):
        """Test successful asset generation process."""
        # Create asset manager
        video_asset_manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Mock only the external generators, not the business logic
        mock_audio_gen = Mock()
        mock_image_gen = Mock()

        # The generators should return the output file path that was passed to them
        def mock_audio_generation(recipe, output_file_path):
            return output_file_path

        def mock_image_generation(recipe, output_file_path):
            return [output_file_path]

        mock_audio_gen.clone_text_to_speech.side_effect = mock_audio_generation
        mock_image_gen.text_to_image.side_effect = mock_image_generation

        # Mock the generator creation from recipe data
        with patch.object(
            video_asset_manager.recipe.narrator_data[0],
            "GENERATOR",
            return_value=mock_audio_gen,
        ), patch.object(
            video_asset_manager.recipe.narrator_data[1],
            "GENERATOR",
            return_value=mock_audio_gen,
        ), patch.object(
            video_asset_manager.recipe.image_data[0],
            "GENERATOR",
            return_value=mock_image_gen,
        ), patch.object(
            video_asset_manager.recipe.image_data[1],
            "GENERATOR",
            return_value=mock_image_gen,
        ):

            # Run the actual generation logic
            video_asset_manager.generate_narrator_and_image_assets()

            # Verify generators were called for each scene
            assert mock_audio_gen.clone_text_to_speech.call_count == 2  # 2 scenes
            assert mock_image_gen.text_to_image.call_count == 2  # 2 scenes

            # The actual files are generated in the chapter asset folder with specific names
            expected_narrator_path_1 = (
                story_setup_with_recipe
                / "video"
                / "chapter_001"
                / "assets"
                / "narrator_and_image"
                / "chapter_001_narrator_001.mp3"
            )
            expected_narrator_path_2 = (
                story_setup_with_recipe
                / "video"
                / "chapter_001"
                / "assets"
                / "narrator_and_image"
                / "chapter_001_narrator_002.mp3"
            )
            expected_image_path_1 = (
                story_setup_with_recipe
                / "video"
                / "chapter_001"
                / "assets"
                / "narrator_and_image"
                / "chapter_001_image_001.png"
            )
            expected_image_path_2 = (
                story_setup_with_recipe
                / "video"
                / "chapter_001"
                / "assets"
                / "narrator_and_image"
                / "chapter_001_image_002.png"
            )

            # Verify assets were set in the video_assets object
            assert (
                video_asset_manager.video_assets.narrator_assets[0]
                == expected_narrator_path_1
            )
            assert (
                video_asset_manager.video_assets.narrator_assets[1]
                == expected_narrator_path_2
            )
            assert (
                video_asset_manager.video_assets.image_assets[0]
                == expected_image_path_1
            )
            assert (
                video_asset_manager.video_assets.image_assets[1]
                == expected_image_path_2
            )

    @patch(
        "ai_video_creator.modules.narrator_and_image.narrator_and_image_asset_manager.begin_file_logging"
    )
    def test_generate_assets_with_existing_assets_skips_generation(
        self, mock_logging, story_setup_with_recipe
    ):
        """Test that existing assets are not regenerated."""
        # Create asset manager
        video_asset_manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Create actual asset files so has_* methods return True naturally
        asset_folder = (
            video_asset_manager.video_assets.asset_file_path.parent
            / "assets"
            / "narrator_and_image"
        )
        asset_folder.mkdir(parents=True, exist_ok=True)

        existing_audio_1 = asset_folder / "existing_narrator_1.mp3"
        existing_audio_2 = asset_folder / "existing_narrator_2.mp3"
        existing_image_1 = asset_folder / "existing_image_1.png"
        existing_image_2 = asset_folder / "existing_image_2.png"

        existing_audio_1.write_text("existing audio 1")
        existing_audio_2.write_text("existing audio 2")
        existing_image_1.write_text("existing image 1")
        existing_image_2.write_text("existing image 2")

        # Set existing assets using actual business logic
        video_asset_manager.video_assets.set_scene_narrator(0, existing_audio_1)
        video_asset_manager.video_assets.set_scene_narrator(1, existing_audio_2)
        video_asset_manager.video_assets.set_scene_image(0, existing_image_1)
        video_asset_manager.video_assets.set_scene_image(1, existing_image_2)

        # Mock generators to verify they're not called
        mock_audio_gen = Mock()
        mock_image_gen = Mock()

        with patch.object(
            video_asset_manager.recipe.narrator_data[0],
            "GENERATOR",
            return_value=mock_audio_gen,
        ), patch.object(
            video_asset_manager.recipe.narrator_data[1],
            "GENERATOR",
            return_value=mock_audio_gen,
        ), patch.object(
            video_asset_manager.recipe.image_data[0],
            "GENERATOR",
            return_value=mock_image_gen,
        ), patch.object(
            video_asset_manager.recipe.image_data[1],
            "GENERATOR",
            return_value=mock_image_gen,
        ):

            # Run the actual generation logic
            video_asset_manager.generate_narrator_and_image_assets()

            # Verify no generators were called since all assets already exist
            mock_audio_gen.clone_text_to_speech.assert_not_called()
            mock_image_gen.text_to_image.assert_not_called()

    @patch(
        "ai_video_creator.modules.narrator_and_image.narrator_and_image_asset_manager.begin_file_logging"
    )
    def test_generate_assets_handles_partial_completion(
        self, mock_logging, story_setup_with_recipe
    ):
        """Test generation when only some assets exist."""
        # Create asset manager
        video_asset_manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Create asset folder and set up existing narrator for scene 0 only
        asset_folder = (
            video_asset_manager.video_assets.asset_file_path.parent
            / "assets"
            / "narrator_and_image"
        )
        asset_folder.mkdir(parents=True, exist_ok=True)

        existing_audio = asset_folder / "existing_narrator.mp3"
        existing_audio.write_text("existing audio content")
        video_asset_manager.video_assets.set_scene_narrator(0, existing_audio)
        # Scene 1 narrator and both scene images are missing

        # Mock generators
        mock_audio_gen = Mock()
        mock_image_gen = Mock()

        # The generators should return the output file path that was passed to them
        def mock_audio_generation(recipe, output_file_path):
            return output_file_path

        def mock_image_generation(recipe, output_file_path):
            return [output_file_path]

        mock_audio_gen.clone_text_to_speech.side_effect = mock_audio_generation
        mock_image_gen.text_to_image.side_effect = mock_image_generation

        with patch.object(
            video_asset_manager.recipe.narrator_data[0],
            "GENERATOR",
            return_value=mock_audio_gen,
        ), patch.object(
            video_asset_manager.recipe.narrator_data[1],
            "GENERATOR",
            return_value=mock_audio_gen,
        ), patch.object(
            video_asset_manager.recipe.image_data[0],
            "GENERATOR",
            return_value=mock_image_gen,
        ), patch.object(
            video_asset_manager.recipe.image_data[1],
            "GENERATOR",
            return_value=mock_image_gen,
        ):

            # Run the actual generation logic
            video_asset_manager.generate_narrator_and_image_assets()

            # Verify audio generator was called only for scene 1 (scene 0 already had narrator)
            assert mock_audio_gen.clone_text_to_speech.call_count == 1

            # Verify image generator was called for both scenes (both were missing)
            assert mock_image_gen.text_to_image.call_count == 2

            # Verify the business logic correctly kept existing asset and added new ones
            assert (
                video_asset_manager.video_assets.narrator_assets[0] == existing_audio
            )  # Kept existing

            # Generated assets should be in the expected locations with proper names
            expected_narrator_path = (
                story_setup_with_recipe
                / "video"
                / "chapter_001"
                / "assets"
                / "narrator_and_image"
                / "chapter_001_narrator_002.mp3"
            )
            expected_image_path_1 = (
                story_setup_with_recipe
                / "video"
                / "chapter_001"
                / "assets"
                / "narrator_and_image"
                / "chapter_001_image_001.png"
            )
            expected_image_path_2 = (
                story_setup_with_recipe
                / "video"
                / "chapter_001"
                / "assets"
                / "narrator_and_image"
                / "chapter_001_image_002.png"
            )

            assert (
                video_asset_manager.video_assets.narrator_assets[1]
                == expected_narrator_path
            )  # Generated new
            assert (
                video_asset_manager.video_assets.image_assets[0]
                == expected_image_path_1
            )  # Generated new
            assert (
                video_asset_manager.video_assets.image_assets[1]
                == expected_image_path_2
            )  # Generated new

    def test_get_missing_narrator_and_image_assets_detection(
        self, story_setup_with_recipe
    ):
        """Test proper detection of missing assets."""
        # Create asset manager
        video_asset_manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Get asset folder path through public interface
        asset_folder = (
            video_asset_manager.video_assets.asset_file_path.parent
            / "assets"
            / "narrator_and_image"
        )
        asset_folder.mkdir(parents=True, exist_ok=True)

        # Initially all assets should be missing (we have 2 scenes from the recipe)
        missing = (
            video_asset_manager.video_assets.get_missing_narrator_and_image_assets()
        )
        assert 0 in missing["narrator"]
        assert 0 in missing["image"]
        assert 1 in missing["narrator"]  # Second scene
        assert 1 in missing["image"]  # Second scene

        # Add narrator asset for scene 0
        narrator_file = asset_folder / "narrator_001.mp3"
        narrator_file.write_text("audio content")
        video_asset_manager.video_assets.set_scene_narrator(0, narrator_file)

        # Now only image for scene 0 and all assets for scene 1 should be missing
        missing = (
            video_asset_manager.video_assets.get_missing_narrator_and_image_assets()
        )
        assert 0 not in missing["narrator"]
        assert 0 in missing["image"]
        assert 1 in missing["narrator"]
        assert 1 in missing["image"]

        # Add image asset for scene 0
        image_file = asset_folder / "image_001.png"
        image_file.write_text("image content")
        video_asset_manager.video_assets.set_scene_image(0, image_file)

        # Now only scene 1 assets should be missing
        missing = (
            video_asset_manager.video_assets.get_missing_narrator_and_image_assets()
        )
        assert 0 not in missing["narrator"]
        assert 0 not in missing["image"]
        assert 1 in missing["narrator"]
        assert 1 in missing["image"]

        # Add assets for scene 1
        narrator_file_2 = asset_folder / "narrator_002.mp3"
        image_file_2 = asset_folder / "image_002.png"
        narrator_file_2.write_text("audio content 2")
        image_file_2.write_text("image content 2")
        video_asset_manager.video_assets.set_scene_narrator(1, narrator_file_2)
        video_asset_manager.video_assets.set_scene_image(1, image_file_2)

        # Now nothing should be missing
        missing = (
            video_asset_manager.video_assets.get_missing_narrator_and_image_assets()
        )
        assert 0 not in missing["narrator"]
        assert 0 not in missing["image"]
        assert 1 not in missing["narrator"]
        assert 1 not in missing["image"]
        assert video_asset_manager.video_assets.is_complete()

    @patch(
        "ai_video_creator.modules.narrator_and_image.narrator_and_image_asset_manager.begin_file_logging"
    )
    @patch(
        "ai_video_creator.modules.narrator_and_image.narrator_and_image_asset_manager.IAudioGenerator"
    )
    def test_generate_narrator_asset_error_handling(
        self, mock_audio_gen_class, mock_logging, story_setup_with_recipe
    ):
        """Test error handling during narrator asset generation."""
        # Setup mock to raise an exception
        mock_audio_gen = Mock()
        mock_audio_gen.clone_text_to_speech.side_effect = IOError("Generator failed")
        mock_audio_gen_class.return_value = mock_audio_gen

        # Create asset manager
        video_asset_manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Mock the recipe's GENERATOR method to return our failing generator
        with patch.object(
            video_asset_manager.recipe.narrator_data[0],
            "GENERATOR",
            return_value=mock_audio_gen,
        ):

            # Call the actual private method which should handle the exception gracefully
            video_asset_manager._generate_narrator_asset(0)

            # Verify asset was not set (should still be None)
            assert not video_asset_manager.video_assets.has_narrator(0)
            # Verify the narrator_assets list still has None at index 0
            assert video_asset_manager.video_assets.narrator_assets[0] is None

    @patch(
        "ai_video_creator.modules.narrator_and_image.narrator_and_image_asset_manager.begin_file_logging"
    )
    @patch(
        "ai_video_creator.modules.narrator_and_image.narrator_and_image_asset_manager.IImageGenerator"
    )
    def test_generate_image_asset_error_handling(
        self, mock_image_gen_class, mock_logging, story_setup_with_recipe
    ):
        """Test error handling during image asset generation."""
        # Setup mock to raise an exception
        mock_image_gen = Mock()
        mock_image_gen.text_to_image.side_effect = RuntimeError(
            "Image generation failed"
        )
        mock_image_gen_class.return_value = mock_image_gen

        # Create asset manager
        video_asset_manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Mock the recipe's GENERATOR method to return our failing generator
        with patch.object(
            video_asset_manager.recipe.image_data[0],
            "GENERATOR",
            return_value=mock_image_gen,
        ):

            # Call the actual private method which should handle the exception gracefully
            video_asset_manager._generate_image_asset(0)

            # Verify asset was not set (should still be None)
            assert not video_asset_manager.video_assets.has_image(0)
            # Verify the image_assets list still has None at index 0
            assert video_asset_manager.video_assets.image_assets[0] is None
