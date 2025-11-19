"""Module to manage video assembler recipe data and persistence."""

import random
import json
from pathlib import Path

from ct_logging import logger

from ct_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER
from ct_video_creator.utils import (
    VideoCreatorPaths,
    SubtitleAlignment,
    SubtitlePosition,
    ensure_collection_index_exists,
)
from ct_video_creator.media_effects.effect_base import EffectBase
from ct_video_creator.media_effects.effects_map import create_effect_from_data


class NarratorAssetEffects:
    """Class to hold both assets and effects for a media type."""

    def __init__(self):
        """Initialize AssetsEffects with empty lists."""
        self.narrator_effects: list[list[EffectBase | None]] = []

    def add_narrator_effect(self, scene_index: int, effect: EffectBase) -> None:
        """Add an effect to narrator effects for a specific scene."""
        ensure_collection_index_exists(self.narrator_effects, scene_index)
        self.narrator_effects[scene_index].append(effect)

    def get_narrator_effects(self, scene_index: int) -> list[EffectBase | None]:
        """Get narrator effects for a specific scene."""
        ensure_collection_index_exists(self.narrator_effects, scene_index)
        return self.narrator_effects[scene_index]

    def clear_assets_effects(self, scene_index: int) -> None:
        """Clear all effects for a specific scene."""
        ensure_collection_index_exists(self.narrator_effects, scene_index)
        self.narrator_effects[scene_index].clear()

    def from_dict(self, data: dict) -> None:
        """Load effects from a dictionary."""
        narrator_effects = data.get("narrator_effects", [])
        for effects_list in narrator_effects:
            effect_instances = []
            for effect_data in effects_list:
                effect_instance = create_effect_from_data(effect_data)
                effect_instances.append(effect_instance)
            self.narrator_effects.append(effect_instances)

    def to_dict(self) -> dict:
        """Serialize effects to a dictionary."""
        return {
            "narrator_effects": [
                [effect.to_dict() if effect else None for effect in effects_list]
                for effects_list in self.narrator_effects
            ]
        }

    def is_empty(self) -> bool:
        """Check if narrator asset effects are empty."""
        return all(effects_list for effects_list in self.narrator_effects)

    def clear(self) -> None:
        """Clear all narrator effects."""
        self.narrator_effects = []


class VideoIntroRecipe:
    """
    Intro video recipe class.
    """

    DEFAULT_INTRO_ASSET = Path(f"{DEFAULT_ASSETS_FOLDER}/intros/intro_20s.mp4")

    def __init__(self, paths: VideoCreatorPaths):
        """Initialize IntroEffects with empty lists."""
        self._paths = paths
        self.skip: bool = False
        self.intro_asset: Path | None = None
        self.intro_effects: list[EffectBase | None] = []

    def from_dict(self, data: dict) -> None:
        """Load effects from a dictionary."""
        self.skip = data.get("skip", False)
        self.intro_effects = data.get("intro_effects", [])

        intro_asset_masked = data.get("intro_asset", None)
        self.intro_asset = self._paths.unmask_asset_path(Path(intro_asset_masked)) if intro_asset_masked else None

    def to_dict(self) -> dict:
        """Serialize effects to a dictionary."""

        available_intro_folders = [
            self._paths.get_default_assets_folder() / "intros",
            self._paths.get_user_assets_folder() / "intros",
        ]
        available_intros = []
        for path in available_intro_folders:
            available_intros.extend([str(self._paths.mask_asset_path(f)) for f in path.glob("*.mp4")])

        if self.intro_asset:
            intro_asset_masked = str(self._paths.mask_asset_path(self.intro_asset))
        else:
            intro_asset_masked = None

        result = {
            "skip": self.skip,
            "intro_asset": intro_asset_masked,
            "available_intros": available_intros,
            "intro_effects": [effect.to_dict() if effect else None for effect in self.intro_effects],
        }

        return result

    def is_empty(self) -> bool:
        """Check if intro effects are empty."""
        return not self.intro_effects and self.intro_asset is None

    def clear(self) -> None:
        """Clear intro asset and effects."""
        self.skip = False
        self.intro_asset = None
        self.intro_effects = []


