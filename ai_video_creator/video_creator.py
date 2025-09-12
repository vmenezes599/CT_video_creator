"""
AI Video Generation Module
"""

from pathlib import Path

from logging_utils import setup_console_logging, cleanup_logging

from .modules.narrator_and_image_recipe import NarratorAndImageRecipeBuilder
from .modules.narrator_and_image_asset_manager import NarratorAndImageAssetManager
from .modules.video_recipe import VideoRecipeBuilder
from .modules.video_asset_manager import VideoAssetManager
from .modules.video_effect_manager import MediaEffectsManager
from .modules.video_assembler import VideoAssembler


def create_narrator_and_image_recipe_from_prompt(story_path: Path, chapter_index: int) -> None:
    """
    Create a video from a video prompt file.

    Args:
        video_prompt_path: Path to the video prompt file.

    Returns:
        None
    """
    log_id = setup_console_logging("CreateVideoRecipe", log_level="TRACE")

    video_recipe_builder = NarratorAndImageRecipeBuilder(
        story_folder=story_path, chapter_prompt_index=chapter_index
    )
    video_recipe_builder.create_narrator_and_image_recipe()

    cleanup_logging(log_id)


def create_narrators_and_images_from_recipe(
    story_path: Path, chapter_index: int
) -> None:
    """
    Create video assets from the recipe.
    """
    log_id = setup_console_logging(
        "CreateNarratorAndImagesFromRecipe", log_level="TRACE"
    )

    narrator_img_asset_manager = NarratorAndImageAssetManager(
        story_folder=story_path, chapter_index=chapter_index
    )
    narrator_img_asset_manager.generate_narrator_and_image_assets()

    video_effect_manager = MediaEffectsManager(
        story_folder=story_path, chapter_index=chapter_index
    )

    cleanup_logging(log_id)


def create_video_recipe_from_images(story_path: Path, chapter_index: int) -> None:
    """
    Create a video recipe from existing images and narrator audio files.
    """
    log_id = setup_console_logging("CreateVideoRecipeFromImages", log_level="TRACE")

    video_recipe_builder = VideoRecipeBuilder(
        story_folder=story_path, chapter_prompt_index=chapter_index
    )
    video_recipe_builder.create_video_recipe()

    cleanup_logging(log_id)


def create_video_assets_from_video_recipe(story_path: Path, chapter_index: int) -> None:
    """
    Create videos from the images in the recipe.
    """
    log_id = setup_console_logging("CreateVideosFromImages", log_level="TRACE")

    video_asset_manager = VideoAssetManager(
        story_folder=story_path, chapter_index=chapter_index
    )
    video_asset_manager.generate_video_assets()

    cleanup_logging(log_id)


def create_video_from_scenes(story_path: Path, chapter_index: int) -> None:
    """
    Assemble a chapter video from the recipe.

    Args:
        story_path: Path to the story folder.
        chapter_index: Chapter index to assemble video for.

    Returns:
        None
    """
    log_id = setup_console_logging("AssembleChapterVideo", log_level="TRACE")

    video_assembler = VideoAssembler(
        story_folder=story_path,
        chapter_index=chapter_index,
    )
    video_assembler.assemble_video()

    cleanup_logging(log_id)


def clean_unused_assets(story_path: Path, chapter_index: int) -> None:
    """Clean up video assets for a specific story folder."""

    video_asset_manager = NarratorAndImageAssetManager(
        story_folder=story_path, chapter_index=chapter_index
    )
    video_asset_manager.clean_unused_assets()
