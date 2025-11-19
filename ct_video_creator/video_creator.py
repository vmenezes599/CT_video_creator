"""
AI Video Generation Module
"""

from pathlib import Path

from ct_logging import setup_console_logging, setup_file_logging, cleanup_logging

from .modules.narrator import NarratorRecipeBuilder, NarratorAssetManager
from .modules.image import ImageRecipeBuilder, ImageAssetManager
from .modules.background_music import BackgroundMusicRecipeBuilder, BackgroundMusicAssetManager
from .modules.sub_video import SubVideoI2VRecipeBuilder, SubVideoT2VRecipeBuilder, SubVideoAssetManager
from .modules.video_assembler import VideoAssemblerRecipeBuilder, VideoAssembler

from .utils import VideoCreatorPaths, AspectRatios
from .utils.garbage_collector import internal_clean_unused_assets


def create_narrator_recipe(user_folder: Path, story_name: str, chapter_index: int) -> None:
    """
    Create a video from a video prompt file.

    Args:
        video_prompt_path: Path to the video prompt file.

    Returns:
        None
    """

    log_id = setup_console_logging("create_narrator_recipe", log_level="TRACE")

    paths = VideoCreatorPaths(
        user_folder=user_folder,
        story_name=story_name,
        chapter_index=chapter_index,
    )
    file_log_id = setup_file_logging(
        "create_narrator_recipe",
        log_level="TRACE",
        base_folder=str(paths.video_chapter_folder),
    )

    narrator_recipe_builder = NarratorRecipeBuilder(paths)
    narrator_recipe_builder.create_narrator_recipes()

    cleanup_logging(log_id)
    cleanup_logging(file_log_id)


def create_narrator_assets(user_folder: Path, story_name: str, chapter_index: int) -> None:
    """
    Create video assets from the recipe.
    """
    log_id = setup_console_logging("create_narrator_assets", log_level="TRACE")
    paths = VideoCreatorPaths(
        user_folder=user_folder,
        story_name=story_name,
        chapter_index=chapter_index,
    )
    file_log_id = setup_file_logging(
        "create_narrator_assets",
        log_level="TRACE",
        base_folder=str(paths.video_chapter_folder),
    )

    narrator_asset_manager = NarratorAssetManager(paths)
    narrator_asset_manager.generate_narrator_assets()

    cleanup_logging(log_id)
    cleanup_logging(file_log_id)


def create_image_recipe(user_folder: Path, story_name: str, chapter_index: int, aspect_ratio: AspectRatios) -> None:
    """
    Create images from the recipe.
    """

    log_id = setup_console_logging("create_image_recipe", log_level="TRACE")

    paths = VideoCreatorPaths(
        user_folder=user_folder,
        story_name=story_name,
        chapter_index=chapter_index,
    )
    file_log_id = setup_file_logging(
        "create_image_recipe",
        log_level="TRACE",
        base_folder=str(paths.video_chapter_folder),
    )

    image_recipe_builder = ImageRecipeBuilder(paths, aspect_ratio)
    image_recipe_builder.create_image_recipes()

    cleanup_logging(log_id)
    cleanup_logging(file_log_id)


def create_images_assets(user_folder: Path, story_name: str, chapter_index: int) -> None:
    """
    Create images from the recipe.
    """
    log_id = setup_console_logging("create_images_assets", log_level="TRACE")

    paths = VideoCreatorPaths(
        user_folder=user_folder,
        story_name=story_name,
        chapter_index=chapter_index,
    )
    file_log_id = setup_file_logging(
        "create_images_assets",
        log_level="TRACE",
        base_folder=str(paths.video_chapter_folder),
    )

    image_asset_manager = ImageAssetManager(paths)
    image_asset_manager.generate_image_assets()

    cleanup_logging(log_id)
    cleanup_logging(file_log_id)


def create_background_music_recipe(user_folder: Path, story_name: str, chapter_index: int) -> None:
    """
    Create background music from the recipe.
    """

    log_id = setup_console_logging("create_background_music_recipe", log_level="TRACE")

    paths = VideoCreatorPaths(
        user_folder=user_folder,
        story_name=story_name,
        chapter_index=chapter_index,
    )
    file_log_id = setup_file_logging(
        "create_background_music_recipe",
        log_level="TRACE",
        base_folder=str(paths.video_chapter_folder),
    )

    recipe_builder = BackgroundMusicRecipeBuilder(paths)
    recipe_builder.create_background_music_recipes()

    cleanup_logging(log_id)
    cleanup_logging(file_log_id)


