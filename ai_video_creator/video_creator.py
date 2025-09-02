"""
AI Video Generation Module
"""

from pathlib import Path

from logging_utils import setup_console_logging, cleanup_logging

from .modules.video_recipe import VideoRecipeBuilder
from .modules.video_asset_manager import VideoAssetManager
from .modules.video_effect_manager import MediaEffectsManager
from .modules.video_assembler import VideoAssembler


def create_recipe_from_prompt(story_path: Path, chapter_index: int) -> None:
    """
    Create a video from a video prompt file.

    Args:
        video_prompt_path: Path to the video prompt file.

    Returns:
        None
    """
    log_id = setup_console_logging("CreateVideoRecipe", log_level="TRACE")

    video_recipe_builder = VideoRecipeBuilder(
        story_folder=story_path, chapter_prompt_index=chapter_index
    )
    video_recipe_builder.create_video_recipe()

    cleanup_logging(log_id)


def create_assets_from_recipe(story_path: Path, chapter_index: int) -> None:
    """
    Create video assets from the recipe.
    """
    log_id = setup_console_logging("CreateAssetsFromRecipe", log_level="TRACE")

    video_asset_manager = VideoAssetManager(
        story_folder=story_path, chapter_index=chapter_index
    )
    video_asset_manager.generate_video_assets()

    video_effect_manager = MediaEffectsManager(
        story_folder=story_path, chapter_index=chapter_index
    )

    cleanup_logging(log_id)


def create_video_from_assets(story_path: Path, chapter_index: int) -> None:
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

    video_asset_manager = VideoAssetManager(
        story_folder=story_path, chapter_index=chapter_index
    )
    video_asset_manager.clean_unused_assets()
