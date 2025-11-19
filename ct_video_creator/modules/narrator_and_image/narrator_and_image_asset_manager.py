"""This module manages the creation of video assets for a given story chapter."""

from logging_utils import logger
from ct_video_creator.utils import VideoCreatorPaths, AspectRatios

from ct_video_creator.modules.image import ImageAssetManager, ImageRecipeBuilder
from ct_video_creator.modules.narrator import (
    NarratorRecipeBuilder,
    NarratorAssetManager,
)


class NarratorAndImageAssetManager:
    """Class to manage video assets creation using separate narrator and image builders."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize VideoAssetManager with story folder and chapter index."""
        self._paths = video_creator_paths

        story_folder = self._paths.story_folder

        logger.info(
            f"Initializing VideoAssetManager for story: {story_folder.name}, chapter: {self._paths.chapter_index + 1}"
        )

        self.story_folder = story_folder
        self.chapter_index = self._paths.chapter_index
        self.output_file_prefix = f"chapter_{self.chapter_index+1:03}"

        # Initialize separate builders for narrator and image assets
        self.narrator_builder = NarratorAssetManager(video_creator_paths)
        self.image_builder = ImageAssetManager(video_creator_paths)

        logger.debug(
            f"VideoAssetManager initialized with narrator scenes: {len(self.narrator_builder.recipe.narrator_data)}, "
            f"image scenes: {len(self.image_builder.recipe.recipes_data)}"
        )

    def _generate_scene_assets(self, scene_index: int):
        """Generate assets for a specific scene."""
        logger.debug(f"Generating assets for scene {scene_index + 1}")

        # Generate image first if missing
        if not self.image_builder.image_assets.has_image(scene_index):
            logger.debug(f"Scene {scene_index + 1} missing image - generating")
            self.image_builder.generate_image_asset(scene_index)
        else:
            logger.debug(f"Scene {scene_index + 1} already has image - skipping")

        # Generate narrator after image if missing
        if not self.narrator_builder.narrator_assets.has_narrator(scene_index):
            logger.debug(f"Scene {scene_index + 1} missing narrator - generating")
            self.narrator_builder.generate_narrator_asset(scene_index)
        else:
            logger.debug(f"Scene {scene_index + 1} already has narrator - skipping")

        logger.info(f"Scene {scene_index + 1} asset generation completed")

    def generate_narrator_and_image_assets(self):
        """Generate all missing assets from the recipes in interleaved manner: image, then narrator for each scene."""

        logger.info("Starting video asset generation process (interleaved: image -> narrator per scene)")

        # Get missing assets from both builders
        missing_narrator = self.narrator_builder.narrator_assets.get_missing_narrator_assets()
        missing_image = self.image_builder.image_assets.get_missing_image_assets()
        all_missing_scenes = set(missing_narrator + missing_image)

        logger.info(f"Found {len(missing_narrator)} scenes missing narrator assets")
        logger.info(f"Found {len(missing_image)} scenes missing image assets")
        logger.info(f"Total scenes requiring processing: {len(all_missing_scenes)}")

        # Process scenes in order, generating image first, then narrator for each scene
        for scene_index in sorted(all_missing_scenes):
            logger.info(f"Processing scene {scene_index + 1} (image -> narrator)...")
            self._generate_scene_assets(scene_index)

        logger.info("Video asset generation process completed successfully")

    def create_narrator_and_image_recipes(self, aspect_ratio: AspectRatios):
        """Create both narrator and image recipes from prompts."""
        logger.info("Creating narrator and image recipes from prompts")

        narrator_recipe_builder = NarratorRecipeBuilder(self._paths)
        narrator_recipe_builder.create_narrator_recipes()

        # Create image recipes using image recipe builder
        image_recipe_builder = ImageRecipeBuilder(self._paths, aspect_ratio)
        image_recipe_builder.create_image_recipes()

        logger.info("Recipe creation completed successfully")
