"""
AI Video Generation Module
"""

from pathlib import Path

from logging_utils import setup_console_logging, cleanup_logging

from .modules.narrator_and_image import NarratorAndImageRecipeBuilder
from .modules.narrator_and_image import NarratorAndImageAssetManager
from .modules.video import SubVideoRecipeBuilder
from .modules.video import SubVideoAssetManager
from .modules.video import MediaEffectsManager
from .modules.video import VideoAssembler


def create_narrator_and_image_recipe_from_prompt(
    story_path: Path, chapter_index: int
) -> None:
    """
    Create a video from a video prompt file.

    Args:
        video_prompt_path: Path to the video prompt file.

    Returns:
        None
    """
    log_id = setup_console_logging(
        "CreateNarratorAndImageRecipesFromPrompt", log_level="TRACE"
    )

    video_recipe_builder = NarratorAndImageRecipeBuilder(
        story_folder=story_path, chapter_prompt_index=chapter_index
    )
    video_recipe_builder.create_narrator_and_image_recipes()

    cleanup_logging(log_id)


def create_narrators_and_images_from_recipe(
    story_path: Path, chapter_index: int
) -> None:
    """
    Create video assets from the recipe.
    """
    log_id = setup_console_logging(
        "create_narrator_and_images_from_recipe", log_level="TRACE"
    )

    narrator_img_asset_manager = NarratorAndImageAssetManager(
        story_folder=story_path, chapter_index=chapter_index
    )
    narrator_img_asset_manager.generate_narrator_and_image_assets()

    video_effect_manager = MediaEffectsManager(
        story_folder=story_path, chapter_index=chapter_index
    )

    cleanup_logging(log_id)


def create_sub_video_recipes_from_images(story_path: Path, chapter_index: int) -> None:
    """
    Create a video recipe from existing images and narrator audio files.
    """
    log_id = setup_console_logging(
        "create_sub_video_recipes_from_images", log_level="TRACE"
    )

    video_recipe_builder = SubVideoRecipeBuilder(
        story_folder=story_path, chapter_prompt_index=chapter_index
    )
    video_recipe_builder.create_video_recipe()

    cleanup_logging(log_id)


def create_sub_videos_from_sub_video_recipes(
    story_path: Path, chapter_index: int
) -> None:
    """
    Create videos from the images in the recipe.
    """
    log_id = setup_console_logging(
        "create_sub_videos_from_sub_video_recipes", log_level="TRACE"
    )

    video_asset_manager = SubVideoAssetManager(
        story_folder=story_path, chapter_index=chapter_index
    )
    video_asset_manager.generate_video_assets()

    cleanup_logging(log_id)


def assemble_final_video(story_path: Path, chapter_index: int) -> None:
    """
    Assemble a chapter video from the recipe.

    Args:
        story_path: Path to the story folder.
        chapter_index: Chapter index to assemble video for.

    Returns:
        None
    """

    raise NotImplementedError("Temporary disabled for fixing issues.")

    log_id = setup_console_logging("assemble_final_video", log_level="TRACE")

    video_assembler = VideoAssembler(
        story_folder=story_path,
        chapter_index=chapter_index,
    )
    video_assembler.assemble_video()

    cleanup_logging(log_id)


def clean_unused_assets(story_path: Path, chapter_index: int) -> None:
    """Clean up video assets for a specific story folder."""

    narrator_and_image_asset_manager = NarratorAndImageAssetManager(
        story_folder=story_path, chapter_index=chapter_index
    )
    narrator_and_image_asset_manager.clean_unused_assets()

    video_asset_manager = SubVideoAssetManager(
        story_folder=story_path, chapter_index=chapter_index
    )
    video_asset_manager.clean_unused_assets()
