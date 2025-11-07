"""
Unit tests for background_music_recipe module.
"""

import json
import pytest

from ai_video_creator.modules.background_music.background_music_recipe import (
    BackgroundMusicRecipe,
)
from ai_video_creator.generators import MusicGenRecipe
from ai_video_creator.utils import VideoCreatorPaths


class TestBackgroundMusicRecipe:
    """Test BackgroundMusicRecipe class."""

    def test_background_music_recipe_initialization(self, tmp_path):
        """Test BackgroundMusicRecipe initialization with empty file."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        recipe = BackgroundMusicRecipe(paths)

        assert recipe.recipe_path == paths.background_music_recipe_file
        assert len(recipe.music_recipes) == 0
        assert recipe.is_empty()

    def test_background_music_recipe_load_existing_file(self, tmp_path):
        """Test loading existing background music recipe file."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)

        test_data = {
            "music_recipes": [
                {
                    "index": 1,
                    "prompt": "Epic orchestral music",
                    "mood": "dramatic",
                    "seed": 12345,
                    "recipe_type": "MusicGenRecipeType",
                },
                {
                    "index": 2,
                    "prompt": "Calm ambient sounds",
                    "mood": "peaceful",
                    "seed": 67890,
                    "recipe_type": "MusicGenRecipeType",
                },
            ]
        }

        with open(paths.background_music_recipe_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        recipe = BackgroundMusicRecipe(paths)

        assert len(recipe.music_recipes) == 2
        assert recipe.music_recipes[0].prompt == "Epic orchestral music"
        assert recipe.music_recipes[0].mood == "dramatic"
        assert recipe.music_recipes[0].seed == 12345
        assert recipe.music_recipes[1].prompt == "Calm ambient sounds"
        assert recipe.music_recipes[1].mood == "peaceful"
        assert recipe.music_recipes[1].seed == 67890
        assert not recipe.is_empty()

    def test_background_music_recipe_add_data(self, tmp_path):
        """Test adding background music data to recipe."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        recipe = BackgroundMusicRecipe(paths)

        music_recipe = MusicGenRecipe(
            prompt="Adventure theme",
            mood="exciting",
            seed=11111,
        )

        recipe.add_music_recipe(music_recipe)

        assert len(recipe.music_recipes) == 1
        assert recipe.music_recipes[0].prompt == "Adventure theme"
        assert recipe.music_recipes[0].mood == "exciting"
        assert recipe.music_recipes[0].seed == 11111
        assert not recipe.is_empty()

    def test_background_music_recipe_save_and_load(self, tmp_path):
        """Test saving and loading background music recipe."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)

        # Create and save recipe
        recipe1 = BackgroundMusicRecipe(paths)
        music_recipe = MusicGenRecipe(
            prompt="Mystery music",
            mood="suspenseful",
            seed=99999,
        )

        recipe1.add_music_recipe(music_recipe)

        # Load new recipe instance
        recipe2 = BackgroundMusicRecipe(paths)

        # Verify data was loaded
        assert len(recipe2.music_recipes) == 1
        assert recipe2.music_recipes[0].prompt == "Mystery music"
        assert recipe2.music_recipes[0].mood == "suspenseful"
        assert recipe2.music_recipes[0].seed == 99999

    def test_background_music_recipe_clean(self, tmp_path):
        """Test cleaning background music recipe data."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        recipe = BackgroundMusicRecipe(paths)

        # Add some data
        music_recipe = MusicGenRecipe(
            prompt="Test music",
            mood="happy",
            seed=12345,
        )

        recipe.add_music_recipe(music_recipe)
        assert len(recipe.music_recipes) == 1
        assert not recipe.is_empty()

        # Clean the recipe
        recipe.clean()
        assert len(recipe.music_recipes) == 0
        assert recipe.is_empty()

    def test_background_music_recipe_to_dict(self, tmp_path):
        """Test converting recipe to dictionary."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        recipe = BackgroundMusicRecipe(paths)

        # Add test data
        for i in range(3):
            music_recipe = MusicGenRecipe(
                prompt=f"Test music {i+1}",
                mood=f"mood_{i+1}",
                seed=1000 + i,
            )
            recipe.add_music_recipe(music_recipe)

        recipe_dict = recipe.to_dict()

        assert "music_recipes" in recipe_dict
        assert len(recipe_dict["music_recipes"]) == 3

        # Check first recipe
        assert recipe_dict["music_recipes"][0]["index"] == 1
        assert recipe_dict["music_recipes"][0]["prompt"] == "Test music 1"
        assert recipe_dict["music_recipes"][0]["mood"] == "mood_1"
        assert recipe_dict["music_recipes"][0]["seed"] == 1000

    def test_background_music_recipe_corrupted_file_handling(self, tmp_path):
        """Test handling of corrupted recipe files."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)

        # Create corrupted JSON file
        with open(paths.background_music_recipe_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        # Should handle corrupted file gracefully and start fresh
        recipe = BackgroundMusicRecipe(paths)
        assert len(recipe.music_recipes) == 0
        assert recipe.is_empty()

        # Verify backup was created
        backup_file = paths.background_music_recipe_file.parent / (paths.background_music_recipe_file.name + ".old")
        assert backup_file.exists()

    def test_background_music_recipe_invalid_data_structure(self, tmp_path):
        """Test handling of files with invalid data structure."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)

        # Create file with invalid structure
        invalid_data = {"wrong_key": ["some", "data"]}
        with open(paths.background_music_recipe_file, "w", encoding="utf-8") as f:
            json.dump(invalid_data, f)

        # Should handle invalid structure gracefully
        recipe = BackgroundMusicRecipe(paths)
        assert len(recipe.music_recipes) == 0
        assert recipe.is_empty()

    def test_background_music_recipe_duplicate_data_handling(self, tmp_path):
        """Test handling of duplicate background music data."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        recipe = BackgroundMusicRecipe(paths)

        # Add the same music recipe multiple times
        music_recipe = MusicGenRecipe(
            prompt="Repeated music",
            mood="calm",
            seed=55555,
        )

        recipe.add_music_recipe(music_recipe)
        recipe.add_music_recipe(music_recipe)
        recipe.add_music_recipe(music_recipe)

        # Should allow duplicates
        assert len(recipe.music_recipes) == 3

    def test_background_music_recipe_missing_required_fields(self, tmp_path):
        """Test handling of recipe data with missing required fields."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)

        # Create file with missing required fields
        invalid_data = {
            "music_recipes": [
                {
                    "index": 1,
                    "prompt": "Missing fields",
                    # Missing mood, seed, recipe_type
                }
            ]
        }
        with open(paths.background_music_recipe_file, "w", encoding="utf-8") as f:
            json.dump(invalid_data, f)

        # Should handle missing fields gracefully
        recipe = BackgroundMusicRecipe(paths)
        assert len(recipe.music_recipes) == 0
        assert recipe.is_empty()

    def test_background_music_recipe_empty_list_initialization(self, tmp_path):
        """Test that recipe can handle empty initialization."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)

        # Create file with empty recipe list
        test_data = {"music_recipes": []}
        with open(paths.background_music_recipe_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        recipe = BackgroundMusicRecipe(paths)
        assert len(recipe.music_recipes) == 0
        assert recipe.is_empty()

    def test_background_music_recipe_multiple_add_operations(self, tmp_path):
        """Test adding multiple recipes sequentially."""
        paths = VideoCreatorPaths(tmp_path, "test_story", 0)
        recipe = BackgroundMusicRecipe(paths)

        # Add multiple different recipes
        moods = ["happy", "sad", "exciting", "calm"]
        for i, mood in enumerate(moods):
            music_recipe = MusicGenRecipe(
                prompt=f"Music for {mood} scene",
                mood=mood,
                seed=i * 1000,
            )
            recipe.add_music_recipe(music_recipe)

        assert len(recipe.music_recipes) == 4
        for i, mood in enumerate(moods):
            assert recipe.music_recipes[i].mood == mood
            assert recipe.music_recipes[i].seed == i * 1000


class TestMusicGenRecipe:
    """Test MusicGenRecipe class."""

    def test_music_gen_recipe_creation(self):
        """Test creating a MusicGenRecipe."""
        recipe = MusicGenRecipe(
            prompt="Epic battle music",
            mood="intense",
            seed=12345,
        )

        assert recipe.prompt == "Epic battle music"
        assert recipe.mood == "intense"
        assert recipe.seed == 12345
        assert recipe.recipe_type == "MusicGenRecipeType"

    def test_music_gen_recipe_auto_seed_generation(self):
        """Test that seed is auto-generated when not provided."""
        recipe1 = MusicGenRecipe(prompt="Test 1", mood="happy", seed=None)
        recipe2 = MusicGenRecipe(prompt="Test 2", mood="sad", seed=None)

        # Both should have seeds
        assert recipe1.seed is not None
        assert recipe2.seed is not None

        # Seeds should be different (very high probability)
        assert recipe1.seed != recipe2.seed

    def test_music_gen_recipe_equality(self):
        """Test equality comparison between MusicGenRecipe instances."""
        recipe1 = MusicGenRecipe(prompt="Test", mood="happy", seed=123)
        recipe2 = MusicGenRecipe(prompt="Test", mood="happy", seed=123)
        recipe3 = MusicGenRecipe(prompt="Test", mood="sad", seed=123)
        recipe4 = MusicGenRecipe(prompt="Different", mood="happy", seed=123)

        # Same values should be equal
        assert recipe1 == recipe2

        # Different mood should not be equal
        assert recipe1 != recipe3

        # Different prompt should not be equal
        assert recipe1 != recipe4

        # Different type should not be equal
        assert recipe1 != "not a recipe"

    def test_music_gen_recipe_to_dict(self):
        """Test converting MusicGenRecipe to dictionary."""
        recipe = MusicGenRecipe(
            prompt="Cinematic score",
            mood="dramatic",
            seed=99999,
        )

        recipe_dict = recipe.to_dict()

        assert recipe_dict["prompt"] == "Cinematic score"
        assert recipe_dict["mood"] == "dramatic"
        assert recipe_dict["seed"] == 99999
        assert recipe_dict["recipe_type"] == "MusicGenRecipeType"

    def test_music_gen_recipe_from_dict_valid(self):
        """Test creating MusicGenRecipe from valid dictionary."""
        data = {
            "prompt": "Adventure theme",
            "mood": "exciting",
            "seed": 54321,
            "recipe_type": "MusicGenRecipeType",
        }

        recipe = MusicGenRecipe.from_dict(data)

        assert recipe.prompt == "Adventure theme"
        assert recipe.mood == "exciting"
        assert recipe.seed == 54321
        assert recipe.recipe_type == "MusicGenRecipeType"

    def test_music_gen_recipe_from_dict_missing_fields(self):
        """Test that from_dict raises KeyError for missing fields."""
        # Missing mood
        data = {
            "prompt": "Test",
            "seed": 123,
            "recipe_type": "MusicGenRecipeType",
        }

        with pytest.raises(KeyError, match="Missing required key: mood"):
            MusicGenRecipe.from_dict(data)

    def test_music_gen_recipe_from_dict_invalid_types(self):
        """Test that from_dict raises ValueError for invalid types."""
        # Invalid prompt type
        data = {
            "prompt": 123,  # Should be string
            "mood": "happy",
            "seed": 123,
            "recipe_type": "MusicGenRecipeType",
        }

        with pytest.raises(ValueError, match="prompt must be a string"):
            MusicGenRecipe.from_dict(data)

    def test_music_gen_recipe_from_dict_invalid_recipe_type(self):
        """Test that from_dict raises ValueError for invalid recipe_type."""
        data = {
            "prompt": "Test",
            "mood": "happy",
            "seed": 123,
            "recipe_type": "WrongType",
        }

        with pytest.raises(ValueError, match="Invalid recipe_type: WrongType"):
            MusicGenRecipe.from_dict(data)

    def test_music_gen_recipe_roundtrip_serialization(self):
        """Test that to_dict and from_dict work correctly together."""
        original = MusicGenRecipe(
            prompt="Test music",
            mood="neutral",
            seed=77777,
        )

        # Convert to dict and back
        recipe_dict = original.to_dict()
        reconstructed = MusicGenRecipe.from_dict(recipe_dict)

        # Should be equal
        assert original == reconstructed
        assert original.prompt == reconstructed.prompt
        assert original.mood == reconstructed.mood
        assert original.seed == reconstructed.seed
