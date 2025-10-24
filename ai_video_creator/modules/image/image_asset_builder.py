"""
Image asset builder for creating image assets from recipes.
"""

from pathlib import Path

from logging_utils import logger
from ai_video_creator.generators import IImageGenerator
from ai_video_creator.utils import VideoCreatorPaths

from .image_assets import ImageAssets
from .image_recipe import ImageRecipe


class ImageAssetBuilder:
    """Class to build image assets from recipes."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize ImageAssetBuilder with story folder and chapter index."""
        self._paths = video_creator_paths
        story_folder = self._paths.story_folder

        logger.info(
            f"Initializing ImageAssetBuilder for story: {story_folder.name}, chapter: {self._paths.chapter_index + 1}"
        )

        self.story_folder = story_folder
        self.chapter_index = self._paths.chapter_index
        self.output_file_prefix = f"chapter_{self.chapter_index+1:03}"

        # Create paths for separate image files
        self.image_recipe_file = self._paths.image_recipe_file
        self.image_asset_file = self._paths.image_asset_file

        self.recipe = ImageRecipe(self.image_recipe_file)
        self.image_assets = ImageAssets(video_creator_paths)

        # Ensure image_assets list has the same size as recipe
        self._synchronize_assets_with_recipe()

        logger.debug(
            f"ImageAssetBuilder initialized with {len(self.recipe.image_data)} scenes"
        )

    def _synchronize_assets_with_recipe(self):
        """Ensure image_assets list has the same size as recipe."""
        recipe_size = len(self.recipe.image_data)
        logger.debug(
            f"Synchronizing image assets with recipe - target size: {recipe_size}"
        )

        # Extend or truncate image_list to match recipe size
        while len(self.image_assets.image_assets) < recipe_size:
            self.image_assets.image_assets.append(None)
        self.image_assets.image_assets = self.image_assets.image_assets[:recipe_size]

        logger.debug(
            f"Image asset synchronization completed - image assets: {len(self.image_assets.image_assets)}"
        )

    def generate_image_asset(self, scene_index: int):
        """Generate image asset for a scene."""
        try:
            logger.info(f"Generating image asset for scene {scene_index + 1}")
            image = self.recipe.image_data[scene_index]
            image_generator: IImageGenerator = image.GENERATOR_TYPE()
            output_image_file_path = (
                self._paths.image_asset_folder
                / f"{self.output_file_prefix}_image_{scene_index+1:03}.png"
            )
            logger.debug(
                f"Using image generator: {type(image_generator).__name__} for file: {output_image_file_path.name}"
            )

            output_image = image_generator.text_to_image(
                recipe=image, output_file_path=output_image_file_path
            )
            self.image_assets.set_scene_image(scene_index, output_image)
            self.image_assets.save_assets_to_file()  # Save progress immediately
            logger.info(
                f"Successfully generated {image.batch_size} image(s) for scene {scene_index + 1}."
            )

        except (IOError, OSError, RuntimeError) as e:
            logger.error(f"Failed to generate image for scene {scene_index + 1}: {e}")

    def generate_image_assets(self):
        """Generate all missing image assets from the recipe."""

        logger.info("Starting image asset generation process")

        missing = self.image_assets.get_missing_image_assets()

        logger.info(f"Found {len(missing)} scenes missing image assets")

        for scene_index in missing:
            logger.info(f"Processing image for scene {scene_index + 1}...")
            self.generate_image_asset(scene_index)

        logger.info("Image asset generation process completed successfully")

    def clean_unused_image_assets(self):
        """Clean up image assets for a specific story folder."""

        logger.info("Starting image asset cleanup process")

        # Get list of valid (non-None) asset files to keep
        valid_image_assets = [
            asset for asset in self.image_assets.image_assets if asset is not None
        ]
        assets_to_keep = set(valid_image_assets)

        for file in self._paths.image_asset_folder.glob("*image*"):
            if file.is_file():
                if file in assets_to_keep:
                    continue
                file.unlink()
                logger.info(f"Deleted image asset file: {file}")

        logger.info("Image asset cleanup process completed successfully")
