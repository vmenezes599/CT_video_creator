"""
Background music asset manager for creating background music assets from recipes.
"""

from logging_utils import logger
from ai_video_creator.generators import IAudioGenerator
from ai_video_creator.utils import VideoCreatorPaths

from .background_music_assets import BackgroundMusicAssets
from .background_music_recipe import BackgroundMusicRecipe


class BackgroundMusicAssetManager:
    """Class to build background music assets from recipes."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize BackgroundMusicAssetManager with story folder and chapter index."""
        self._paths = video_creator_paths
        story_folder = self._paths.story_folder

        logger.info(
            f"Initializing BackgroundMusicAssetManager for story: {story_folder.name}, chapter: {self._paths.chapter_index + 1}"
        )

        self.story_folder = story_folder
        self.chapter_index = self._paths.chapter_index
        self.output_file_prefix = f"chapter_{self.chapter_index+1:03}"

        # Create paths for background music files
        self.background_music_recipe_file = self._paths.background_music_recipe_file
        self.background_music_asset_file = self._paths.background_music_asset_file

        self.recipe = BackgroundMusicRecipe(video_creator_paths)
        self.background_music_assets = BackgroundMusicAssets(video_creator_paths)

        # Ensure background_music_assets list has the same size as recipe
        self._synchronize_assets_with_recipe()

        logger.debug(f"BackgroundMusicAssetManager initialized with {len(self.recipe.music_recipes)} scenes")

    def _synchronize_assets_with_recipe(self):
        """Ensure background_music_assets list has the same size as recipe."""
        recipe_size = len(self.recipe.music_recipes)
        logger.debug(f"Synchronizing background music assets with recipe - target size: {recipe_size}")

        # Extend or truncate background_music_assets to match recipe size
        while len(self.background_music_assets.background_music_assets) < recipe_size:
            self.background_music_assets.background_music_assets.append(None)
        self.background_music_assets.background_music_assets = self.background_music_assets.background_music_assets[
            :recipe_size
        ]

        logger.debug(
            f"Background music asset synchronization completed - music assets: {len(self.background_music_assets.background_music_assets)}"
        )

    def generate_background_music_asset(self, scene_index: int):
        """Generate background music asset for a scene."""
        try:
            logger.info(f"Generating background music asset for scene {scene_index + 1}")
            music_info = self.recipe.music_recipes[scene_index]
            audio_generator: IAudioGenerator = music_info.get("generator_type", IAudioGenerator)()
            output_audio_file_path = (
                self._paths.background_music_asset_folder / f"{self.output_file_prefix}_bgmusic_{scene_index+1:03}.mp3"
            )
            logger.debug(
                f"Using audio generator: {type(audio_generator).__name__} for file: {output_audio_file_path.name}"
            )

            output_audio = audio_generator.generate_music(
                music_info=music_info,
                output_file_path=output_audio_file_path,
            )

            self.background_music_assets.background_music_assets[scene_index] = output_audio
            self.background_music_assets.save_assets_to_file()
            logger.info(f"Successfully generated background music for scene {scene_index + 1}: {output_audio.name}")

        except (IOError, OSError, RuntimeError) as e:
            logger.error(f"Failed to generate background music for scene {scene_index + 1}: {e}")

    def generate_background_music_assets(self):
        """Generate all missing background music assets from the recipe."""

        logger.info("Starting background music asset generation process")

        missing = self.background_music_assets.get_missing_background_music()

        logger.info(f"Found {len(missing)} scenes missing background music assets")

        for scene_index in missing:
            logger.info(f"Processing background music for scene {scene_index + 1}...")
            self.generate_background_music_asset(scene_index)

        logger.info("Background music asset generation process completed successfully")

    def clean_unused_background_music_assets(self):
        """Clean up background music assets for a specific story folder."""

        logger.info("Starting background music asset cleanup process")

        # Get list of valid (non-None) asset files to keep
        valid_background_music_assets = [
            asset for asset in self.background_music_assets.background_music_assets if asset is not None
        ]
        assets_to_keep = set(valid_background_music_assets)

        for file in self._paths.background_music_asset_folder.glob("*bgmusic*"):
            if file.is_file():
                if file in assets_to_keep:
                    continue
                file.unlink()
                logger.info(f"Deleted background music asset file: {file}")

        logger.info("Background music asset cleanup process completed successfully")
