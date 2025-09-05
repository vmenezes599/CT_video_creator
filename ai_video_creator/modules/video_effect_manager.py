"""
Video effect manager for create_video command.
"""

import json
from pathlib import Path

from logging_utils import begin_file_logging, logger

from ai_video_creator.utils.video_recipe_paths import VideoRecipePaths
from ai_video_creator.media_effects.effect_base import EffectBase
from ai_video_creator.media_effects.effects_map import (
    EFFECTS_MAP,
    AudioExtender,
)

from .video_asset_manager import VideoAssets


class MediaEffects:
    """Class to manage video effects data and persistence only."""

    def __init__(self, effects_file_path: Path):
        """Initialize VideoEffects with file path."""
        self.effects_file_path = effects_file_path
        self.narrator_effects: list[list[EffectBase | None]] = []
        self.image_effects: list[list[EffectBase | None]] = []
        self._load_effects_from_file()

    def _create_effect_from_data(self, effect_data: dict) -> EffectBase | None:
        """Create an effect instance from serialized data."""
        if effect_data is None:
            return None

        effect_type = effect_data.get("type")
        if effect_type not in EFFECTS_MAP:
            logger.warning(f"Unknown effect type: {effect_type}")
            return None

        effect_instance = EFFECTS_MAP[effect_type].__new__(EFFECTS_MAP[effect_type])
        effect_instance.from_dict(effect_data)
        return effect_instance

    def _load_effects_from_file(self):
        """Load effects from the video effects file."""
        try:
            logger.debug(f"Loading video effects from: {self.effects_file_path.name}")
            with open(self.effects_file_path, "r", encoding="utf-8") as file_handler:
                data = json.load(file_handler)

            # Load effects from the saved data
            media_effects = data.get("media_effects", [])

            self.narrator_effects.clear()
            self.image_effects.clear()

            for effect_group in media_effects:
                narrator_effects_list = []
                video_effects_list = []

                # Load narrator effects
                for effect_data in effect_group.get("narrator_effects", []):
                    effect = self._create_effect_from_data(effect_data)
                    narrator_effects_list.append(effect)

                # Load video effects
                for effect_data in effect_group.get("video_effects", []):
                    effect = self._create_effect_from_data(effect_data)
                    video_effects_list.append(effect)

                self.narrator_effects.append(narrator_effects_list)
                self.image_effects.append(video_effects_list)

            logger.info(
                f"Successfully loaded {len(self.narrator_effects)} narrator effect groups and {len(self.image_effects)} image effect groups"
            )

        except FileNotFoundError:
            logger.debug(
                f"Effects file not found: {self.effects_file_path.name} - starting with empty effects"
            )
            self.narrator_effects = []
            self.image_effects = []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse video effects file: {e}")
            self.narrator_effects = []
            self.image_effects = []
        except (PermissionError, OSError) as e:
            logger.error(f"Failed to read video effects file: {e}")
            self.narrator_effects = []
            self.image_effects = []
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to load video effects - invalid data format: {e}")
            self.narrator_effects = []
            self.image_effects = []

    def save_effects_to_file(self) -> None:
        """Save the current state of the video effects to a file."""
        try:
            media_effects = []

            for narrator_effect, video_effect in zip(
                self.narrator_effects, self.image_effects
            ):
                narrator_effects = []
                video_effects = []
                for effect in narrator_effect:
                    narrator_effects.append(effect.to_dict() if effect else None)
                for effect in video_effect:
                    video_effects.append(effect.to_dict() if effect else None)
                media_effects.append(
                    {
                        "narrator_effects": narrator_effects,
                        "video_effects": video_effects,
                    }
                )

            result = {
                "media_effects": media_effects,
            }
            with open(self.effects_file_path, "w", encoding="utf-8") as file_handler:
                json.dump(result, file_handler, indent=4)
            logger.trace(f"Effects saved with {len(media_effects)} effect groups")

        except IOError as e:
            logger.error(
                f"Error saving video effects to {self.effects_file_path.name}: {e}"
            )

    def _ensure_index_exists(self, scene_index: int) -> None:
        """Extend lists to ensure the scene_index exists."""
        # Extend narrator_effects if needed
        while len(self.narrator_effects) <= scene_index:
            self.narrator_effects.append([])

        # Extend image_effects if needed
        while len(self.image_effects) <= scene_index:
            self.image_effects.append([])

    def add_narrator_effect(self, scene_index: int, effect: EffectBase) -> None:
        """Add an effect to narrator effects for a specific scene."""
        self._ensure_index_exists(scene_index)
        self.narrator_effects[scene_index].append(effect)
        logger.debug(
            f"Added narrator effect for scene {scene_index}: {type(effect).__name__}"
        )

    def add_image_effect(self, scene_index: int, effect: EffectBase) -> None:
        """Add an effect to image effects for a specific scene."""
        self._ensure_index_exists(scene_index)
        self.image_effects[scene_index].append(effect)
        logger.debug(
            f"Added image effect for scene {scene_index}: {type(effect).__name__}"
        )

    def clear_scene_effects(self, scene_index: int) -> None:
        """Clear all effects for a specific scene."""
        self._ensure_index_exists(scene_index)
        self.narrator_effects[scene_index].clear()
        self.image_effects[scene_index].clear()
        logger.debug(f"Cleared all effects for scene {scene_index}")

    def has_any_effects(self) -> bool:
        """Check if there are any effects loaded."""
        return any(effects for effects in self.narrator_effects) or any(
            effects for effects in self.image_effects
        )

    def get_narrator_effects(self, scene_index: int) -> list[EffectBase | None]:
        """Get narrator effects for a specific scene."""
        self._ensure_index_exists(scene_index)
        return self.narrator_effects[scene_index]

    def get_image_effects(self, scene_index: int) -> list[EffectBase | None]:
        """Get image effects for a specific scene."""
        self._ensure_index_exists(scene_index)
        return self.image_effects[scene_index]


