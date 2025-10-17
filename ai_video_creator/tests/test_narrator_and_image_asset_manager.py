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

        # Create separate narrator and image recipe files
        narrator_recipe_file = chapter_folder / "narrator_recipe.json"
        image_recipe_file = chapter_folder / "image_recipe.json"

        narrator_recipe = {
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
        }

        image_recipe = {
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

        with open(narrator_recipe_file, "w", encoding="utf-8") as f:
            json.dump(narrator_recipe, f)

        with open(image_recipe_file, "w", encoding="utf-8") as f:
            json.dump(image_recipe, f)

        return story_folder

    def test_asset_manager_initialization(self, story_setup_with_recipe):
        """Test VideoAssetManager initialization with recipe synchronization."""
        manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        assert len(manager.narrator_builder.recipe.narrator_data) == 2
        assert len(manager.image_builder.recipe.image_data) == 2

        assert len(manager.narrator_builder.narrator_assets.narrator_assets) == 2
        assert len(manager.image_builder.image_assets.image_assets) == 2

        assert not (
            manager.narrator_builder.narrator_assets.is_complete()
            and manager.image_builder.image_assets.is_complete()
        )
        missing_narrator = (
            manager.narrator_builder.narrator_assets.get_missing_narrator_assets()
        )
        missing_image = manager.image_builder.image_assets.get_missing_image_assets()
        assert missing_narrator == [0, 1]
        assert missing_image == [0, 1]

    def test_asset_manager_creates_asset_file(self, story_setup_with_recipe):
        """Test that VideoAssetManager creates and manages asset files properly."""
        manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Create separate asset folders for narrator and image
        narrator_assets_folder = (
            story_setup_with_recipe / "video" / "chapter_001" / "assets" / "narrators"
        )
        image_assets_folder = (
            story_setup_with_recipe / "video" / "chapter_001" / "assets" / "images"
        )
        narrator_assets_folder.mkdir(parents=True, exist_ok=True)
        image_assets_folder.mkdir(parents=True, exist_ok=True)

        test_narrator = narrator_assets_folder / "narrator_001.mp3"
        test_image = image_assets_folder / "image_001.jpg"
        test_narrator.touch()
        test_image.touch()

        manager.narrator_builder.narrator_assets.set_scene_narrator(0, test_narrator)
        manager.image_builder.image_assets.set_scene_image(0, test_image)
        manager.narrator_builder.narrator_assets.save_assets_to_file()
        manager.image_builder.image_assets.save_assets_to_file()

        narrator_asset_file = manager.narrator_builder.narrator_assets.asset_file_path
        image_asset_file = manager.image_builder.image_assets.asset_file_path
        assert narrator_asset_file.exists()
        assert image_asset_file.exists()

        with open(narrator_asset_file, "r", encoding="utf-8") as f:
            narrator_saved_data = json.load(f)

        with open(image_asset_file, "r", encoding="utf-8") as f:
            image_saved_data = json.load(f)

        assert "assets" in narrator_saved_data
        assert "assets" in image_saved_data
        assert len(narrator_saved_data["assets"]) == 2
        assert len(image_saved_data["assets"]) == 2
        assert (
            narrator_saved_data["assets"][0]["narrator"]
            == "assets/narrators/narrator_001.mp3"
        )
        assert image_saved_data["assets"][0]["image"] == "assets/images/image_001.jpg"
        assert narrator_saved_data["assets"][1]["narrator"] is None
        assert image_saved_data["assets"][1]["image"] is None

    def test_asset_manager_with_existing_assets(self, story_setup_with_recipe):
        """Test VideoAssetManager loading existing asset files."""
        video_folder = story_setup_with_recipe / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)

        # Create separate asset files for the new architecture
        narrator_asset_file = chapter_folder / "narrator_assets.json"
        image_asset_file = chapter_folder / "image_assets.json"

        # Create actual asset files within the allowed directory
        narrator_assets_folder = chapter_folder / "assets" / "narrators"
        image_assets_folder = chapter_folder / "assets" / "images"
        narrator_assets_folder.mkdir(parents=True, exist_ok=True)
        image_assets_folder.mkdir(parents=True, exist_ok=True)

        narrator1 = narrator_assets_folder / "narrator1.mp3"
        narrator2 = narrator_assets_folder / "narrator2.mp3"
        image1 = image_assets_folder / "image1.jpg"
        image2 = image_assets_folder / "image2.jpg"

        for file in [narrator1, narrator2, image1, image2]:
            file.touch()

        narrator_existing_data = {
            "assets": [
                {"index": 1, "narrator": "assets/narrators/narrator1.mp3"},
                {"index": 2, "narrator": "assets/narrators/narrator2.mp3"},
            ]
        }

        image_existing_data = {
            "assets": [
                {"index": 1, "image": "assets/images/image1.jpg"},
                {"index": 2, "image": "assets/images/image2.jpg"},
            ]
        }

        with open(narrator_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_existing_data, f)

        with open(image_asset_file, "w", encoding="utf-8") as f:
            json.dump(image_existing_data, f)

        manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        assert manager.narrator_builder.narrator_assets.narrator_assets[0] == narrator1
        assert manager.image_builder.image_assets.image_assets[0] == image1
        assert manager.narrator_builder.narrator_assets.narrator_assets[1] == narrator2
        assert manager.image_builder.image_assets.image_assets[1] == image2

        assert (
            manager.narrator_builder.narrator_assets.is_complete()
            and manager.image_builder.image_assets.is_complete()
        )

    def test_asset_synchronization_different_sizes(self, story_setup_with_recipe):
        """Test asset synchronization when asset file has different size than recipe."""
        video_folder = Path(story_setup_with_recipe) / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)

        # Create separate asset files for the new architecture (only one asset each)
        narrator_asset_file = chapter_folder / "narrator_assets.json"
        image_asset_file = chapter_folder / "image_assets.json"

        # Create actual asset files within the allowed directory using new structure
        narrator_assets_folder = chapter_folder / "assets" / "narrators"
        image_assets_folder = chapter_folder / "assets" / "images"
        narrator_assets_folder.mkdir(parents=True, exist_ok=True)
        image_assets_folder.mkdir(parents=True, exist_ok=True)

        narrator1 = narrator_assets_folder / "narrator1.mp3"
        image1 = image_assets_folder / "image1.jpg"

        for file in [narrator1, image1]:
            file.touch()

        # Create asset files with only one asset each (recipe has 2)
        narrator_existing_data = {
            "assets": [
                {"index": 1, "narrator": "assets/narrators/narrator1.mp3"},
            ]
        }

        image_existing_data = {
            "assets": [
                {"index": 1, "image": "assets/images/image1.jpg"},
            ]
        }

        with open(narrator_asset_file, "w", encoding="utf-8") as f:
            json.dump(narrator_existing_data, f)

        with open(image_asset_file, "w", encoding="utf-8") as f:
            json.dump(image_existing_data, f)

        manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Should synchronize to recipe size (2 assets each)
        assert len(manager.narrator_builder.narrator_assets.narrator_assets) == 2
        assert len(manager.image_builder.image_assets.image_assets) == 2

        # First assets should be loaded from files
        assert manager.narrator_builder.narrator_assets.narrator_assets[0] == narrator1
        assert manager.image_builder.image_assets.image_assets[0] == image1

        # Second assets should be None (not in asset file)
        assert manager.narrator_builder.narrator_assets.narrator_assets[1] is None
        assert manager.image_builder.image_assets.image_assets[1] is None

        # Manager should not be complete
        assert not (
            manager.narrator_builder.narrator_assets.is_complete()
            and manager.image_builder.image_assets.is_complete()
        )

    def test_cleanup_assets_removes_unused_files(self, story_setup_with_recipe):
        """Test that cleanup_assets removes files not referenced in assets."""

        video_folder = Path(story_setup_with_recipe) / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)

        # Create separate asset folders for new architecture
        narrator_assets_folder = chapter_folder / "assets" / "narrators"
        image_assets_folder = chapter_folder / "assets" / "images"
        narrator_assets_folder.mkdir(parents=True, exist_ok=True)
        image_assets_folder.mkdir(parents=True, exist_ok=True)

        # Create some asset files that should be kept
        valid_narrator1 = narrator_assets_folder / "chapter_001_narrator_001.mp3"
        valid_image1 = image_assets_folder / "chapter_001_image_001.png"
        valid_narrator2 = narrator_assets_folder / "chapter_001_narrator_002.mp3"

        # Create some files that should be deleted
        old_narrator = narrator_assets_folder / "old_narrator.mp3"
        old_image = image_assets_folder / "old_image.png"
        # Note: temp files without narrator/image patterns won't be deleted
        # This is safer behavior in the new architecture

        # Create all files
        for file_path in [
            valid_narrator1,
            valid_image1,
            valid_narrator2,
            old_narrator,
            old_image,
        ]:
            file_path.touch()

        manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Set up some assets to be kept - use absolute paths as production would
        manager.narrator_builder.narrator_assets.set_scene_narrator(0, valid_narrator1)
        manager.image_builder.image_assets.set_scene_image(0, valid_image1)
        manager.narrator_builder.narrator_assets.set_scene_narrator(1, valid_narrator2)
        # Note: scene 1 has no image asset (None)

        # Run cleanup
        manager.clean_unused_assets()

        # Verify that valid assets are kept
        assert valid_narrator1.exists()
        assert valid_image1.exists()
        assert valid_narrator2.exists()

        # Verify that unused files matching asset patterns are deleted
        assert not old_narrator.exists()
        assert not old_image.exists()

    def test_cleanup_assets_handles_none_values_in_assets(
        self, story_setup_with_recipe
    ):
        """Test that cleanup_assets properly handles None values in asset lists."""
        video_folder = Path(story_setup_with_recipe) / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)

        # Create separate asset folders for new architecture
        narrator_assets_folder = chapter_folder / "assets" / "narrators"
        image_assets_folder = chapter_folder / "assets" / "images"
        narrator_assets_folder.mkdir(parents=True, exist_ok=True)
        image_assets_folder.mkdir(parents=True, exist_ok=True)

        # Create some files with proper patterns for cleanup
        valid_file = narrator_assets_folder / "valid_narrator.mp3"
        invalid_narrator_file = narrator_assets_folder / "invalid_narrator.mp3"
        invalid_image_file = image_assets_folder / "invalid_image.png"

        valid_file.touch()
        invalid_narrator_file.touch()
        invalid_image_file.touch()

        with patch("logging_utils.logger"):
            manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

            # Set only one asset, leaving others as None - use absolute path as production would
            manager.narrator_builder.narrator_assets.set_scene_narrator(0, valid_file)
            # manager.narrator_builder.narrator_assets.narrator_assets[1] is None
            # manager.image_builder.image_assets.image_assets[0] and [1] are None

            # Run cleanup
            manager.clean_unused_assets()

            # Verify that the valid file is kept
            assert valid_file.exists()

            # Verify that the unused files are deleted
            assert not invalid_narrator_file.exists()
            assert not invalid_image_file.exists()

    def test_cleanup_assets_preserves_directories(self, story_setup_with_recipe):
        """Test that cleanup_assets only removes files, not directories."""
        video_folder = Path(story_setup_with_recipe) / "video"
        chapter_folder = video_folder / "chapter_001"
        chapter_folder.mkdir(parents=True, exist_ok=True)

        # Create separate asset folders for new architecture
        narrator_assets_folder = chapter_folder / "assets" / "narrator"
        image_assets_folder = chapter_folder / "assets" / "image"
        narrator_assets_folder.mkdir(parents=True, exist_ok=True)
        image_assets_folder.mkdir(parents=True, exist_ok=True)

        # Create subdirectories in both asset folders
        narrator_sub_dir = narrator_assets_folder / "subdirectory"
        image_sub_dir = image_assets_folder / "subdirectory"
        narrator_sub_dir.mkdir()
        image_sub_dir.mkdir()

        # Create files inside the subdirectories with proper patterns
        file_in_narrator_subdir = narrator_sub_dir / "test_narrator.txt"
        file_in_image_subdir = image_sub_dir / "test_image.txt"
        file_in_narrator_subdir.touch()
        file_in_image_subdir.touch()

        # Create files in the main assets folders with proper patterns
        main_narrator_file = narrator_assets_folder / "main_narrator.txt"
        main_image_file = image_assets_folder / "main_image.txt"
        main_narrator_file.touch()
        main_image_file.touch()

        manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Run cleanup with no assets set (all should be deleted except directories)
        manager.clean_unused_assets()

        # Verify that the subdirectories still exist
        assert narrator_sub_dir.exists()
        assert narrator_sub_dir.is_dir()
        assert image_sub_dir.exists()
        assert image_sub_dir.is_dir()

    def test_generate_narrator_and_image_assets_success(self, story_setup_with_recipe):
        """Test successful asset generation process with fake generators."""
        # Create asset manager
        video_asset_manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Create fake generators that create real files for testing
        class FakeAudioGenerator:
            def clone_text_to_speech(self, recipe, output_file_path):
                # Create actual file to test file operations
                output_file_path.parent.mkdir(parents=True, exist_ok=True)
                output_file_path.write_text(f"Fake audio for: {recipe.prompt}")
                return output_file_path

        class FakeImageGenerator:
            def text_to_image(self, recipe, output_file_path):
                # Create actual file to test file operations
                output_file_path.parent.mkdir(parents=True, exist_ok=True)
                output_file_path.write_text(f"Fake image for: {recipe.prompt}")
                return [output_file_path]

        # Replace only the generator classes, not the core business logic
        for recipe in video_asset_manager.narrator_builder.recipe.narrator_data:
            recipe.GENERATOR_TYPE = lambda: FakeAudioGenerator()

        for recipe in video_asset_manager.image_builder.recipe.image_data:
            recipe.GENERATOR_TYPE = lambda: FakeImageGenerator()

        # Test the actual generation logic without mocking core methods
        video_asset_manager.generate_narrator_and_image_assets()

        # Verify business logic executed correctly by checking actual results
        # The actual files should be generated in separate asset folders with specific names
        expected_narrator_path_1 = (
            story_setup_with_recipe
            / "video"
            / "chapter_001"
            / "assets"
            / "narrators"
            / "chapter_001_narrator_001.mp3"
        )
        expected_narrator_path_2 = (
            story_setup_with_recipe
            / "video"
            / "chapter_001"
            / "assets"
            / "narrators"
            / "chapter_001_narrator_002.mp3"
        )
        expected_image_path_1 = (
            story_setup_with_recipe
            / "video"
            / "chapter_001"
            / "assets"
            / "images"
            / "chapter_001_image_001.png"
        )
        expected_image_path_2 = (
            story_setup_with_recipe
            / "video"
            / "chapter_001"
            / "assets"
            / "images"
            / "chapter_001_image_002.png"
        )

        # Verify files were actually created through the business logic
        assert expected_narrator_path_1.exists()
        assert expected_narrator_path_2.exists()
        assert expected_image_path_1.exists()
        assert expected_image_path_2.exists()

        # Verify content was written with recipe information
        narrator_1_content = expected_narrator_path_1.read_text(encoding="utf-8")
        assert "Test narrator 1" in narrator_1_content

        image_1_content = expected_image_path_1.read_text(encoding="utf-8")
        assert "Test prompt 1" in image_1_content

        # Verify assets were set in the asset manager through actual business logic
        assert (
            video_asset_manager.narrator_builder.narrator_assets.narrator_assets[0]
            == expected_narrator_path_1
        )
        assert (
            video_asset_manager.narrator_builder.narrator_assets.narrator_assets[1]
            == expected_narrator_path_2
        )
        assert (
            video_asset_manager.image_builder.image_assets.image_assets[0]
            == expected_image_path_1
        )
        assert (
            video_asset_manager.image_builder.image_assets.image_assets[1]
            == expected_image_path_2
        )

        # Verify business logic completion state
        assert video_asset_manager.narrator_builder.narrator_assets.is_complete()
        assert video_asset_manager.image_builder.image_assets.is_complete()

    def test_generate_assets_with_existing_assets_skips_generation(
        self, story_setup_with_recipe
    ):
        """Test that existing assets are not regenerated."""
        # Create asset manager
        video_asset_manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Create actual asset files in separate folders so has_* methods return True naturally
        narrator_folder = (
            story_setup_with_recipe / "video" / "chapter_001" / "assets" / "narrator"
        )
        image_folder = (
            story_setup_with_recipe / "video" / "chapter_001" / "assets" / "image"
        )
        narrator_folder.mkdir(parents=True, exist_ok=True)
        image_folder.mkdir(parents=True, exist_ok=True)

        # Create existing files in both folders
        existing_audio_1 = narrator_folder / "existing_narrator_1.mp3"
        existing_audio_2 = narrator_folder / "existing_narrator_2.mp3"
        existing_image_1 = image_folder / "existing_image_1.png"
        existing_image_2 = image_folder / "existing_image_2.png"

        existing_audio_1.write_text("existing audio 1")
        existing_audio_2.write_text("existing audio 2")
        existing_image_1.write_text("existing image 1")
        existing_image_2.write_text("existing image 2")

        # Set existing assets using actual business logic with the new separate API
        video_asset_manager.narrator_builder.narrator_assets.set_scene_narrator(
            0, existing_audio_1
        )
        video_asset_manager.narrator_builder.narrator_assets.set_scene_narrator(
            1, existing_audio_2
        )
        video_asset_manager.image_builder.image_assets.set_scene_image(
            0, existing_image_1
        )
        video_asset_manager.image_builder.image_assets.set_scene_image(
            1, existing_image_2
        )

        # Track generation calls to verify skipping logic
        generation_calls = []

        class TrackingFakeGenerator:
            def clone_text_to_speech(self, recipe, output_path):
                generation_calls.append(f"audio: {recipe.prompt}")
                return output_path

            def text_to_image(self, recipe, output_path):
                generation_calls.append(f"image: {recipe.prompt}")
                return [output_path]

        # Replace generators with tracking versions
        for recipe in video_asset_manager.narrator_builder.recipe.narrator_data:
            recipe.GENERATOR_TYPE = lambda: TrackingFakeGenerator()
        for recipe in video_asset_manager.image_builder.recipe.image_data:
            recipe.GENERATOR_TYPE = lambda: TrackingFakeGenerator()

        # Run the actual generation logic
        video_asset_manager.generate_narrator_and_image_assets()

        # Verify no generators were called since all assets already exist
        assert len(generation_calls) == 0

    def test_generate_assets_handles_partial_completion(self, story_setup_with_recipe):
        """Test generation when only some assets exist."""
        # Create asset manager
        video_asset_manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Create asset folders and set up existing narrator for scene 0 only
        narrator_folder = (
            story_setup_with_recipe / "video" / "chapter_001" / "assets" / "narrators"
        )
        image_folder = (
            story_setup_with_recipe / "video" / "chapter_001" / "assets" / "images"
        )
        narrator_folder.mkdir(parents=True, exist_ok=True)
        image_folder.mkdir(parents=True, exist_ok=True)
        existing_audio = narrator_folder / "existing_narrator.mp3"
        existing_audio.write_text("existing audio content")
        video_asset_manager.narrator_builder.narrator_assets.set_scene_narrator(
            0, existing_audio
        )
        # Scene 1 narrator and both scene images are missing

        # Use mock generators with side effects to create test files
        mock_audio_gen = Mock()
        mock_image_gen = Mock()

        def audio_side_effect(*args, **kwargs):
            # Create a simple test file using the output_file_path
            output_path = kwargs.get("output_file_path")
            if output_path:
                Path(output_path).write_text("Test audio content", encoding="utf-8")
                return output_path
            return None

        def image_side_effect(*args, **kwargs):
            # Create a simple test file using the output_file_path
            output_path = kwargs.get("output_file_path")
            if output_path:
                Path(output_path).write_text("Test image content", encoding="utf-8")
                return [output_path]  # Return list as expected by image generators
            return []

        mock_audio_gen.clone_text_to_speech.side_effect = audio_side_effect
        mock_image_gen.text_to_image.side_effect = image_side_effect

        with patch.object(
            video_asset_manager.narrator_builder.recipe.narrator_data[0],
            "GENERATOR_TYPE",
            return_value=mock_audio_gen,
        ), patch.object(
            video_asset_manager.narrator_builder.recipe.narrator_data[1],
            "GENERATOR_TYPE",
            return_value=mock_audio_gen,
        ), patch.object(
            video_asset_manager.image_builder.recipe.image_data[0],
            "GENERATOR_TYPE",
            return_value=mock_image_gen,
        ), patch.object(
            video_asset_manager.image_builder.recipe.image_data[1],
            "GENERATOR_TYPE",
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
                video_asset_manager.narrator_builder.narrator_assets.narrator_assets[0]
                == existing_audio
            )  # Kept existing

            # Generated assets should be in the expected locations with proper names in separate folders
            expected_narrator_path = (
                story_setup_with_recipe
                / "video"
                / "chapter_001"
                / "assets"
                / "narrators"
                / "chapter_001_narrator_002.mp3"
            )
            expected_image_path_1 = (
                story_setup_with_recipe
                / "video"
                / "chapter_001"
                / "assets"
                / "images"
                / "chapter_001_image_001.png"
            )
            expected_image_path_2 = (
                story_setup_with_recipe
                / "video"
                / "chapter_001"
                / "assets"
                / "images"
                / "chapter_001_image_002.png"
            )

            # Verify files were actually created
            assert expected_narrator_path.exists()
            assert expected_image_path_1.exists()
            assert expected_image_path_2.exists()

            assert (
                video_asset_manager.narrator_builder.narrator_assets.narrator_assets[1]
                == expected_narrator_path
            )  # Generated new
            assert (
                video_asset_manager.image_builder.image_assets.image_assets[0]
                == expected_image_path_1
            )  # Generated new
            assert (
                video_asset_manager.image_builder.image_assets.image_assets[1]
                == expected_image_path_2
            )  # Generated new

    def test_generate_assets_handles_generation_failures(self, story_setup_with_recipe):
        """Test that generation failures are handled gracefully."""
        # Create asset manager
        video_asset_manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Create failing mock generators
        failing_audio_gen = Mock()
        failing_image_gen = Mock()

        # Set up failures through side effects - using RuntimeError which is caught by the actual code
        failing_audio_gen.clone_text_to_speech.side_effect = RuntimeError(
            "Audio generation failed"
        )
        failing_image_gen.text_to_image.side_effect = RuntimeError(
            "Image generation failed"
        )

        with patch.object(
            video_asset_manager.narrator_builder.recipe.narrator_data[0],
            "GENERATOR_TYPE",
            return_value=failing_audio_gen,
        ), patch.object(
            video_asset_manager.narrator_builder.recipe.narrator_data[1],
            "GENERATOR_TYPE",
            return_value=failing_audio_gen,
        ), patch.object(
            video_asset_manager.image_builder.recipe.image_data[0],
            "GENERATOR_TYPE",
            return_value=failing_image_gen,
        ), patch.object(
            video_asset_manager.image_builder.recipe.image_data[1],
            "GENERATOR_TYPE",
            return_value=failing_image_gen,
        ):

            # Generation should continue despite failures (exceptions are caught and logged)
            video_asset_manager.generate_narrator_and_image_assets()

            # Verify generators were called despite failures
            assert failing_audio_gen.clone_text_to_speech.call_count >= 1
            assert failing_image_gen.text_to_image.call_count >= 1

            # Verify no assets were set due to failures
            assert (
                video_asset_manager.narrator_builder.narrator_assets.narrator_assets[0]
                is None
            )
            assert (
                video_asset_manager.image_builder.image_assets.image_assets[0] is None
            )

    def test_get_missing_narrator_and_image_assets_detection(
        self, story_setup_with_recipe
    ):
        """Test proper detection of missing assets."""
        # Create asset manager
        video_asset_manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Create asset folders for the new architecture
        narrator_folder = (
            story_setup_with_recipe / "video" / "chapter_001" / "assets" / "narrator"
        )
        image_folder = (
            story_setup_with_recipe / "video" / "chapter_001" / "assets" / "image"
        )
        narrator_folder.mkdir(parents=True, exist_ok=True)
        image_folder.mkdir(parents=True, exist_ok=True)

        # Initially all assets should be missing (we have 2 scenes from the recipe)
        missing_narrator = (
            video_asset_manager.narrator_builder.narrator_assets.get_missing_narrator_assets()
        )
        missing_image = (
            video_asset_manager.image_builder.image_assets.get_missing_image_assets()
        )

        assert 0 in missing_narrator
        assert 1 in missing_narrator  # Second scene
        assert 0 in missing_image
        assert 1 in missing_image  # Second scene

        # Add narrator asset for scene 0
        narrator_file = narrator_folder / "narrator_001.mp3"
        narrator_file.write_text("audio content")
        video_asset_manager.narrator_builder.narrator_assets.set_scene_narrator(
            0, narrator_file
        )

        # Now only image for scene 0 and all assets for scene 1 should be missing
        missing_narrator = (
            video_asset_manager.narrator_builder.narrator_assets.get_missing_narrator_assets()
        )
        missing_image = (
            video_asset_manager.image_builder.image_assets.get_missing_image_assets()
        )

        assert 0 not in missing_narrator
        assert 1 in missing_narrator
        assert 0 in missing_image
        assert 1 in missing_image

        # Add image asset for scene 0
        image_file = image_folder / "image_001.png"
        image_file.write_text("image content")
        video_asset_manager.image_builder.image_assets.set_scene_image(0, image_file)

        # Now only scene 1 assets should be missing
        missing_narrator = (
            video_asset_manager.narrator_builder.narrator_assets.get_missing_narrator_assets()
        )
        missing_image = (
            video_asset_manager.image_builder.image_assets.get_missing_image_assets()
        )

        assert 0 not in missing_narrator
        assert 1 in missing_narrator
        assert 0 not in missing_image
        assert 1 in missing_image

        # Add assets for scene 1
        narrator_file_2 = narrator_folder / "narrator_002.mp3"
        image_file_2 = image_folder / "image_002.png"
        narrator_file_2.write_text("audio content 2")
        image_file_2.write_text("image content 2")
        video_asset_manager.narrator_builder.narrator_assets.set_scene_narrator(
            1, narrator_file_2
        )
        video_asset_manager.image_builder.image_assets.set_scene_image(1, image_file_2)

        # Now nothing should be missing and both should be complete
        missing_narrator = (
            video_asset_manager.narrator_builder.narrator_assets.get_missing_narrator_assets()
        )
        missing_image = (
            video_asset_manager.image_builder.image_assets.get_missing_image_assets()
        )

        assert 0 not in missing_narrator
        assert 1 not in missing_narrator
        assert 0 not in missing_image
        assert 1 not in missing_image
        assert video_asset_manager.narrator_builder.narrator_assets.is_complete()
        assert video_asset_manager.image_builder.image_assets.is_complete()

    def test_generate_narrator_asset_error_handling(
        self, story_setup_with_recipe
    ):
        """Test error handling during narrator asset generation."""
        # Create asset manager
        video_asset_manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Mock the recipe's GENERATOR_TYPE method to return a failing generator
        mock_audio_gen = Mock()
        mock_audio_gen.clone_text_to_speech.side_effect = IOError("Generator failed")

        with patch.object(
            video_asset_manager.narrator_builder.recipe.narrator_data[0],
            "GENERATOR_TYPE",
            return_value=mock_audio_gen,
        ):
            # The method should handle the error gracefully and not crash
            video_asset_manager.narrator_builder.generate_narrator_asset(0)

            # Verify that the asset was not set due to the error
            assert (
                video_asset_manager.narrator_builder.narrator_assets.narrator_assets[0]
                is None
            )

    def test_generate_image_asset_error_handling(
        self, story_setup_with_recipe
    ):
        """Test error handling during image asset generation."""
        # Create asset manager
        video_asset_manager = NarratorAndImageAssetManager(story_setup_with_recipe, 0)

        # Mock the recipe's GENERATOR_TYPE method to return a failing generator
        mock_image_gen = Mock()
        mock_image_gen.text_to_image.side_effect = IOError("Generator failed")

        with patch.object(
            video_asset_manager.image_builder.recipe.image_data[0],
            "GENERATOR_TYPE",
            return_value=mock_image_gen,
        ):
            # The method should handle the error gracefully and not crash
            video_asset_manager.image_builder.generate_image_asset(0)

            # Verify that the asset was not set due to the error
            assert (
                video_asset_manager.image_builder.image_assets.image_assets[0] is None
            )