class VideoEndingRecipe:
    """
    Ending video recipe class.
    """

    DEFAULT_ENDING_OVERLAY_ASSET = Path(f"{DEFAULT_ASSETS_FOLDER}/outros/CTA_YOUTUBE_INGLES.mov")

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize EndingEffects with empty lists."""
        self._paths = video_creator_paths
        self.skip: bool = False
        self.narrator_text_list: list[str] = []
        self.narrator_clone_voice: Path | None = None
        self.seed: int = random.randint(0, (2**31) - 1)
        self.ending_overlay_start_narrator_index: int | None = None
        self.ending_start_delay_seconds: float | None = None
        self.ending_overlay_asset: Path | None = None
        self.sub_video: Path | None = None

    def from_dict(self, data: dict) -> None:
        """Load effects from a dictionary."""
        self.skip = data.get("skip", False)
        self.narrator_text_list = data.get("narrator_list", [])
        narrator_clone_voice = data.get("narrator_clone_voice", None)
        self.narrator_clone_voice = (
            self._paths.unmask_asset_path(Path(narrator_clone_voice)) if narrator_clone_voice else None
        )

        self.seed = data.get("seed", random.randint(0, 1**64 - 1))
        self.ending_overlay_start_narrator_index = data.get("ending_overlay_start_narrator_index", None)
        self.ending_start_delay_seconds = data.get("ending_start_delay_seconds", None)
        ending_overlay_asset = data.get("ending_overlay_asset", None)
        self.ending_overlay_asset = (
            self._paths.unmask_asset_path(Path(ending_overlay_asset)) if ending_overlay_asset else None
        )
        sub_video = data.get("subvideo", None)
        self.sub_video = self._paths.unmask_asset_path(Path(sub_video)) if sub_video else None

    def to_dict(self) -> dict:
        """Serialize effects to a dictionary."""

        narrator_clone_voice_str = (
            str(self._paths.mask_asset_path(self.narrator_clone_voice)) if self.narrator_clone_voice else None
        )

        ending_overlay_asset_str = (
            str(self._paths.mask_asset_path(self.ending_overlay_asset)) if self.ending_overlay_asset else None
        )

        sub_video_str = str(self._paths.mask_asset_path(self.sub_video)) if self.sub_video else None

        result = {
            "skip": self.skip,
            "narrator_list": self.narrator_text_list,
            "narrator_clone_voice": narrator_clone_voice_str,
            "seed": self.seed,
            "ending_overlay_start_narrator_index": self.ending_overlay_start_narrator_index,
            "ending_start_delay_seconds": self.ending_start_delay_seconds,
            "ending_overlay_asset": ending_overlay_asset_str,
            "sub_video": sub_video_str,
        }

        return result

    def is_empty(self) -> bool:
        """Check if ending effects are empty."""
        return not self.narrator_text_list and self.ending_overlay_asset is None and self.narrator_clone_voice is None

    def clear(self) -> None:
        """Clear ending asset and effects."""
        self.skip = False
        self.ending_overlay_asset = None
        self.narrator_clone_voice = None
        self.seed = random.randint(0, 1**64 - 1)
        self.narrator_text_list = []
        self.ending_overlay_start_narrator_index = None
        self.ending_start_delay_seconds = None
        self.sub_video = None


class VideoOverlayRecipe:
    """
    Outro effects class.
    """

    DEFAULT_OVERLAY_ASSET = Path(f"{DEFAULT_ASSETS_FOLDER}/outros/CTA_YOUTUBE_INGLES.mov")
    DEFAULT_START_TIME_SECONDS = 10
    DEFAULT_INTERVAL_SECONDS = 60

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize OutroEffects with empty lists."""
        self._paths = video_creator_paths
        self.skip: bool = False
        self.overlay_asset: Path | None = None
        self.start_time_seconds: int = self.DEFAULT_START_TIME_SECONDS
        self.interval_seconds: int = self.DEFAULT_INTERVAL_SECONDS
        self.overlay_effects: list[EffectBase] = []

    def from_dict(self, data: dict) -> None:
        """Load effects from a dictionary."""
        self.skip = data.get("skip", False)
        self.overlay_effects = data.get("outro_effects", [])
        self.interval_seconds = data.get("interval_seconds", self.DEFAULT_INTERVAL_SECONDS)
        self.start_time_seconds = data.get("start_time_seconds", self.DEFAULT_START_TIME_SECONDS)

        outro_asset_masked = data.get("outro_asset", None)
        self.overlay_asset = self._paths.unmask_asset_path(Path(outro_asset_masked)) if outro_asset_masked else None

    def to_dict(self) -> dict:
        """Serialize effects to a dictionary."""

        available_outro_folders = [
            self._paths.get_default_assets_folder() / "outros",
            self._paths.get_user_assets_folder() / "outros",
        ]
        available_outros = []
        for path in available_outro_folders:
            available_outros.extend([str(self._paths.mask_asset_path(f)) for f in path.glob("*")])

        if self.overlay_asset:
            masked_outro_asset = str(self._paths.mask_asset_path(self.overlay_asset))
        else:
            masked_outro_asset = None

        return {
            "skip": self.skip,
            "outro_asset": masked_outro_asset,
            "available_outros": available_outros,
            "interval_seconds": self.interval_seconds,
            "start_time_seconds": self.start_time_seconds,
            "outro_effects": [effect.to_dict() if effect else None for effect in self.overlay_effects],
        }

    def is_empty(self) -> bool:
        """Check if outro effects are empty."""
        return not self.overlay_effects and self.overlay_asset is None

    def clear(self) -> None:
        """Clear outro asset and effects."""
        self.skip = False
        self.overlay_asset = None
        self.overlay_effects = []
        self.interval_seconds = self.DEFAULT_INTERVAL_SECONDS
        self.start_time_seconds = self.DEFAULT_START_TIME_SECONDS