def create_background_music_assets(user_folder: Path, story_name: str, chapter_index: int) -> None:
    """
    Create background music from the recipe.
    """
    log_id = setup_console_logging("create_background_music_assets", log_level="TRACE")

    paths = VideoCreatorPaths(
        user_folder=user_folder,
        story_name=story_name,
        chapter_index=chapter_index,
    )
    file_log_id = setup_file_logging(
        "create_background_music_assets",
        log_level="TRACE",
        base_folder=str(paths.video_chapter_folder),
    )

    asset_manager = BackgroundMusicAssetManager(paths)
    asset_manager.generate_background_music_assets()

    cleanup_logging(log_id)
    cleanup_logging(file_log_id)


def create_sub_video_recipes(user_folder: Path, story_name: str, chapter_index: int) -> None:
    """
    Create a video recipe from existing images and narrator audio files.
    """
    log_id = setup_console_logging("create_sub_video_recipes", log_level="TRACE")
    paths = VideoCreatorPaths(
        user_folder=user_folder,
        story_name=story_name,
        chapter_index=chapter_index,
    )
    file_log_id = setup_file_logging(
        "create_sub_video_recipes",
        log_level="TRACE",
        base_folder=str(paths.video_chapter_folder),
    )

    video_recipe_builder = SubVideoI2VRecipeBuilder(paths)
    video_recipe_builder.create_sub_video_recipe()

    cleanup_logging(log_id)
    cleanup_logging(file_log_id)


def create_sub_videos_assets(user_folder: Path, story_name: str, chapter_index: int) -> None:
    """
    Create videos from the images in the recipe.
    """
    log_id = setup_console_logging("create_sub_videos_assets", log_level="TRACE")

    paths = VideoCreatorPaths(
        user_folder=user_folder,
        story_name=story_name,
        chapter_index=chapter_index,
    )
    file_log_id = setup_file_logging(
        "create_sub_videos_assets",
        log_level="TRACE",
        base_folder=str(paths.video_chapter_folder),
    )

    video_asset_manager = SubVideoAssetManager(paths)
    video_asset_manager.generate_video_assets()

    cleanup_logging(log_id)
    cleanup_logging(file_log_id)


def create_assemble_video_recipe(user_folder: Path, story_name: str, chapter_index: int) -> None:
    """
    Create assemble video recipe from sub-videos.
    """
    log_id = setup_console_logging("create_assemble_video_recipe", log_level="TRACE")

    paths = VideoCreatorPaths(
        user_folder=user_folder,
        story_name=story_name,
        chapter_index=chapter_index,
    )
    file_log_id = setup_file_logging(
        "create_assemble_video_recipe",
        log_level="TRACE",
        base_folder=str(paths.video_chapter_folder),
    )

    _ = VideoAssemblerRecipeBuilder(paths)

    cleanup_logging(log_id)
    cleanup_logging(file_log_id)


def assemble_video(user_folder: Path, story_name: str, chapter_index: int) -> None:
    """
    Assemble a chapter video from the recipe.

    Args:
        story_path: Path to the story folder.
        chapter_index: Chapter index to assemble video for.

    Returns:
        None
    """
    log_id = setup_console_logging("assemble_video", log_level="TRACE")

    paths = VideoCreatorPaths(
        user_folder=user_folder,
        story_name=story_name,
        chapter_index=chapter_index,
    )
    file_log_id = setup_file_logging(
        "assemble_video",
        log_level="TRACE",
        base_folder=str(paths.video_chapter_folder),
    )

    video_assembler = VideoAssembler(paths)
    video_assembler.assemble_video()

    cleanup_logging(log_id)
    cleanup_logging(file_log_id)


def clean_unused_assets(user_folder: Path, story_name: str, chapter_index: int) -> None:
    """Clean up video assets for a specific story folder."""

    internal_clean_unused_assets(user_folder, story_name, chapter_index)
