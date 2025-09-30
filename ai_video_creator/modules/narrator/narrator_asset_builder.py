"""
Narrator asset builder for creating narrator assets from recipes.
"""

from pathlib import Path

from logging_utils import begin_file_logging, logger
from ai_video_creator.generators import IAudioGenerator
from ai_video_creator.utils import VideoCreatorPaths

from .narrator_assets import NarratorAssets
from .narrator_recipe import NarratorRecipe


class NarratorAssetBuilder:
    """Class to build narrator assets from recipes."""

    def __init__(self, story_folder: Path, chapter_index: int):
        """Initialize NarratorAssetBuilder with story folder and chapter index."""

        logger.info(
            f"Initializing NarratorAssetBuilder for story: {story_folder.name}, chapter: {chapter_index + 1}"
        )

        self.story_folder = story_folder
        self.chapter_index = chapter_index
        self.output_file_prefix = f"chapter_{self.chapter_index+1:03}"

        self.__paths = VideoCreatorPaths(story_folder, chapter_index)

        # Create paths for separate narrator files
        self.narrator_recipe_file = self.__paths.narrator_recipe_file
        self.narrator_asset_file = self.__paths.narrator_asset_file

        self.recipe = NarratorRecipe(self.narrator_recipe_file)
        self.narrator_assets = NarratorAssets(self.narrator_asset_file)

        # Ensure narrator_assets list has the same size as recipe
        self._synchronize_assets_with_recipe()

        logger.debug(
            f"NarratorAssetBuilder initialized with {len(self.recipe.narrator_data)} scenes"
        )

    def _synchronize_assets_with_recipe(self):
        """Ensure narrator_assets list has the same size as recipe."""
        recipe_size = len(self.recipe.narrator_data)
        logger.debug(
            f"Synchronizing narrator assets with recipe - target size: {recipe_size}"
        )

        # Extend or truncate narrator_list to match recipe size
        while len(self.narrator_assets.narrator_assets) < recipe_size:
            self.narrator_assets.narrator_assets.append(None)
        self.narrator_assets.narrator_assets = self.narrator_assets.narrator_assets[
            :recipe_size
        ]

        logger.debug(
            f"Narrator asset synchronization completed - narrator assets: {len(self.narrator_assets.narrator_assets)}"
        )

    def generate_narrator_asset(self, scene_index: int):
        """Generate narrator asset for a scene."""
        try:
            logger.info(f"Generating narrator asset for scene {scene_index + 1}")
            audio = self.recipe.narrator_data[scene_index]
            audio_generator: IAudioGenerator = audio.GENERATOR()
            output_audio_file_path = (
                self.__paths.narrator_asset_folder
                / f"{self.output_file_prefix}_narrator_{scene_index+1:03}.mp3"
            )
            logger.debug(
                f"Using audio generator: {type(audio_generator).__name__} for file: {output_audio_file_path.name}"
            )

            output_audio = audio_generator.clone_text_to_speech(
                recipe=audio,
                output_file_path=output_audio_file_path,
            )

            self.narrator_assets.set_scene_narrator(scene_index, output_audio)
            self.narrator_assets.save_assets_to_file()  # Save progress immediately
            logger.info(
                f"Successfully generated narrator for scene {scene_index + 1}: {output_audio.name}"
            )

        except (IOError, OSError, RuntimeError) as e:
            logger.error(
                f"Failed to generate narrator for scene {scene_index + 1}: {e}"
            )

    def generate_narrator_assets(self):
        """Generate all missing narrator assets from the recipe."""
        with begin_file_logging(
            name="create_narrator_assets_from_recipes",
            log_level="TRACE",
            base_folder=self.__paths.chapter_folder,
        ):
            logger.info("Starting narrator asset generation process")

            missing = self.narrator_assets.get_missing_narrator_assets()

            logger.info(f"Found {len(missing)} scenes missing narrator assets")

            for scene_index in missing:
                logger.info(f"Processing narrator for scene {scene_index + 1}...")
                self.generate_narrator_asset(scene_index)

            logger.info("Narrator asset generation process completed successfully")

    def clean_unused_narrator_assets(self):
        """Clean up narrator assets for a specific story folder."""

        logger.info("Starting narrator asset cleanup process")

        # Get list of valid (non-None) asset files to keep
        valid_narrator_assets = [
            asset for asset in self.narrator_assets.narrator_assets if asset is not None
        ]
        assets_to_keep = set(valid_narrator_assets)

        for file in self.__paths.narrator_asset_folder.glob("*narrator*"):
            if file.is_file():
                if file in assets_to_keep:
                    continue
                file.unlink()
                logger.info(f"Deleted narrator asset file: {file}")

        logger.info("Narrator asset cleanup process completed successfully")