class SubtitleRecipe:
    """Class to hold subtitle recipe data."""

    def __init__(self):
        """Initialize SubtitleRecipe with default values."""
        self.skip: bool = False
        self.burn_subtitles_into_video: bool = False
        self.word_level_timestamps: bool = False
        self.segment_level_timestamps: bool = True
        self.karaoke: bool = True
        self.subtitle_margin: int = 25
        self.font_size: int = 12
        self.position: SubtitlePosition = SubtitlePosition.BOTTOM
        self.alignment: SubtitleAlignment = SubtitleAlignment.CENTER

    def to_dict(self) -> dict:
        """Serialize subtitle recipe to a dictionary."""
        available_positions = [pos.value for pos in SubtitlePosition]
        available_alignments = [align.value for align in SubtitleAlignment]

        return {
            "skip": self.skip,
            "burn_subtitles_into_video": self.burn_subtitles_into_video,
            "word_level_timestamps": self.word_level_timestamps,
            "segment_level_timestamps": self.segment_level_timestamps,
            "karaoke": self.karaoke,
            "margin": self.subtitle_margin,
            "font_size": self.font_size,
            "position": self.position.value,
            "available_positions": available_positions,
            "alignment": self.alignment.value,
            "available_alignments": available_alignments,
        }

    def from_dict(self, data: dict) -> None:
        """Load subtitle recipe from a dictionary."""
        self.skip = data.get("skip", False)
        self.burn_subtitles_into_video = data.get("burn_subtitles_into_video", False)
        self.word_level_timestamps = data.get("word_level_timestamps", False)
        self.segment_level_timestamps = data.get("segment_level_timestamps", True)
        self.subtitle_margin = data.get("margin", 25)
        self.font_size = data.get("font_size", 12)
        self.karaoke = data.get("karaoke", True)

        position_value = data.get("position", "bottom")
        try:
            self.position = SubtitlePosition(position_value.lower())
        except ValueError:
            logger.warning(f"Invalid position value '{position_value}', defaulting to BOTTOM")
            self.position = SubtitlePosition.BOTTOM

        # Transform alignment string to SubtitleAlignment enum
        alignment_value = data.get("alignment", "center")
        try:
            self.alignment = SubtitleAlignment(alignment_value.lower())
        except ValueError:
            logger.warning(f"Invalid alignment value '{alignment_value}', defaulting to CENTER")
            self.alignment = SubtitleAlignment.CENTER


