"""
Narrator asset builder for creating narrator assets from recipes.
"""

from logging_utils import logger
from ct_video_creator.generators import IAudioGenerator
from ct_video_creator.utils import VideoCreatorPaths

from .narrator_assets import NarratorAssets
from .narrator_recipe import NarratorRecipe


class NarratorAssetManager:
    """Class to build narrator assets from recipes."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize NarratorAssetBuilder with story folder and chapter index."""
        self._paths = video_creator_paths
        story_folder = self._paths.story_folder

        logger.info(
            f"Initializing NarratorAssetBuilder for story: {story_folder.name}, chapter: {self._paths.chapter_index + 1}"
        )

        self.story_folder = story_folder
        self.chapter_index = self._paths.chapter_index
        self.output_file_prefix = f"chapter_{self.chapter_index+1:03}"

        # Create paths for separate narrator files
        self.narrator_recipe_file = self._paths.narrator_recipe_file
        self.narrator_asset_file = self._paths.narrator_asset_file

        self.recipe = NarratorRecipe(video_creator_paths)
        self.narrator_assets = NarratorAssets(video_creator_paths)

        # Ensure narrator_assets list has the same size as recipe
        self._synchronize_assets_with_recipe()

        logger.debug(f"NarratorAssetBuilder initialized with {len(self.recipe.narrator_data)} scenes")

    def _synchronize_assets_with_recipe(self):
        """Ensure narrator_assets list has the same size as recipe."""
        recipe_size = len(self.recipe.narrator_data)
        logger.debug(f"Synchronizing narrator assets with recipe - target size: {recipe_size}")

        # Extend or truncate narrator_list to match recipe size
        while len(self.narrator_assets.narrator_assets) < recipe_size:
            self.narrator_assets.narrator_assets.append(None)
        self.narrator_assets.narrator_assets = self.narrator_assets.narrator_assets[:recipe_size]

        logger.debug(
            f"Narrator asset synchronization completed - narrator assets: {len(self.narrator_assets.narrator_assets)}"
        )

    def generate_narrator_asset(self, scene_index: int):
        """Generate narrator asset for a scene."""
        try:
            logger.info(f"Generating narrator asset for scene {scene_index + 1}")
            audio = self.recipe.narrator_data[scene_index]
            audio_generator: IAudioGenerator = audio.GENERATOR_TYPE()
            output_audio_file_path = (
                self._paths.narrator_asset_folder / f"{self.output_file_prefix}_narrator_{scene_index+1:03}.mp3"
            )
            logger.debug(
                f"Using audio generator: {type(audio_generator).__name__} for file: {output_audio_file_path.name}"
            )

            output_audio = audio_generator.clone_text_to_speech(
                recipe=audio,
                output_file_path=output_audio_file_path,
            )

            self.narrator_assets.set_scene_narrator(scene_index, output_audio)
            self.narrator_assets.save_assets_to_file()
            logger.info(f"Successfully generated narrator for scene {scene_index + 1}: {output_audio.name}")

        except (IOError, OSError, RuntimeError) as e:
            logger.error(f"Failed to generate narrator for scene {scene_index + 1}: {e}")

    def generate_narrator_assets(self):
        """Generate all missing narrator assets from the recipe."""

        logger.info("Starting narrator asset generation process")

        missing = self.narrator_assets.get_missing_narrator_assets()

        logger.info(f"Found {len(missing)} scenes missing narrator assets")

        for scene_index in missing:
            logger.info(f"Processing narrator for scene {scene_index + 1}...")
            self.generate_narrator_asset(scene_index)

        logger.info("Narrator asset generation process completed successfully")