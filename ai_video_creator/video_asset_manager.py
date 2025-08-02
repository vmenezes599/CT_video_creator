"""This module manages the creation of video assets for a given story chapter."""

import json
from pathlib import Path

from .video_recipe import VideoRecipe
from .video_recipe_paths import VideoRecipePaths

from .generators import (
    IAudioGenerator,
    IImageGenerator,
)

class VideoAssets:
    """Class to manage video assets data and persistence."""

    def __init__(self, asset_file_path: Path, recipe: VideoRecipe):
        """Initialize VideoAssets with file path and recipe."""
        self.asset_file_path = asset_file_path
        self.recipe = recipe
        self.assets = []
        self.__load_assets_from_file()

    def __load_assets_from_file(self):
        """Load assets from the video asset file."""
        try:
            with open(self.asset_file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.assets = data.get("assets", [])
        except FileNotFoundError:
            self.assets = [
                {"narrator": "", "image": ""} for _ in self.recipe.narrator_data
            ]
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading video recipe: {e}")
            self.assets = [
                {"narrator": "", "image": ""} for _ in self.recipe.narrator_data
            ]

    def save_assets_to_file(self) -> None:
        """Save the current state of the video assets to a file."""
        try:
            with open(self.asset_file_path, "w", encoding="utf-8") as file:
                json.dump({"assets": self.assets}, file, indent=4)
        except IOError as e:
            print(f"Error saving video assets: {e}")

    def add_scene_narrator(self, scene_index: int, narrator_file_path: Path) -> None:
        """Add narrator data for a specific scene."""
        if scene_index < 0 or scene_index >= len(self.assets):
            raise IndexError("Scene index out of range")
        self.assets[scene_index]["narrator"] = str(narrator_file_path)

    def add_scene_image(self, scene_index: int, image_file_path: Path) -> None:
        """Add image data for a specific scene."""
        if scene_index < 0 or scene_index >= len(self.assets):
            raise IndexError("Scene index out of range")
        self.assets[scene_index]["image"] = str(image_file_path)

    def regenerate_asset(self, scene_index: int) -> None:
        """Clear assets for a specific scene to allow regeneration."""
        if scene_index < 0 or scene_index >= len(self.assets):
            raise IndexError("Scene index out of range")
        
        # Remove existing assets
        self.assets[scene_index] = {"narrator": "", "image": ""}
        self.save_assets_to_file()

    def has_narrator(self, scene_index: int) -> bool:
        """Check if a scene has narrator asset."""
        if scene_index < 0 or scene_index >= len(self.assets):
            return False
        return bool(self.assets[scene_index]["narrator"])

    def has_image(self, scene_index: int) -> bool:
        """Check if a scene has image asset."""
        if scene_index < 0 or scene_index >= len(self.assets):
            return False
        return bool(self.assets[scene_index]["image"])

    def get_scene_count(self) -> int:
        """Get the total number of scenes."""
        return len(self.assets)
    

class VideoAssetManager:
    """Class to manage video assets creation."""

    def __init__(self, story_folder: Path, chapter_index: int):
        """Initialize VideoAssetCreator with story folder and chapter index."""
        self.story_folder = story_folder
        self.chapter_index = chapter_index
        self.output_file_prefix = f"chapter_{self.chapter_index:03}"

        # Initialize path management
        self.__paths = VideoRecipePaths.create_from_story_and_index(
            story_folder, chapter_index
        )

        self.recipe = VideoRecipe(self.__paths.recipe_file)
        self.video_assets = VideoAssets(self.__paths.video_asset_file, self.recipe)

    @property
    def assets(self):
        """Backward compatibility property to access video assets."""
        return self.video_assets.assets

    def regenerate_asset(self, scene_index: int) -> None:
        """Regenerate assets for a specific scene."""
        self.video_assets.regenerate_asset(scene_index)
        # Generate new assets
        self.generate_recipe_output()

    def generate_recipe_output(self):
        """Generate audio and image outputs from the recipe."""

        for index, (audio, image) in enumerate(
            zip(self.recipe.narrator_data, self.recipe.image_data)
        ):
            if not self.video_assets.has_narrator(index):
                audio_generator: IAudioGenerator = audio.GENERATOR()
                output_audio_file_name = (
                    f"{self.output_file_prefix}_narrator_{index+1:03}"
                )
                output_audio = audio_generator.clone_text_to_speech(
                    recipe=audio,
                    output_file_name=output_audio_file_name,
                )
                self.video_assets.add_scene_narrator(index, output_audio)
                self.video_assets.save_assets_to_file()

            if not self.video_assets.has_image(index):
                image_generator: IImageGenerator = image.GENERATOR()
                output_image_file_name = f"{self.output_file_prefix}_image_{index+1:03}"
                output_image = image_generator.text_to_image(
                    recipe=image, output_file_name=output_image_file_name
                )
                self.video_assets.add_scene_image(index, output_image)
                self.video_assets.save_assets_to_file()