class VideoAssemblerRecipe:
    """Class to manage video assembler recipe data and persistence only."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize VideoAssemblerRecipe with file path."""
        self.effects_file_path = video_creator_paths.video_assembler_recipe_file
        self._narrator_asset_effects = NarratorAssetEffects()
        self._video_intro_recipe = VideoIntroRecipe(video_creator_paths)
        self._video_ending_recipe = VideoEndingRecipe(video_creator_paths)
        self._video_overlay_recipe = VideoOverlayRecipe(video_creator_paths)
        self._subtitle_recipe = SubtitleRecipe()

        self._load_effects_from_file()

    def _load_effects_from_file(self):
        """Load video assembler recipe from the video assembler recipe file."""
        try:
            logger.debug(f"Loading video assembler recipe from: {self.effects_file_path.name}")
            with open(self.effects_file_path, "r", encoding="utf-8") as file_handler:
                data: dict = json.load(file_handler)

            self._narrator_asset_effects.from_dict(data.get("narrator_asset_effects", {}))
            self._video_ending_recipe.from_dict(data.get("video_ending_recipe", {}))
            self._video_intro_recipe.from_dict(data.get("video_intro_recipe", {}))
            self._video_overlay_recipe.from_dict(data.get("video_overlay_recipe", {}))
            self._subtitle_recipe.from_dict(data.get("subtitle_recipe", {}))

            logger.info("Successfully loaded video assembler recipe.")
        except FileNotFoundError:
            logger.warning(f"Video assembler recipe file not found: {self.effects_file_path.name}")
        except (
            json.JSONDecodeError,
            PermissionError,
            OSError,
            KeyError,
            ValueError,
            TypeError,
        ) as e:
            logger.error(f"Failed to load video assembler recipe - invalid data format: {e}")
        finally:
            self.save_to_file()

    def save_to_file(self) -> None:
        """Save the current state of the video assembler recipe to a file."""
        try:
            result = {
                "video_intro_recipe": self._video_intro_recipe.to_dict(),
                "video_ending_recipe": self._video_ending_recipe.to_dict(),
                "video_overlay_recipe": self._video_overlay_recipe.to_dict(),
                "subtitle_recipe": self._subtitle_recipe.to_dict(),
                "narrator_asset_effects": self._narrator_asset_effects.to_dict(),
            }
            with open(self.effects_file_path, "w", encoding="utf-8") as file_handler:
                json.dump(result, file_handler, indent=4)
            logger.trace("Video assembler recipe saved.")

        except IOError as e:
            logger.error(f"Error saving video assembler recipe to {self.effects_file_path.name}: {e}")

    def match_size_to_target(self, target_size: int) -> None:
        """Ensure video_effects lists have the specified target size."""
        logger.debug(f"Ensuring effects size - target size: {target_size}")

        # Extend or truncate narrator_effects to match target size
        while len(self._narrator_asset_effects.narrator_effects) < target_size:
            self._narrator_asset_effects.narrator_effects.append([])
        self._narrator_asset_effects.narrator_effects = self._narrator_asset_effects.narrator_effects[:target_size]

        logger.debug(f"Ensured narrator effects: {len(self._narrator_asset_effects.narrator_effects)}")

    def is_complete(self) -> bool:
        """Check if the VideoAssemblerRecipe is properly initialized."""
        return (
            not self._narrator_asset_effects.is_empty()
            and not self._video_intro_recipe.is_empty()
            and not self._video_overlay_recipe.is_empty()
        )

    def clear(self) -> None:
        """Clear all effects."""
        self._narrator_asset_effects.clear()
        self._video_intro_recipe.clear()
        self._video_overlay_recipe.clear()

    def get_narrator_effects(self, index: int) -> list[list[EffectBase | None]]:
        """Get narrator asset effects."""
        return self._narrator_asset_effects.narrator_effects[index]

    def add_narrator_effect(self, index: int, effect: EffectBase) -> None:
        """Add narrator effect to a specific index."""
        self._narrator_asset_effects.add_narrator_effect(index, effect)

    def len_narrator_effects(self) -> int:
        """Get the number of narrator effects."""
        return len(self._narrator_asset_effects.narrator_effects)

    def get_video_intro_recipe(self) -> VideoIntroRecipe:
        """Get video intro recipe."""
        return self._video_intro_recipe

    def set_video_intro_recipe(self, intro_recipe: VideoIntroRecipe) -> None:
        """Set video intro recipe."""
        self._video_intro_recipe = intro_recipe
        self.save_to_file()

    def get_video_overlay_recipe(self) -> VideoOverlayRecipe:
        """Get video overlay recipe."""
        return self._video_overlay_recipe

    def set_video_overlay_recipe(self, overlay_recipe: VideoOverlayRecipe) -> None:
        """Set video overlay recipe."""
        self._video_overlay_recipe = overlay_recipe
        self.save_to_file()

    def get_video_ending_recipe(self) -> VideoEndingRecipe:
        """Get video ending recipe."""
        return self._video_ending_recipe

    def set_video_ending_recipe(self, ending_recipe: VideoEndingRecipe) -> None:
        """Set video ending recipe."""
        self._video_ending_recipe = ending_recipe
        self.save_to_file()

    def set_video_ending_subvideo(self, subvideo: Path) -> Path:
        """Set video ending subvideo."""
        self._video_ending_recipe.sub_video = subvideo
        self.save_to_file()

    def get_subtitle_recipe(self) -> SubtitleRecipe:
        """Get subtitle recipe."""
        return self._subtitle_recipe

    def get_used_assets_list(self) -> list[Path]:
        """Get a list of all used video asset file paths."""
        used_assets = []

        if self._video_ending_recipe.sub_video:
            used_assets.append(self._video_ending_recipe.sub_video)

        return used_assets
