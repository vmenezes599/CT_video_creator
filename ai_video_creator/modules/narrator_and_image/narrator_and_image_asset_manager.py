"""This module manages the creation of video assets for a given story chapter."""

import json
from pathlib import Path

from logging_utils import begin_file_logging, logger
from ai_video_creator.generators import IAudioGenerator, IImageGenerator
from ai_video_creator.utils import VideoCreatorPaths

from .narrator_and_image_assets import NarratorAndImageAssets
from .narrator_and_image_recipe import NarratorAndImageRecipe


class NarratorAndImageAssetManager:
    """Class to manage video assets creation."""

    def __init__(self, story_folder: Path, chapter_index: int):
        """Initialize VideoAssetManager with story folder and chapter index."""

        logger.info(
            f"Initializing VideoAssetManager for story: {story_folder.name}, chapter: {chapter_index + 1}"
        )

        self.story_folder = story_folder
        self.chapter_index = chapter_index
        self.output_file_prefix = f"chapter_{self.chapter_index+1:03}"

        self.__paths = VideoCreatorPaths(story_folder, chapter_index)
        self.recipe = NarratorAndImageRecipe(
            self.__paths.narrator_and_image_recipe_file
        )
        self.video_assets = NarratorAndImageAssets(
            self.__paths.narrator_and_image_asset_file
        )

        # Ensure video_assets lists have the same size as recipe
        self._synchronize_assets_with_recipe()

        logger.debug(
            f"VideoAssetManager initialized with {len(self.recipe.narrator_data)} scenes"
        )

    def _synchronize_assets_with_recipe(self):
        """Ensure video_assets lists have the same size as recipe."""
        recipe_size = len(self.recipe.image_data)
        logger.debug(f"Synchronizing assets with recipe - target size: {recipe_size}")

        # Extend or truncate narrator_list to match recipe size
        while len(self.video_assets.narrator_assets) < recipe_size:
            self.video_assets.narrator_assets.append(None)
        self.video_assets.narrator_assets = self.video_assets.narrator_assets[
            :recipe_size
        ]

        # Extend or truncate image_list to match recipe size
        while len(self.video_assets.image_assets) < recipe_size:
            self.video_assets.image_assets.append(None)
        self.video_assets.image_assets = self.video_assets.image_assets[:recipe_size]

        logger.debug(
            f"Asset synchronization completed - narrator assets: {len(self.video_assets.narrator_assets)}, image assets: {len(self.video_assets.image_assets)}"
        )

    def _generate_scene_assets(self, scene_index: int):
        """Generate assets for a specific scene."""
        logger.debug(f"Generating assets for scene {scene_index + 1}")

        # Generate narrator if missing
        if not self.video_assets.has_narrator(scene_index):
            logger.debug(f"Scene {scene_index + 1} missing narrator - generating")
            self._generate_narrator_asset(scene_index)
        else:
            logger.debug(f"Scene {scene_index + 1} already has narrator - skipping")

        # Generate image if missing
        if not self.video_assets.has_image(scene_index):
            logger.debug(f"Scene {scene_index + 1} missing image - generating")
            self._generate_image_asset(scene_index)
        else:
            logger.debug(f"Scene {scene_index + 1} already has image - skipping")

        logger.info(f"Scene {scene_index + 1} asset generation completed")

    def _generate_narrator_asset(self, scene_index: int):
        """Generate narrator asset for a scene."""
        try:
            logger.info(f"Generating narrator asset for scene {scene_index + 1}")
            audio = self.recipe.narrator_data[scene_index]
            audio_generator: IAudioGenerator = audio.GENERATOR()
            output_audio_file_path = (
                self.__paths.narrator_and_image_asset_folder
                / f"{self.output_file_prefix}_narrator_{scene_index+1:03}.mp3"
            )
            logger.debug(
                f"Using audio generator: {type(audio_generator).__name__} for file: {output_audio_file_path.name}"
            )

            output_audio = audio_generator.clone_text_to_speech(
                recipe=audio,
                output_file_path=output_audio_file_path,
            )

            self.video_assets.set_scene_narrator(scene_index, output_audio)
            self.video_assets.save_assets_to_file()  # Save progress immediately
            logger.info(
                f"Successfully generated narrator for scene {scene_index + 1}: {output_audio.name}"
            )

        except (IOError, OSError, RuntimeError) as e:
            logger.error(
                f"Failed to generate narrator for scene {scene_index + 1}: {e}"
            )

    def _generate_image_asset(self, scene_index: int):
        """Generate image asset for a scene."""
        try:
            logger.info(f"Generating image asset for scene {scene_index + 1}")
            image = self.recipe.image_data[scene_index]
            image_generator: IImageGenerator = image.GENERATOR()
            output_image_file_path = (
                self.__paths.narrator_and_image_asset_folder
                / f"{self.output_file_prefix}_image_{scene_index+1:03}.png"
            )
            logger.debug(
                f"Using image generator: {type(image_generator).__name__} for file: {output_image_file_path.name}"
            )

            output_images = image_generator.text_to_image(
                recipe=image, output_file_path=output_image_file_path
            )
            first_output_image = output_images[0]
            self.video_assets.set_scene_image(scene_index, first_output_image)
            self.video_assets.save_assets_to_file()  # Save progress immediately
            for img in output_images:
                logger.info(
                    f"Successfully generated image for scene {scene_index + 1}: {img.name}"
                )
            logger.info(
                f"Using generated image for scene {scene_index + 1}: {first_output_image.name}"
            )

        except (IOError, OSError, RuntimeError) as e:
            logger.error(f"Failed to generate image for scene {scene_index + 1}: {e}")

    def generate_narrator_and_image_assets(self):
        """Generate all missing assets from the recipe."""
        with begin_file_logging(
            name="create_narrator_and_images_from_recipes",
            log_level="TRACE",
            base_folder=self.__paths.video_path,
        ):
            logger.info("Starting video asset generation process")

            missing = self.video_assets.get_missing_narrator_and_image_assets()
            all_missing_scenes = set(missing["narrator"] + missing["image"])

            logger.info(
                f"Found {len(missing['narrator'])} scenes missing narrator assets"
            )
            logger.info(f"Found {len(missing['image'])} scenes missing image assets")
            logger.info(f"Total scenes requiring processing: {len(all_missing_scenes)}")

            for scene_index in sorted(all_missing_scenes):
                logger.info(f"Processing scene {scene_index + 1}...")
                self._generate_scene_assets(scene_index)

            logger.info("Video asset generation process completed successfully")

    def clean_unused_assets(self):
        """Clean up video assets for a specific story folder."""

        logger.info("Starting video asset cleanup process")

        # Get list of valid (non-None) asset files to keep
        valid_narrator_assets = [
            asset for asset in self.video_assets.narrator_assets if asset is not None
        ]
        valid_image_assets = [
            asset for asset in self.video_assets.image_assets if asset is not None
        ]
        assets_to_keep = set(valid_narrator_assets + valid_image_assets)

        for file in self.__paths.narrator_and_image_asset_folder.glob("*"):
            if file.is_file():
                if file in assets_to_keep:
                    continue
                file.unlink()
                logger.info(f"Deleted asset file: {file}")

        logger.info("Video asset cleanup process completed successfully")
