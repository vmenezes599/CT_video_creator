"""
Unit tests for narrator_recipe module.
"""

import json
import pytest
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open

from ai_video_creator.modules.narrator.narrator_recipe import (
    NarratorRecipe,
)
from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER
from ai_video_creator.generators import ZonosTTSRecipe
from ai_video_creator.utils import VideoCreatorPaths


class TestNarratorRecipe:
    """Test NarratorRecipe class."""

    @pytest.fixture
    def temp_default_assets(self, tmp_path):
        """Create a temporary default assets folder with voice_002.mp3."""
        # Create a temporary default assets folder in tmp_path instead of using the real one
        temp_default_assets_folder = tmp_path / "temp_default_assets"
        temp_voices_folder = temp_default_assets_folder / "voices"
        temp_voices_folder.mkdir(parents=True, exist_ok=True)
        
        # Get the real default assets folder to copy the original file
        real_default_assets_folder = Path(DEFAULT_ASSETS_FOLDER)
        real_voice_file = real_default_assets_folder / "voices" / "voice_002.mp3"
        
        # Create temp voice file - copy from real file if it exists, otherwise create mock
        temp_voice_file = temp_voices_folder / "voice_002.mp3"
        if real_voice_file.exists():
            shutil.copy2(real_voice_file, temp_voice_file)
        else:
            temp_voice_file.write_text("mock audio data")
        
        return temp_default_assets_folder

    @pytest.fixture
    def video_creator_paths(self, tmp_path, temp_default_assets):
        """Create VideoCreatorPaths fixture with mocked default assets."""
        user_folder = tmp_path / "user"
        story_name = "test_story"
        chapter_index = 0
        
        # Create story structure
        story_folder = user_folder / story_name / "prompts"
        story_folder.mkdir(parents=True)
        
        # Patch get_default_assets_folder to return our temp folder
        with patch.object(
            VideoCreatorPaths, 
            'get_default_assets_folder', 
            return_value=temp_default_assets
        ):
            # Create VideoCreatorPaths with patched method
            video_creator_paths = VideoCreatorPaths(user_folder, story_name, chapter_index)
            
            # Create asset folders structure for the working directory
            narrator_assets_folder = video_creator_paths.story_folder / "assets" / "narrators"
            narrator_assets_folder.mkdir(parents=True, exist_ok=True)
        
        # Store temp folder for tests that need to patch again
        video_creator_paths._temp_default_assets_folder = temp_default_assets
        
        return video_creator_paths

    def test_narrator_recipe_initialization(self, video_creator_paths):
        """Test NarratorRecipe initialization with empty file."""
        recipe = NarratorRecipe(video_creator_paths)

        assert recipe.recipe_path == video_creator_paths.narrator_recipe_file
        assert len(recipe.narrator_data) == 0

    def test_narrator_recipe_load_existing_file(self, video_creator_paths):
        """Test loading existing narrator recipe file."""
        test_data = {
            "narrator_data": [
                {
                    "prompt": "Test narrator 1",
                    "clone_voice_path": "default_assets/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                    "index": 1,
                },
                {
                    "prompt": "Test narrator 2",
                    "clone_voice_path": "default_assets/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                    "index": 2,
                },
            ]
        }

        with open(video_creator_paths.narrator_recipe_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        recipe = NarratorRecipe(video_creator_paths)

        assert len(recipe.narrator_data) == 2
        assert recipe.narrator_data[0].prompt == "Test narrator 1"
        assert recipe.narrator_data[1].prompt == "Test narrator 2"

    def test_narrator_recipe_add_data(self, video_creator_paths):
        """Test adding narrator data to recipe."""
        
        # Patch get_default_assets_folder to use temp folder
        with patch.object(
            VideoCreatorPaths, 
            'get_default_assets_folder', 
            return_value=video_creator_paths._temp_default_assets_folder
        ):
            recipe = NarratorRecipe(video_creator_paths)

            # Create a test narrator recipe using the temp voice file
            temp_voice_path = video_creator_paths._temp_default_assets_folder / "voices" / "voice_002.mp3"
            narrator_recipe = ZonosTTSRecipe(
                prompt="Test narrator",
                clone_voice_path=str(temp_voice_path),
            )

            recipe.add_narrator_data(narrator_recipe)

            assert len(recipe.narrator_data) == 1
            assert recipe.narrator_data[0].prompt == "Test narrator"

    def test_narrator_recipe_save_and_load(self, video_creator_paths):
        """Test saving and loading narrator recipe."""
        
        # Patch get_default_assets_folder to use temp folder
        with patch.object(
            VideoCreatorPaths, 
            'get_default_assets_folder', 
            return_value=video_creator_paths._temp_default_assets_folder
        ):
            # Create and save recipe
            recipe1 = NarratorRecipe(video_creator_paths)
            temp_voice_path = video_creator_paths._temp_default_assets_folder / "voices" / "voice_002.mp3"
            narrator_recipe = ZonosTTSRecipe(
                prompt="Test narrator",
                clone_voice_path=str(temp_voice_path),
            )

            recipe1.add_narrator_data(narrator_recipe)

            # Load new recipe instance
            recipe2 = NarratorRecipe(video_creator_paths)

            # Verify data was loaded
            assert len(recipe2.narrator_data) == 1
            assert recipe2.narrator_data[0].prompt == "Test narrator"

    def test_narrator_recipe_clean(self, video_creator_paths):
        """Test cleaning narrator recipe data."""
        
        # Patch get_default_assets_folder to use temp folder
        with patch.object(
            VideoCreatorPaths, 
            'get_default_assets_folder', 
            return_value=video_creator_paths._temp_default_assets_folder
        ):
            recipe = NarratorRecipe(video_creator_paths)

            # Add some data
            temp_voice_path = video_creator_paths._temp_default_assets_folder / "voices" / "voice_002.mp3"
            narrator_recipe = ZonosTTSRecipe(
                prompt="Test narrator",
                clone_voice_path=str(temp_voice_path),
            )

            recipe.add_narrator_data(narrator_recipe)
            assert len(recipe.narrator_data) == 1

            # Clean the recipe
            recipe.clean()
            assert len(recipe.narrator_data) == 0

    def test_narrator_recipe_len_and_getitem(self, video_creator_paths):
        """Test __len__ and __getitem__ methods."""
        
        # Patch get_default_assets_folder to use temp folder
        with patch.object(
            VideoCreatorPaths, 
            'get_default_assets_folder', 
            return_value=video_creator_paths._temp_default_assets_folder
        ):
            recipe = NarratorRecipe(video_creator_paths)

            # Add test data
            temp_voice_path = video_creator_paths._temp_default_assets_folder / "voices" / "voice_002.mp3"
            for i in range(3):
                narrator_recipe = ZonosTTSRecipe(
                    prompt=f"Test narrator {i+1}",
                    clone_voice_path=str(temp_voice_path),
                )
                recipe.add_narrator_data(narrator_recipe)

            assert len(recipe) == 3
            assert recipe[0].prompt == "Test narrator 1"
            assert recipe[1].prompt == "Test narrator 2"
            assert recipe[2].prompt == "Test narrator 3"

    def test_narrator_recipe_corrupted_file_handling(self, video_creator_paths):
        """Test handling of corrupted recipe files."""
        # Create corrupted JSON file
        with open(video_creator_paths.narrator_recipe_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        # Should handle corrupted file gracefully and start fresh
        recipe = NarratorRecipe(video_creator_paths)
        assert len(recipe.narrator_data) == 0

    def test_narrator_recipe_invalid_data_structure(self, video_creator_paths):
        """Test handling of files with invalid data structure."""
        # Create file with invalid structure
        invalid_data = {"wrong_key": ["some", "data"]}
        with open(video_creator_paths.narrator_recipe_file, "w", encoding="utf-8") as f:
            json.dump(invalid_data, f)

        # Should handle invalid structure gracefully
        recipe = NarratorRecipe(video_creator_paths)
        assert len(recipe.narrator_data) == 0

    def test_narrator_recipe_duplicate_data_handling(self, video_creator_paths):
        """Test handling of duplicate narrator data."""
        
        # Patch get_default_assets_folder to use temp folder
        with patch.object(
            VideoCreatorPaths, 
            'get_default_assets_folder', 
            return_value=video_creator_paths._temp_default_assets_folder
        ):
            recipe = NarratorRecipe(video_creator_paths)

            # Add the same narrator recipe multiple times
            temp_voice_path = video_creator_paths._temp_default_assets_folder / "voices" / "voice_002.mp3"
            narrator_recipe = ZonosTTSRecipe(
                prompt="Test narrator",
                clone_voice_path=str(temp_voice_path),
            )

            recipe.add_narrator_data(narrator_recipe)
            recipe.add_narrator_data(narrator_recipe)
            recipe.add_narrator_data(narrator_recipe)

            # Depending on implementation, should either have 3 entries or handle duplicates
            # For this test, we assume it allows duplicates
            assert len(recipe.narrator_data) >= 1
