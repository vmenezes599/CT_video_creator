"""This module is the main entry point for the AI Video Creator application."""

from pathlib import Path
from .video_creator import (
    create_narrators_and_images_assets,
    create_narrator_and_image_recipe,
    create_background_music_assets,
    create_background_music_recipe,
    create_sub_videos_assets,
    create_sub_video_recipes,
    create_assemble_video_recipe,
    assemble_video,
    clean_unused_assets,
)


def main():
    """Main function to run the AI Video Creator application."""
    user_folder = Path(".").resolve()
    story_path = "simple_story"
    chapter_index = 0

    create_background_music_recipe(user_folder, story_path, chapter_index)
    create_background_music_assets(user_folder, story_path, chapter_index)
    create_narrator_and_image_recipe(user_folder, story_path, chapter_index)
    create_narrators_and_images_assets(user_folder, story_path, chapter_index)
    create_background_music_recipe(user_folder, story_path, chapter_index)
    create_background_music_assets(user_folder, story_path, chapter_index)
    create_sub_video_recipes(user_folder, story_path, chapter_index)
    create_sub_videos_assets(user_folder, story_path, chapter_index)
    create_assemble_video_recipe(user_folder, story_path, chapter_index)
    assemble_video(user_folder, story_path, chapter_index)

    clean_unused_assets(user_folder, story_path, chapter_index)


if __name__ == "__main__":
    main()
