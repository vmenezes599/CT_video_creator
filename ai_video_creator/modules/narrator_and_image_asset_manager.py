"""This module manages the creation of video assets for a given story chapter."""

import json
from pathlib import Path

from logging_utils import begin_file_logging, logger
from ai_video_creator.generators import IAudioGenerator, IImageGenerator
from ai_video_creator.utils.video_creator_paths import VideoCreatorPaths

from .narrator_and_image_recipe import NarratorAndImageRecipeFile


class NarratorAndImageAssetsFile:
    """Class to manage video assets data and persistence only."""

    def __init__(self, asset_file_path: Path):
        """Initialize NarratorAndImageAssets with file path and expected scene count."""
        self.asset_file_path = asset_file_path
        self.narrator_assets: list[Path] = []
        self.image_assets: list[Path] = []
        self._load_assets_from_file()

    def _load_assets_from_file(self):
        """Load assets from JSON file."""
        try:
            logger.debug(f"Loading video assets from: {self.asset_file_path.name}")
            with open(self.asset_file_path, "r", encoding="utf-8") as file:
                data: dict = json.load(file)

                assets = data.get("assets", [])
                self._ensure_index_exists(len(assets) - 1)

                # Load assets from the "assets" array format
                for index, asset in enumerate(assets):
                    # Load narrator asset, skip None/empty values
                    narrator_value = asset.get("narrator")
                    if narrator_value is not None and narrator_value != "":
                        self.narrator_assets[index] = Path(narrator_value)

                    # Load image asset, skip None/empty values
                    image_value = asset.get("image")
                    if image_value is not None and image_value != "":
                        self.image_assets[index] = Path(image_value)

                self.save_assets_to_file()

        except json.JSONDecodeError:
            logger.error(
                f"Error decoding JSON from {self.asset_file_path.name} - renaming to .old and starting with empty assets"
            )
            # Rename corrupted file to .old for backup
            old_file_path = Path(str(self.asset_file_path) + ".old")
            if self.asset_file_path.exists():
                self.asset_file_path.rename(old_file_path)
            self.narrator_assets = []
            self.image_assets = []
            # Create a new empty file
            self.save_assets_to_file()

        except FileNotFoundError:
            logger.debug(
                f"Asset file not found: {self.asset_file_path.name} - starting with empty assets"
            )
            self.narrator_assets = []
            self.image_assets = []

    def save_assets_to_file(self) -> None:
        """Save the current state of the video assets to a file."""
        try:
            with open(self.asset_file_path, "w", encoding="utf-8") as file:
                assets = []
                for i, _ in enumerate(self.narrator_assets):
                    narrator = (
                        str(self.narrator_assets[i])
                        if i < len(self.narrator_assets)
                        and self.narrator_assets[i] is not None
                        else ""
                    )
                    image = (
                        str(self.image_assets[i])
                        if i < len(self.image_assets)
                        and self.image_assets[i] is not None
                        else ""
                    )
                    assets.append(
                        {"index": i + 1, "narrator": narrator, "image": image}
                    )

                data = {"assets": assets}
                json.dump(data, file, indent=4)
            logger.trace(f"Assets saved with {len(assets)} scene assets")
        except IOError as e:
            logger.error(
                f"Error saving video assets to {self.asset_file_path.name}: {e}"
            )

    def _ensure_index_exists(self, scene_index: int) -> None:
        """Extend lists to ensure the scene_index exists."""
        # Extend narrator_list if needed
        while len(self.narrator_assets) <= scene_index:
            self.narrator_assets.append(None)

        # Extend image_list if needed
        while len(self.image_assets) <= scene_index:
            self.image_assets.append(None)

    def set_scene_narrator(self, scene_index: int, narrator_file_path: Path) -> None:
        """Set narrator file path for a specific scene."""
        self._ensure_index_exists(scene_index)
        self.narrator_assets[scene_index] = narrator_file_path
        logger.debug(f"Set narrator for scene {scene_index}: {narrator_file_path.name}")

    def set_scene_image(self, scene_index: int, image_file_path: Path) -> None:
        """Set image file path for a specific scene."""
        self._ensure_index_exists(scene_index)
        self.image_assets[scene_index] = image_file_path
        logger.debug(f"Set image for scene {scene_index}: {image_file_path.name}")

    def clear_scene_assets(self, scene_index: int) -> None:
        """Clear all assets for a specific scene."""
        self._ensure_index_exists(scene_index)
        self.narrator_assets[scene_index] = None
        self.image_assets[scene_index] = None
        logger.debug(f"Cleared all assets for scene {scene_index}")

    def has_narrator(self, scene_index: int) -> bool:
        """Check if a scene has narrator asset."""
        if scene_index < 0 or scene_index >= len(self.narrator_assets):
            return False
        narrator = self.narrator_assets[scene_index]
        return narrator is not None and narrator.exists() and narrator.is_file()

    def has_image(self, scene_index: int) -> bool:
        """Check if a scene has image asset."""
        if scene_index < 0 or scene_index >= len(self.image_assets):
            return False
        image = self.image_assets[scene_index]
        return image is not None and image.exists() and image.is_file()

    def get_missing_narrator_and_image_assets(self) -> dict:
        """Get a summary of missing assets per scene."""
        missing = {"narrator": [], "image": []}
        for i, _ in enumerate(self.narrator_assets):
            if not self.has_narrator(i):
                missing["narrator"].append(i)
        for i, _ in enumerate(self.image_assets):
            if not self.has_image(i):
                missing["image"].append(i)
        return missing

    def is_complete(self) -> bool:
        """Check if all assets are present for all scenes."""
        missing = self.get_missing_narrator_and_image_assets()
        return len(missing["narrator"]) == 0 and len(missing["image"]) == 0


class NarratorAndImageAssetManager:
    """Class to manage video assets creation."""

    def __init__(self, story_folder: Path, chapter_index: int):
        """Initialize VideoAssetManager with story folder and chapter index."""

        logger.info(
            f"Initializing VideoAssetManager for story: {story_folder.name}, chapter: {chapter_index}"
        )

        self.story_folder = story_folder
        self.chapter_index = chapter_index
        self.output_file_prefix = f"chapter_{self.chapter_index+1:03}"

        self.__paths = VideoCreatorPaths(story_folder, chapter_index)
        self.recipe = NarratorAndImageRecipeFile(self.__paths.narrator_and_image_recipe_file)
        self.video_assets = NarratorAndImageAssetsFile(
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
                f"Successfully generated narrator for scene {scene_index}: {output_audio.name}"
            )

        except (IOError, OSError, RuntimeError) as e:
            logger.error(f"Failed to generate narrator for scene {scene_index}: {e}")

    def _generate_image_asset(self, scene_index: int):
        """Generate image asset for a scene."""
        try:
            logger.info(f"Generating image asset for scene {scene_index}")
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
                    f"Successfully generated image for scene {scene_index}: {img.name}"
                )
            logger.info(
                f"Using generated image for scene {scene_index}: {first_output_image.name}"
            )

        except (IOError, OSError, RuntimeError) as e:
            logger.error(f"Failed to generate image for scene {scene_index}: {e}")

    def generate_narrator_and_image_assets(self):
        """Generate all missing assets from the recipe."""
        with begin_file_logging(
            name="VideoAssetManager",
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
                logger.info(f"Processing scene {scene_index}...")
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