class MediaEffectsManager:
    """Class to manage video effects creation and business logic."""

    def __init__(self, story_folder: Path, chapter_index: int):
        """Initialize MediaEffectsManager with story folder and chapter index."""
        self.__paths = VideoRecipePaths(story_folder, chapter_index)

        with begin_file_logging(
            name="MediaEffectsManager",
            log_level="TRACE",
            base_folder=self.__paths.video_path,
        ):
            logger.info(
                f"Initializing MediaEffectsManager for story: {story_folder.name}, chapter: {chapter_index}"
            )

            self.assets = VideoAssets(self.__paths.video_asset_file)
            if not self.assets.is_complete():
                raise ValueError(
                    "Video assets are incomplete. Please ensure all required assets are present."
                )

            self.video_effects = MediaEffects(self.__paths.video_effects_file)

            # Ensure video_effects lists have the same size as assets
            self._synchronize_effects_with_assets()

            # Only add default values if no effects were loaded
            if not self.video_effects.has_any_effects():
                self._add_default_values()

            self.video_effects.save_effects_to_file()

            logger.debug(
                f"MediaEffectsManager initialized with {len(self.video_effects.narrator_effects)} effect groups"
            )

    def _synchronize_effects_with_assets(self):
        """Ensure video_effects lists have the same size as assets."""
        assets_size = len(self.assets.narrator_assets)
        logger.debug(f"Synchronizing effects with assets - target size: {assets_size}")

        # Extend or truncate narrator_effects to match assets size
        while len(self.video_effects.narrator_effects) < assets_size:
            self.video_effects.narrator_effects.append([])
        self.video_effects.narrator_effects = self.video_effects.narrator_effects[
            :assets_size
        ]

        # Extend or truncate image_effects to match assets size
        while len(self.video_effects.image_effects) < assets_size:
            self.video_effects.image_effects.append([])
        self.video_effects.image_effects = self.video_effects.image_effects[
            :assets_size
        ]

        logger.debug(
            f"Effect synchronization completed - narrator effects: {len(self.video_effects.narrator_effects)}, image effects: {len(self.video_effects.image_effects)}"
        )

    def _add_default_values(self):
        """Add default values for video effects."""

        with begin_file_logging(
            name="MediaEffectsManager",
            log_level="TRACE",
            base_folder=self.__paths.video_path,
        ):
            logger.info("Adding default effect values")

            if len(self.video_effects.narrator_effects) > 0:
                self.video_effects.add_narrator_effect(0, AudioExtender(1.5))

            for index in range(1, len(self.video_effects.narrator_effects)):
                self.video_effects.add_narrator_effect(index, AudioExtender(1))

            logger.debug("Default effect values added successfully")
