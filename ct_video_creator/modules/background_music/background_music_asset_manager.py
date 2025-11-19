"""
Background music asset manager for creating background music assets from recipes.
"""

from ct_logging import logger
from ct_video_creator.generators import IBackgroundMusicGenerator
from ct_video_creator.utils import VideoCreatorPaths

from .background_music_assets import BackgroundMusicAssets, BackgroundMusicAsset
from .background_music_recipe import BackgroundMusicRecipe


class BackgroundMusicAssetManager:
    """Class to build background music assets from recipes."""

    DEFAULT_BACKGROUND_MUSIC_VOLUME = 0.3
    DEFAULT_SKIP_MUSIC = False

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
        self.background_music_assets.save_assets_to_file()

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

    def generate_background_music_asset(self, scene_index: int):
        """Generate background music asset for a scene."""
        try:
            recipe = self.recipe.music_recipes[scene_index]
            previous_recipe = self.recipe.music_recipes[scene_index - 1] if scene_index > 0 else None
            if recipe != previous_recipe:
                audio_generator: IBackgroundMusicGenerator = recipe.GENERATOR_TYPE()
                output_folder = self._paths.background_music_asset_folder
                logger.debug(f"Using audio generator: {type(audio_generator).__name__}")

                output_audio = audio_generator.text_to_music(recipe=recipe, output_folder=output_folder)

                self.background_music_assets.background_music_assets[scene_index] = BackgroundMusicAsset(
                    asset=output_audio, volume=self.DEFAULT_BACKGROUND_MUSIC_VOLUME, skip=self.DEFAULT_SKIP_MUSIC
                )
                self.background_music_assets.save_assets_to_file()
                logger.info(f"Successfully generated background music for scene {scene_index + 1}: {output_audio.name}")
            else:
                self.background_music_assets.background_music_assets[scene_index] = (
                    self.background_music_assets.background_music_assets[scene_index - 1]
                )
                self.background_music_assets.save_assets_to_file()
                logger.info(f"Using existing background music asset for scene {scene_index + 1} as recipe is unchanged")

        except (IOError, OSError, RuntimeError) as e:
            logger.error(f"Failed to generate background music for scene {scene_index + 1}: {e}")

    def generate_background_music_assets(self):
        """Generate all missing background music assets from the recipe."""

        logger.info("Starting background music asset generation process")

        missing = self.background_music_assets.get_missing_background_music()

        logger.info(f"Found {len(missing)} scenes missing background music assets")

        for scene_index in missing:
            self.generate_background_music_asset(scene_index)

        logger.info("Background music asset generation process completed successfully")
