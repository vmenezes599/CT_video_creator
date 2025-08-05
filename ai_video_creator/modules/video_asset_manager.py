"""This module manages the creation of video assets for a given story chapter."""

import json
import shutil
from pathlib import Path

from logging_utils import begin_console_logging, logger
from ai_video_creator.generators import IAudioGenerator, IImageGenerator
from ai_video_creator.helpers.video_recipe_paths import VideoRecipePaths

from .video_recipe import VideoRecipe


class VideoAssets:
    """Class to manage video assets data and persistence only."""

    def __init__(self, asset_file_path: Path):
        """Initialize VideoAssets with file path and expected scene count."""
        self.asset_file_path = asset_file_path
        self.narrator_list: list[str] = []
        self.image_list: list[str] = []
        self.__load_assets_from_file()

    def __load_assets_from_file(self):
        """Load assets from the video asset file."""
        try:
            logger.debug(f"Loading video assets from: {self.asset_file_path.name}")
            with open(self.asset_file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                assets = data.get("assets", [])
                self.narrator_list = [asset.get("narrator", "") for asset in assets]
                self.image_list = [asset.get("image", "") for asset in assets]
            logger.info(
                f"Successfully loaded {len(self.narrator_list)} narrator assets and {len(self.image_list)} image assets"
            )
        except FileNotFoundError:
            logger.debug(
                f"Asset file not found: {self.asset_file_path.name} - starting with empty assets"
            )
            self.narrator_list = []
            self.image_list = []

    def save_assets_to_file(self) -> None:
        """Save the current state of the video assets to a file."""
        try:
            with open(self.asset_file_path, "w", encoding="utf-8") as file:
                assets = []
                for i, _ in enumerate(self.narrator_list):
                    narrator = (
                        self.narrator_list[i] if i < len(self.narrator_list) else ""
                    )
                    image = self.image_list[i] if i < len(self.image_list) else ""
                    assets.append({"narrator": narrator, "image": image})

                data = {"assets": assets}
                json.dump(data, file, indent=4)
            logger.trace(f"Assets saved with {len(assets)} scene assets")
        except IOError as e:
            logger.error(
                f"Error saving video assets to {self.asset_file_path.name}: {e}"
            )
            print(f"Error saving video assets: {e}")

    def _ensure_index_exists(self, scene_index: int) -> None:
        """Extend lists to ensure the scene_index exists."""
        # Extend narrator_list if needed
        while len(self.narrator_list) <= scene_index:
            self.narrator_list.append("")

        # Extend image_list if needed
        while len(self.image_list) <= scene_index:
            self.image_list.append("")

    def set_scene_narrator(self, scene_index: int, narrator_file_path: Path) -> None:
        """Set narrator file path for a specific scene."""
        self._ensure_index_exists(scene_index)
        self.narrator_list[scene_index] = str(narrator_file_path)
        logger.debug(f"Set narrator for scene {scene_index}: {narrator_file_path.name}")

    def set_scene_image(self, scene_index: int, image_file_path: Path) -> None:
        """Set image file path for a specific scene."""
        self._ensure_index_exists(scene_index)
        self.image_list[scene_index] = str(image_file_path)
        logger.debug(f"Set image for scene {scene_index}: {image_file_path.name}")

    def clear_scene_assets(self, scene_index: int) -> None:
        """Clear all assets for a specific scene."""
        self._ensure_index_exists(scene_index)
        self.narrator_list[scene_index] = ""
        self.image_list[scene_index] = ""
        logger.debug(f"Cleared all assets for scene {scene_index}")

    def has_narrator(self, scene_index: int) -> bool:
        """Check if a scene has narrator asset."""
        if scene_index < 0 or scene_index >= len(self.narrator_list):
            return False
        return bool(self.narrator_list[scene_index])

    def has_image(self, scene_index: int) -> bool:
        """Check if a scene has image asset."""
        if scene_index < 0 or scene_index >= len(self.image_list):
            return False
        return bool(self.image_list[scene_index])

    def get_missing_assets(self) -> dict:
        """Get a summary of missing assets per scene."""
        missing = {"narrator": [], "image": []}
        for i, narrator in enumerate(self.narrator_list):
            if not narrator:
                missing["narrator"].append(i)
        for i, image in enumerate(self.image_list):
            if not image:
                missing["image"].append(i)
        return missing

    def is_complete(self) -> bool:
        """Check if all assets are present for all scenes."""
        missing = self.get_missing_assets()
        return len(missing["narrator"]) == 0 and len(missing["image"]) == 0


class VideoAssetManager:
    """Class to manage video assets creation."""

    def __init__(self, story_folder: Path, chapter_index: int):
        """Initialize VideoAssetManager with story folder and chapter index."""
        logger.info(
            f"Initializing VideoAssetManager for story: {story_folder.name}, chapter: {chapter_index}"
        )

        self.story_folder = story_folder
        self.chapter_index = chapter_index
        self.output_file_prefix = f"chapter_{self.chapter_index+1:03}"

        # Initialize path management
        self.__paths = VideoRecipePaths(story_folder, chapter_index)

        self.recipe = VideoRecipe(self.__paths.recipe_file)
        self.video_assets = VideoAssets(self.__paths.video_asset_file)

        # Ensure video_assets lists have the same size as recipe
        self._synchronize_assets_with_recipe()

        logger.debug(
            f"VideoAssetManager initialized with {len(self.recipe.narrator_data)} scenes"
        )

    def _synchronize_assets_with_recipe(self):
        """Ensure video_assets lists have the same size as recipe."""
        recipe_size = len(self.recipe.narrator_data)
        logger.debug(f"Synchronizing assets with recipe - target size: {recipe_size}")

        # Extend or truncate narrator_list to match recipe size
        while len(self.video_assets.narrator_list) < recipe_size:
            self.video_assets.narrator_list.append("")
        self.video_assets.narrator_list = self.video_assets.narrator_list[:recipe_size]

        # Extend or truncate image_list to match recipe size
        while len(self.video_assets.image_list) < recipe_size:
            self.video_assets.image_list.append("")
        self.video_assets.image_list = self.video_assets.image_list[:recipe_size]

        logger.debug(
            f"Asset synchronization completed - narrator assets: {len(self.video_assets.narrator_list)}, image assets: {len(self.video_assets.image_list)}"
        )

    def _move_asset_to_database(self, asset_path: Path) -> Path:
        """Move asset to the database folder and return the new path."""
        if not asset_path.exists():
            logger.error(f"Asset file does not exist: {asset_path}")
            raise FileNotFoundError(f"Asset file does not exist: {asset_path}")

        target_path = self.__paths.assets_path / asset_path.name
        shutil.move(asset_path, target_path)
        logger.trace(f"Asset moved successfully to: {target_path}")
        return target_path

    def _generate_scene_assets(self, scene_index: int):
        """Generate assets for a specific scene."""
        logger.debug(f"Generating assets for scene {scene_index}")

        # Generate narrator if missing
        if not self.video_assets.has_narrator(scene_index):
            logger.debug(f"Scene {scene_index} missing narrator - generating")
            self._generate_narrator_asset(scene_index)
        else:
            logger.debug(f"Scene {scene_index} already has narrator - skipping")

        # Generate image if missing
        if not self.video_assets.has_image(scene_index):
            logger.debug(f"Scene {scene_index} missing image - generating")
            self._generate_image_asset(scene_index)
        else:
            logger.debug(f"Scene {scene_index} already has image - skipping")

        logger.info(f"Scene {scene_index} asset generation completed")

    def _generate_narrator_asset(self, scene_index: int):
        """Generate narrator asset for a scene."""
        try:
            logger.info(f"Generating narrator asset for scene {scene_index}")
            audio = self.recipe.narrator_data[scene_index]
            audio_generator: IAudioGenerator = audio.GENERATOR()
            output_audio_file_name = (
                f"{self.output_file_prefix}_narrator_{scene_index+1:03}"
            )
            logger.debug(
                f"Using audio generator: {type(audio_generator).__name__} for file: {output_audio_file_name}"
            )

            output_audio = audio_generator.clone_text_to_speech(
                recipe=audio,
                output_file_name=output_audio_file_name,
            )
            output_audio = self._move_asset_to_database(output_audio)

            self.video_assets.set_scene_narrator(scene_index, output_audio)
            self.video_assets.save_assets_to_file()  # Save progress immediately
            logger.info(
                f"Successfully generated narrator for scene {scene_index}: {output_audio.name}"
            )
            print(f"Generated narrator for scene {scene_index}")

        except (IOError, OSError, RuntimeError) as e:
            logger.error(f"Failed to generate narrator for scene {scene_index}: {e}")
            print(f"Failed to generate narrator for scene {scene_index}: {e}")

    def _generate_image_asset(self, scene_index: int):
        """Generate image asset for a scene."""
        try:
            logger.info(f"Generating image asset for scene {scene_index}")
            image = self.recipe.image_data[scene_index]
            image_generator: IImageGenerator = image.GENERATOR()
            output_image_file_name = (
                f"{self.output_file_prefix}_image_{scene_index+1:03}"
            )
            logger.debug(
                f"Using image generator: {type(image_generator).__name__} for file: {output_image_file_name}"
            )

            output_image = image_generator.text_to_image(
                recipe=image, output_file_name=output_image_file_name
            )
            output_image = self._move_asset_to_database(output_image)

            self.video_assets.set_scene_image(scene_index, output_image)
            self.video_assets.save_assets_to_file()  # Save progress immediately
            logger.info(
                f"Successfully generated image for scene {scene_index}: {output_image.name}"
            )
            print(f"Generated image for scene {scene_index}")

        except (IOError, OSError, RuntimeError) as e:
            logger.error(f"Failed to generate image for scene {scene_index}: {e}")
            print(f"Failed to generate image for scene {scene_index}: {e}")

    def regenerate_asset(self, scene_index: int):
        """Regenerate assets for a specific scene."""
        logger.info(f"Regenerating assets for scene {scene_index}")
        self.video_assets.clear_scene_assets(scene_index)
        self.video_assets.save_assets_to_file()
        self._generate_scene_assets(scene_index)
        logger.info(f"Asset regeneration completed for scene {scene_index}")

    def generate_recipe_output(self):
        """Generate all missing assets from the recipe."""
        with begin_console_logging(name="VideoAssetManager", log_level="TRACE"):
            logger.info("Starting video asset generation process")

            missing = self.video_assets.get_missing_assets()
            all_missing_scenes = set(missing["narrator"] + missing["image"])

            logger.info(
                f"Found {len(missing['narrator'])} scenes missing narrator assets"
            )
            logger.info(f"Found {len(missing['image'])} scenes missing image assets")
            logger.info(f"Total scenes requiring processing: {len(all_missing_scenes)}")

            for scene_index in sorted(all_missing_scenes):
                logger.info(f"Processing scene {scene_index}...")
                print(f"Processing scene {scene_index}...")
                self._generate_scene_assets(scene_index)

            logger.info("Video asset generation process completed successfully")
