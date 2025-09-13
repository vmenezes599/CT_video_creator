"""This module is the main entry point for the AI Video Creator application."""

from pathlib import Path
from .video_creator import (
    create_narrator_and_image_recipe_from_prompt,
    create_narrators_and_images_from_recipe,
    create_sub_videos_from_video_recipe,
    create_sub_videos_recipe_from_images,
    assemble_final_video,
)


def main():
    """Main function to run the AI Video Creator application."""
    story_path = Path("stories/The retainer")
    chapter_index = 0

    create_narrator_and_image_recipe_from_prompt(story_path, chapter_index)
    create_narrators_and_images_from_recipe(story_path, chapter_index)
    create_sub_videos_recipe_from_images(story_path, chapter_index)
    create_sub_videos_from_video_recipe(story_path, chapter_index)
    # create_video_from_scenes(story_path, chapter_index)


if __name__ == "__main__":
    main()
