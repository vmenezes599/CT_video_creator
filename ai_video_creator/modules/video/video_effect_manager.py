"""
Video effect manager for create_video command.
"""

import json
from pathlib import Path

from logging_utils import logger

from ai_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER
from ai_video_creator.utils import VideoCreatorPaths, ensure_collection_index_exists
from ai_video_creator.media_effects.effect_base import EffectBase
from ai_video_creator.media_effects.effects_map import (
    create_effect_from_data,
    AudioExtender,
)

from ai_video_creator.modules.narrator import NarratorAssets
from ai_video_creator.modules.image import ImageAssets


class AssetsEffects:
    """Class to hold both assets and effects for a media type."""

    def __init__(self):
        """Initialize AssetsEffects with empty lists."""
        self.narrator_effects: list[list[EffectBase | None]] = []
        self.image_effects: list[list[EffectBase | None]] = []

    def add_narrator_effect(self, scene_index: int, effect: EffectBase) -> None:
        """Add an effect to narrator effects for a specific scene."""
        ensure_collection_index_exists(self.narrator_effects, scene_index)
        self.narrator_effects[scene_index].append(effect)

    def add_image_effect(self, scene_index: int, effect: EffectBase) -> None:
        """Add an effect to image effects for a specific scene."""
        ensure_collection_index_exists(self.image_effects, scene_index)
        self.image_effects[scene_index].append(effect)

    def get_narrator_effects(self, scene_index: int) -> list[EffectBase | None]:
        """Get narrator effects for a specific scene."""
        ensure_collection_index_exists(self.narrator_effects, scene_index)
        return self.narrator_effects[scene_index]

    def get_image_effects(self, scene_index: int) -> list[EffectBase | None]:
        """Get image effects for a specific scene."""
        ensure_collection_index_exists(self.image_effects, scene_index)
        return self.image_effects[scene_index]

    def has_any_assets_effects(self) -> bool:
        """Check if there are any effects for either narrator or image assets."""
        return any(
            len(effects_list) > 0
            for effects_list in self.narrator_effects + self.image_effects
        )

    def clear_assets_effects(self, scene_index: int) -> None:
        """Clear all effects for a specific scene."""
        ensure_collection_index_exists(self.narrator_effects, scene_index)
        ensure_collection_index_exists(self.image_effects, scene_index)
        self.narrator_effects[scene_index].clear()
        self.image_effects[scene_index].clear()

    def from_dict(self, data: dict) -> None:
        """Load effects from a dictionary."""
        narrator_effects = data.get("narrator_effects", [])
        for effects_list in narrator_effects:
            effect_instances = []
            for effect_data in effects_list:
                effect_instance = create_effect_from_data(effect_data)
                effect_instances.append(effect_instance)
            self.narrator_effects.append(effect_instances)

        image_effects = data.get("image_effects", [])
        for effects_list in image_effects:
            effect_instances = []
            for effect_data in effects_list:
                effect_instance = create_effect_from_data(effect_data)
                effect_instances.append(effect_instance)
            self.image_effects.append(effect_instances)

    def to_dict(self) -> dict:
        """Serialize effects to a dictionary."""
        return {
            "narrator_effects": [
                [effect.to_dict() if effect else None for effect in effects_list]
                for effects_list in self.narrator_effects
            ],
            "image_effects": [
                [effect.to_dict() if effect else None for effect in effects_list]
                for effects_list in self.image_effects
            ],
        }


class IntroEffects:
    """
    Intro effects class.
    """

    DEFAULT_INTRO_ASSET = Path(f"{DEFAULT_ASSETS_FOLDER}/intros/intro_video.mp4")

    def __init__(self, paths: VideoCreatorPaths):
        """Initialize IntroEffects with empty lists."""
        self._paths = paths
        self.intro_asset: Path | None = None
        self.intro_effects: list[EffectBase | None] = []

    def from_dict(self, data: dict) -> None:
        """Load effects from a dictionary."""
        intro_asset_masked = data.get("intro_asset", Path())

        self.intro_effects = data.get("intro_effects", [])
        self.intro_asset = self._paths.unmask_asset_path(intro_asset_masked)

    def to_dict(self) -> dict:
        """Serialize effects to a dictionary."""

        available_intro_folders = [
            self._paths.get_default_assets_folder() / "intros",
            self._paths.get_user_assets_folder() / "intros",
        ]
        available_intros = []
        for path in available_intro_folders:
            available_intros.extend(
                [str(self._paths.mask_asset_path(f)) for f in path.glob("*.mp4")]
            )

        if self.intro_asset:
            intro_asset_masked = str(self._paths.mask_asset_path(self.intro_asset))
        else:
            intro_asset_masked = None

        result = {
            "intro_asset": intro_asset_masked,
            "available_intros": available_intros,
            "intro_effects": [
                effect.to_dict() if effect else None for effect in self.intro_effects
            ],
        }

        return result


