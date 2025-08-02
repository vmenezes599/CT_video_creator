"""
AI Video Generation Module
"""

from pathlib import Path

from .modules.video_assembler import VideoAssembler
from .modules.video_asset_manager import VideoAssetManager
from .modules.video_recipe import VideoRecipeBuilder


def create_chapter_video_recipe(story_path: Path, chapter_index: Path) -> None:
    """
    Create a video from a video prompt file.

    Args:
        video_prompt_path: Path to the video prompt file.

    Returns:
        None
    """
    video_recipe_builder = VideoRecipeBuilder(
        story_folder=story_path, chapter_prompt_index=chapter_index
    )
    video_recipe_builder.create_video_recipe()

    video_asset_manager = VideoAssetManager(
        story_folder=story_path, chapter_index=chapter_index
    )
    video_asset_manager.generate_recipe_output()


def assemble_chapter_video(story_path: Path, chapter_index: int) -> None:
    """
    Assemble a chapter video from the recipe.

    Args:
        story_path: Path to the story folder.
        chapter_index: Chapter index to assemble video for.

    Returns:
        None
    """
    video_assembler = VideoAssembler(
        story_folder=story_path,
        chapter_index=chapter_index,
    )
    video_assembler.assemble_video()
