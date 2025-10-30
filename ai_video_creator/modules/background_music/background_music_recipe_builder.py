"""Module for building background music generation prompts."""

from logging_utils import logger
from ai_video_creator.prompt import Prompt

from ai_video_creator.utils import VideoCreatorPaths

from .background_music_recipe import BackgroundMusicRecipe


class BackgroundMusicRecipeBuilder:
    """Background music recipe builder for creating background music recipes from stories."""

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize BackgroundMusicRecipeBuilder with recipe data."""

        self._paths = video_creator_paths
        story_folder = self._paths.story_folder

        logger.info(
            "Initializing BackgroundMusicRecipeBuilder for story:"
            f" {story_folder.name}, chapter: {self._paths.chapter_index + 1}"
        )

        self._chapter_prompt_path = self._paths.chapter_prompt_path

        # Load video prompt
        self._video_prompt = Prompt.load_from_json(self._chapter_prompt_path)

        self.recipe = None

    def _default_init_time(self) -> int:
        """Get the default initialization time for background music."""
        return 21

    def _get_default_end_time(self) -> int:
        """Get the total length of the chapter video in seconds."""
        return 120

    def _get_default_volume_level(self) -> float:
        """Get the default volume level for background music."""
        return 0.25

    def _verify_recipe_against_prompt(self) -> bool:
        """Verify the recipe against the prompt to ensure all required data is present."""
        logger.debug("Verifying background music recipe against prompt data")

        if not self.recipe.music_data or len(self.recipe.music_data) != len(self._video_prompt):
            return False

        return True

    def _extract_average_mood(self) -> str:
        """Extract average mood from video prompts."""
        return ""

    def _generate_music_prompt_from_mood(self, mood: str) -> str:
        """Generate a music prompt based on the given mood."""
        if mood:
            return f"Create background music that reflects a {mood} atmosphere."
        else:
            return "Create relaxing background music."

    def _create_default_background_music_recipe(self) -> None:
        """Create background music recipe using default prompts."""
        logger.info(f"Creating background music recipes for {len(self._video_prompt)} prompts")

        average_mood = self._extract_average_mood()

        average_mood_music_prompt = self._generate_music_prompt_from_mood(average_mood)

        music_info = {
            "prompt": average_mood_music_prompt,
            "start_time": self._default_init_time(),
            "end_time": self._get_default_end_time(),
            "volume_level": self._get_default_volume_level(),
        }
        self.recipe.add_music_data(music_info)

        logger.info(f"Successfully created {len(self._video_prompt)} background music recipes")

    def create_background_music_recipes(self) -> None:
        """Create background music recipe from story folder and chapter prompt index."""

        logger.info("Starting background music recipe creation process")

        self.recipe = BackgroundMusicRecipe(self._paths)

        if not self._verify_recipe_against_prompt():
            self.recipe.clean()
            self._create_default_background_music_recipe()

        logger.info("Background music recipe creation completed successfully")
