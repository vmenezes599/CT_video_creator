"""This module is the main entry point for the AI Video Creator application."""

from pathlib import Path
from ct_video_creator import (
    create_background_music_assets,
    create_background_music_recipe,
    create_assemble_video_recipe,
    create_sub_video_recipes,
    create_sub_videos_assets,
    create_narrator_assets,
    create_narrator_recipe,
    create_images_assets,
    create_image_recipe,
    clean_unused_assets,
    assemble_video,
    AspectRatios,
)


def main():
    """Main function to run the AI Video Creator application."""
    user_folder = Path(".").resolve()
    story_path = "simple_story"
    chapter_index = 0

    create_narrator_recipe(user_folder, story_path, chapter_index)
    create_narrator_assets(user_folder, story_path, chapter_index)
    create_image_recipe(user_folder, story_path, chapter_index, AspectRatios.RATIO_16_9)
    create_images_assets(user_folder, story_path, chapter_index)
    create_background_music_recipe(user_folder, story_path, chapter_index)
    create_background_music_assets(user_folder, story_path, chapter_index)
    create_sub_video_recipes(user_folder, story_path, chapter_index)
    create_sub_videos_assets(user_folder, story_path, chapter_index)
    create_assemble_video_recipe(user_folder, story_path, chapter_index)
    assemble_video(user_folder, story_path, chapter_index)

    clean_unused_assets(user_folder, story_path, chapter_index)


if __name__ == "__main__":
    main()
