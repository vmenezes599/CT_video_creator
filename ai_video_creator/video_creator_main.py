"""This module is the main entry point for the AI Video Creator application."""

from pathlib import Path
from .video_creator import (
    create_narrator_and_image_recipe_from_prompt,
    create_narrators_and_images_from_recipe,
    create_sub_videos_from_sub_video_recipes,
    create_sub_video_recipes_from_images,
    assemble_final_video,
)


def main():
    """Main function to run the AI Video Creator application."""
    story_path = Path("stories/Milenium Desert Prologue")
    chapter_index = 0

    create_narrator_and_image_recipe_from_prompt(story_path, chapter_index)
    create_narrators_and_images_from_recipe(story_path, chapter_index)
    create_sub_video_recipes_from_images(story_path, chapter_index)
    create_sub_videos_from_sub_video_recipes(story_path, chapter_index)
    assemble_final_video(story_path, chapter_index)


if __name__ == "__main__":
    main()