class OutroEffects:
    """
    Outro effects class.
    """

    DEFAULT_OUTRO_ASSET = Path(f"{DEFAULT_ASSETS_FOLDER}/outros/CTA_YOUTUBE_INGLES.mov")

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize OutroEffects with empty lists."""
        self._paths = video_creator_paths
        self.outro_asset: Path | None = None
        self.outro_effects: list[EffectBase] = []

    def from_dict(self, data: dict) -> None:
        """Load effects from a dictionary."""
        outro_asset_masked = data.get("outro_asset", Path())

        self.outro_effects = data.get("outro_effects", [])
        self.outro_asset = self._paths.unmask_asset_path(outro_asset_masked)

    def to_dict(self) -> dict:
        """Serialize effects to a dictionary."""

        available_outro_folders = [
            self._paths.get_default_assets_folder() / "outros",
            self._paths.get_user_assets_folder() / "outros",
        ]
        available_outros = []
        for path in available_outro_folders:
            available_outros.extend(
                [str(self._paths.mask_asset_path(f)) for f in path.glob("*")]
            )

        if self.outro_asset:
            masked_outro_asset = str(self._paths.mask_asset_path(self.outro_asset))
        else:
            masked_outro_asset = None

        return {
            "outro_asset": masked_outro_asset,
            "available_outros": available_outros,
            "outro_effects": [
                effect.to_dict() if effect else None for effect in self.outro_effects
            ],
        }


class MediaEffects:
    """Class to manage video effects data and persistence only."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize VideoEffects with file path."""
        self.effects_file_path = video_creator_paths.video_effects_file
        self.assets_effects = AssetsEffects()
        self.intro_effects = IntroEffects(video_creator_paths)
        self.outro_effects = OutroEffects(video_creator_paths)

        self._load_effects_from_file()

    def _load_effects_from_file(self):
        """Load effects from the video effects file."""
        try:
            logger.debug(f"Loading video effects from: {self.effects_file_path.name}")
            with open(self.effects_file_path, "r", encoding="utf-8") as file_handler:
                data: dict = json.load(file_handler)

            required_fields = ["intro_effects", "outro_effects", "assets_effects"]
            missing_fields = set(data.keys()) - set(required_fields)
            if missing_fields:
                raise KeyError(f"Missing required fields: {missing_fields}")

            self.assets_effects.from_dict(data["assets_effects"])
            self.intro_effects.from_dict(data["intro_effects"])
            self.outro_effects.from_dict(data["outro_effects"])

            logger.info("Successfully loaded media effects.")

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
            result = {
                "intro_effects": self.intro_effects.to_dict(),
                "outro_effects": self.outro_effects.to_dict(),
                "assets_effects": self.assets_effects.to_dict(),
            }
            with open(self.effects_file_path, "w", encoding="utf-8") as file_handler:
                json.dump(result, file_handler, indent=4)
            logger.trace("Effects saved.")

        except IOError as e:
            logger.error(
                f"Error saving video effects to {self.effects_file_path.name}: {e}"
            )

    def ensure_effects_size(self, target_size: int) -> None:
        """Ensure video_effects lists have the specified target size."""
        logger.debug(f"Ensuring effects size - target size: {target_size}")

        # Extend or truncate narrator_effects to match target size
        while len(self.assets_effects.narrator_effects) < target_size:
            self.assets_effects.narrator_effects.append([])
        self.assets_effects.narrator_effects = self.assets_effects.narrator_effects[
            :target_size
        ]

        # Extend or truncate image_effects to match target size
        while len(self.assets_effects.image_effects) < target_size:
            self.assets_effects.image_effects.append([])
        self.assets_effects.image_effects = self.assets_effects.image_effects[
            :target_size
        ]

        logger.debug(
            f"Effect size ensured - narrator effects: {len(self.assets_effects.narrator_effects)},"
            f" image effects: {len(self.assets_effects.image_effects)}"
        )


class MediaEffectsManager:
    """Class to manage video effects creation and business logic."""

    def __init__(
        self,
        video_creator_paths: VideoCreatorPaths,
    ):
        """Initialize MediaEffectsManager with story folder and chapter index."""

        self._paths = video_creator_paths

        logger.info(
            f"Initializing MediaEffectsManager for story: {video_creator_paths.story_folder.name}, chapter: {video_creator_paths.chapter_index + 1}"
        )

        # Load separate narrator and image assets
        self.narrator_assets = NarratorAssets(video_creator_paths.narrator_asset_file)
        self.image_assets = ImageAssets(video_creator_paths.image_asset_file)

        if (
            not self.narrator_assets.is_complete()
            or not self.image_assets.is_complete()
        ):
            raise ValueError(
                "Video assets are incomplete. Please ensure all required assets are present."
            )

        self.media_effects = MediaEffects(video_creator_paths)

        # Ensure video_effects lists have the same size as assets
        self._synchronize_effects_with_assets()

        # Only add default values if no effects were loaded
        if not self.media_effects.assets_effects.has_any_assets_effects():
            self._add_default_values()

        self.media_effects.save_effects_to_file()

        logger.debug("MediaEffectsManager initialized.")

    def _synchronize_effects_with_assets(self):
        """Ensure video_effects lists have the same size as assets."""
        assets_size = len(self.narrator_assets.narrator_assets)
        logger.debug(f"Synchronizing effects with assets - target size: {assets_size}")

        self.media_effects.ensure_effects_size(assets_size)

        logger.debug(
            f"Effect synchronization completed - narrator effects: {len(self.media_effects.assets_effects.narrator_effects)},"
            f" image effects: {len(self.media_effects.assets_effects.image_effects)}"
        )

    def _add_default_values(self):
        """Add default values for video effects."""

        logger.info("Adding default effect values")

        if len(self.media_effects.narrator_effects) > 0:
            self.media_effects.assets_effects.add_narrator_effect(
                0,
                AudioExtender(seconds_to_extend_front=0.5, seconds_to_extend_back=1.5),
            )

        for index in range(1, len(self.media_effects.narrator_effects)):
            self.media_effects.assets_effects.add_narrator_effect(
                index,
                AudioExtender(seconds_to_extend_front=0, seconds_to_extend_back=1),
            )

        self.media_effects.intro_effects = IntroEffects(self._paths)
        self.media_effects.intro_effects.intro_asset = IntroEffects.DEFAULT_INTRO_ASSET

        self.media_effects.outro_effects = OutroEffects(self._paths)
        self.media_effects.outro_effects.outro_asset = OutroEffects.DEFAULT_OUTRO_ASSET

        logger.debug("Default effect values added successfully")
