""" "Garbage collector utilities for cleaning up generated assets."""

from pathlib import Path
from loguru import logger

from ai_video_creator.utils.video_creator_paths import VideoCreatorPaths
from ai_video_creator.modules.narrator import NarratorAssets
from ai_video_creator.modules.image import ImageAssets
from ai_video_creator.modules.sub_video import (
    SubVideoAssets,
    SubVideoRecipe,
)
from ai_video_creator.modules.video_assembler import (
    VideoAssemblerAssets,
    VideoAssemblerRecipe,
)


def internal_clean_unused_assets(user_folder: Path, story_name: str, chapter_index: int) -> None:
    """Cleans all generated assets for a given story and chapter."""

    logger.info(f"Cleaning unused assets for story: {story_name}, chapter: {chapter_index + 1}")

    paths = VideoCreatorPaths(user_folder, story_name, chapter_index)

    narrator_assets = NarratorAssets(paths)
    image_assets = ImageAssets(paths)
    sub_video_assets = SubVideoAssets(paths)
    sub_video_recipe = SubVideoRecipe(paths)
    video_assembler_assets = VideoAssemblerAssets(paths)
    video_assembler_recipe = VideoAssemblerRecipe(paths)

    assets_to_keep = set()
    assets_to_keep.update(narrator_assets.get_used_assets_list())
    assets_to_keep.update(image_assets.get_used_assets_list())
    assets_to_keep.update(sub_video_assets.get_used_assets_list())
    assets_to_keep.update(sub_video_recipe.get_used_assets_list())
    assets_to_keep.update(video_assembler_assets.get_used_assets_list())
    assets_to_keep.update(video_assembler_recipe.get_used_assets_list())

    all_folders_to_clean = [
        paths.narrator_asset_folder,
        paths.image_asset_folder,
        paths.sub_videos_asset_folder,
        paths.video_assembler_asset_folder,
    ]

    for folder in all_folders_to_clean:
        if not folder.exists() or not folder.is_dir():
            continue

        for item in folder.iterdir():
            if item.is_file() and item not in assets_to_keep:
                logger.debug(f"Deleting unused asset: {item}")
                item.unlink()

    logger.info("Unused asset cleanup completed.")
