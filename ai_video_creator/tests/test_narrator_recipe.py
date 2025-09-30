"""
Unit tests for narrator_recipe module.
"""

import json
from pathlib import Path

from ai_video_creator.modules.narrator.narrator_recipe import (
    NarratorRecipe,
    NarratorRecipeDefaultSettings,
)
from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER
from ai_video_creator.generators import ZonosTTSRecipe


class TestNarratorRecipeDefaultSettings:
    """Test NarratorRecipeDefaultSettings class."""

    def test_default_narrator_voice(self):
        """Test default narrator voice setting."""
        assert (
            NarratorRecipeDefaultSettings.NARRATOR_VOICE
            == f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3"
        )


class TestNarratorRecipe:
    """Test NarratorRecipe class."""

    def test_narrator_recipe_initialization(self, tmp_path):
        """Test NarratorRecipe initialization with empty file."""
        recipe_path = tmp_path / "test_narrator_recipe.json"
        recipe = NarratorRecipe(recipe_path)

        assert recipe.recipe_path == recipe_path
        assert len(recipe.narrator_data) == 0

    def test_narrator_recipe_load_existing_file(self, tmp_path):
        """Test loading existing narrator recipe file."""
        recipe_path = tmp_path / "test_narrator_recipe.json"

        test_data = {
            "narrator_data": [
                {
                    "prompt": "Test narrator 1",
                    "clone_voice_path": f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                    "index": 1,
                },
                {
                    "prompt": "Test narrator 2",
                    "clone_voice_path": f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3",
                    "recipe_type": "ZonosTTSRecipeType",
                    "index": 2,
                },
            ]
        }

        with open(recipe_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        recipe = NarratorRecipe(recipe_path)

        assert len(recipe.narrator_data) == 2
        assert recipe.narrator_data[0].prompt == "Test narrator 1"
        assert recipe.narrator_data[1].prompt == "Test narrator 2"

    def test_narrator_recipe_add_data(self, tmp_path):
        """Test adding narrator data to recipe."""

        recipe_path = tmp_path / "test_narrator_recipe.json"
        recipe = NarratorRecipe(recipe_path)

        # Create a test narrator recipe
        narrator_recipe = ZonosTTSRecipe(
            prompt="Test narrator",
            clone_voice_path=f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3",
        )

        recipe.add_narrator_data(narrator_recipe)

        assert len(recipe.narrator_data) == 1
        assert recipe.narrator_data[0].prompt == "Test narrator"

    def test_narrator_recipe_save_and_load(self, tmp_path):
        """Test saving and loading narrator recipe."""

        recipe_path = tmp_path / "test_narrator_recipe.json"

        # Create and save recipe
        recipe1 = NarratorRecipe(recipe_path)
        narrator_recipe = ZonosTTSRecipe(
            prompt="Test narrator",
            clone_voice_path=f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3",
        )

        recipe1.add_narrator_data(narrator_recipe)

        # Load recipe in new instance
        recipe2 = NarratorRecipe(recipe_path)

        assert len(recipe2.narrator_data) == 1
        assert recipe2.narrator_data[0].prompt == "Test narrator"

    def test_narrator_recipe_clean(self, tmp_path):
        """Test cleaning narrator recipe data."""

        recipe_path = tmp_path / "test_narrator_recipe.json"
        recipe = NarratorRecipe(recipe_path)

        # Add some data
        narrator_recipe = ZonosTTSRecipe(
            prompt="Test narrator",
            clone_voice_path=f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3",
        )

        recipe.add_narrator_data(narrator_recipe)
        assert len(recipe.narrator_data) == 1

        # Clean and verify
        recipe.clean()
        assert len(recipe.narrator_data) == 0

    def test_narrator_recipe_len_and_getitem(self, tmp_path):
        """Test __len__ and __getitem__ methods."""

        recipe_path = tmp_path / "test_narrator_recipe.json"
        recipe = NarratorRecipe(recipe_path)

        # Add test data
        for i in range(3):
            narrator_recipe = ZonosTTSRecipe(
                prompt=f"Test narrator {i+1}",
                clone_voice_path=f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3",
            )
            recipe.add_narrator_data(narrator_recipe)

        assert len(recipe) == 3
        assert recipe[0].prompt == "Test narrator 1"
        assert recipe[1].prompt == "Test narrator 2"
        assert recipe[2].prompt == "Test narrator 3"

    def test_narrator_recipe_corrupted_file_handling(self, tmp_path):
        """Test handling of corrupted recipe files."""
        recipe_path = tmp_path / "test_narrator_recipe.json"

        # Create corrupted JSON file
        with open(recipe_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        # Should handle corrupted file gracefully and start fresh
        recipe = NarratorRecipe(recipe_path)
        assert len(recipe.narrator_data) == 0

    def test_narrator_recipe_invalid_data_structure(self, tmp_path):
        """Test handling of files with invalid data structure."""
        recipe_path = tmp_path / "test_narrator_recipe.json"

        # Create file with invalid structure
        invalid_data = {"wrong_key": ["some", "data"]}
        with open(recipe_path, "w", encoding="utf-8") as f:
            json.dump(invalid_data, f)

        # Should handle invalid structure gracefully
        recipe = NarratorRecipe(recipe_path)
        assert len(recipe.narrator_data) == 0

    def test_narrator_recipe_duplicate_data_handling(self, tmp_path):
        """Test handling of duplicate narrator data."""

        recipe_path = tmp_path / "test_narrator_recipe.json"
        recipe = NarratorRecipe(recipe_path)

        # Add the same narrator recipe multiple times
        narrator_recipe = ZonosTTSRecipe(
            prompt="Test narrator",
            clone_voice_path=f"{DEFAULT_ASSETS_FOLDER}/voices/voice_002.mp3",
        )

        recipe.add_narrator_data(narrator_recipe)
        recipe.add_narrator_data(narrator_recipe)
        recipe.add_narrator_data(narrator_recipe)

        # Should allow duplicates (this might be intentional behavior)
        assert len(recipe.narrator_data) == 3
        assert all(item.prompt == "Test narrator" for item in recipe.narrator_data)
