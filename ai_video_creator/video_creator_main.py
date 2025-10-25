"""This module is the main entry point for the AI Video Creator application."""

from pathlib import Path
from .video_creator import (
    create_narrator_and_image_recipe_from_prompt,
    create_narrators_and_images_from_recipe,
    create_sub_videos_from_sub_video_recipes,
    create_sub_video_recipes_from_images,
    assemble_final_video,
    clean_unused_assets,
)


def main():
    """Main function to run the AI Video Creator application."""
    user_folder = Path(".").resolve()
    story_path = "simple_story"
    chapter_index = 0

    clean_unused_assets(user_folder, story_path, chapter_index)

    # create_narrator_and_image_recipe_from_prompt(user_folder, story_path, chapter_index)
    create_narrators_and_images_from_recipe(user_folder, story_path, chapter_index)
    create_sub_video_recipes_from_images(user_folder, story_path, chapter_index)
    create_sub_videos_from_sub_video_recipes(user_folder, story_path, chapter_index)
    assemble_final_video(user_folder, story_path, chapter_index)


if __name__ == "__main__":
    main()
