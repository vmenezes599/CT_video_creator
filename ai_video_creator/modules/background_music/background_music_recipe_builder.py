"""Module for building background music generation prompts."""

from logging_utils import logger
from ai_video_creator.prompt import Prompt

from ai_video_creator.utils import VideoCreatorPaths

from ai_video_creator.utils import get_audio_duration
from ai_video_creator.modules.narrator import NarratorAssets
from .background_music_recipe import BackgroundMusicRecipe, MusicRecipe


class BackgroundMusicRecipeBuilder:
    """Background music recipe builder for creating background music recipes from stories."""

    DEFAULT_VOLUME_LEVEL = 0.25

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize BackgroundMusicRecipeBuilder with recipe data."""

        self._paths = video_creator_paths
        story_folder = self._paths.story_folder

        logger.info(
            "Initializing BackgroundMusicRecipeBuilder for story:"
            f" {story_folder.name}, chapter: {self._paths.chapter_index + 1}"
        )

        self._chapter_prompt_path = self._paths.chapter_prompt_path

        self._narrator_assets = NarratorAssets(video_creator_paths)

        if not self._narrator_assets.is_complete():
            raise ValueError("Narrator assets are incomplete. Cannot build background music recipe.")

        # Load video prompt
        self._video_prompt = Prompt.load_from_json(self._chapter_prompt_path)

        self.recipe = None

    def _generate_music_prompt(self, music_data: dict) -> list[dict]:
        """Generate music prompt based on narrator and mood."""
        generated_prompts = {}

        assert len(music_data) == len(
            self._narrator_assets.narrator_assets
        ), "Mismatch between music data and narrator assets."


        same_mood_duration = 0

        for audio_asset, data in zip(music_data, self._narrator_assets.narrator_assets):
            narrator = data["narrator"]
            mood = data["mood"]
            narrator_info = get_audio_duration(audio_asset)
            
            
            same_mood_duration += narrator_info.duration_seconds
            
            
            

        return generated_prompts

    def _create_default_background_music_recipe(self) -> None:
        """Create background music recipe using default prompts."""
        logger.info(f"Creating background music recipes for {len(self._video_prompt)} prompts")

        music_data = []
        for prompt in self._video_prompt:
            narrator = prompt.narrator
            mood = prompt.mood

            music_data.append({"narrator": narrator, "mood": mood})

        music_data = self._generate_music_prompt(music_data)

        for data in music_data:
            narrator = data["narrator"]
            music_prompt = data["music_prompt"]
            mood = data["mood"]

            music_recipe = MusicRecipe(
                narrator=narrator, prompt=music_prompt, mood=mood, volume_level=self.DEFAULT_VOLUME_LEVEL
            )
            self.recipe.add_music_recipe(music_recipe)

        logger.info(f"Successfully created {len(self._video_prompt)} background music recipes")

    def create_background_music_recipes(self) -> None:
        """Create background music recipe from story folder and chapter prompt index."""

        logger.info("Starting background music recipe creation process")

        self.recipe = BackgroundMusicRecipe(self._paths)

        if self.recipe.is_empty():
            self.recipe.clean()
            self._create_default_background_music_recipe()

        logger.info("Background music recipe creation completed successfully")
