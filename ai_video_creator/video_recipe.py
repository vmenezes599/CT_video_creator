"""
Video executor for create_video command.
"""

from pathlib import Path

from .prompt import Prompt
from .generators import SparkTTSComfyUIAudioGenerator as audio_generator
from .generators import FluxAIImageGenerator as image_generator


class VideoRecipeDefaultSettings:
    """Default settings for video recipe."""

    NARRATOR_VOICE = "default-assets/voices/voice_002.mp3"
    BACKGROUND_MUSIC = "default-assets/background_music.mp3"


class VideoRecipe:
    """Video recipe for creating videos from stories."""

    def __init__(
        self,
        voice_audios: list[Path],
        images: list[Path],
        narrator_audio: str = VideoRecipeDefaultSettings.NARRATOR_VOICE,
        background_music: str = VideoRecipeDefaultSettings.BACKGROUND_MUSIC,
    ):
        """Initialize VideoRecipe with required data.

        Args:
            voice_audios: List of Path objects for audio files
            images: List of Path objects for image files
            narrator_audio: Audio voice setting for narrator
            background_music: Background music setting
        """
        self.voice_audios = [str(path) for path in voice_audios]
        self.images = [str(path) for path in images]
        self.narrator_audio = narrator_audio
        self.background_music = background_music

    @classmethod
    def load_from_dict(cls, data: dict[str, any]) -> "VideoRecipe":
        """Load VideoRecipe from dictionary.

        Args:
            data: Dictionary containing recipe data

        Returns:
            VideoRecipe instance

        Raises:
            KeyError: If required keys are missing
            ValueError: If data format is invalid
        """
        required_keys = ["narrator", "visual_description"]
        for key in required_keys:
            if key not in data:
                raise KeyError(f"Missing required key: {key}")

        return cls(
            voice_audios=data["voice_audios"],
            images=data["images"],
            narrator_audio=data.get(
                "narrator_audio", VideoRecipeDefaultSettings.NARRATOR_VOICE
            ),
            background_music=data.get(
                "background_music", VideoRecipeDefaultSettings.BACKGROUND_MUSIC
            ),
        )

    def to_dict(self) -> dict[str, any]:
        """Convert VideoRecipe to dictionary.

        Returns:
            Dictionary representation of the recipe
        """
        return {
            "narrator": self.voice_audios,
            "voice_audios": self.voice_audios,
            "narrator_audio": self.narrator_audio,
            "background_music": self.background_music,
            "images": self.images,
        }


class VideoRecipeCreator:
    """Video recipe for creating videos from stories."""

    def __init__(self, story_path: Path, prompt_file: Path):
        """Initialize VideoRecipeCreator with video prompt.

        Args:
            video_prompt: Prompt containing story data
        """
        self.__video_prompt = Prompt.load_from_json(prompt_file)

        self.__video_path = story_path / "video"
        self.__assets_path = self.__video_path / "assets"
        self.__assets_path.mkdir(parents=True, exist_ok=True)

        self.__recipe_name = f"{self.__video_path.name}_{prompt_file.stem}_recipe"

    def generate_narration_audio(self, narrator_text: str) -> list[Path]:
        """Generate audio for the narrator text.

        Args:
            narrator_text: Text to convert to audio

        Returns:
            Path to the generated audio file
        """
        audio_name = self.__recipe_name + "_narration.mp3"
        return audio_generator().clone_text_to_speech(
            [narrator_text], audio_name, VideoRecipeDefaultSettings.NARRATOR_VOICE
        )

    def generate_visual_description(self, visual_description: str) -> list[Path]:
        """Generate visual description for the video.

        Args:
            visual_description: Description of the visual content

        Returns:
            Path to the generated visual description file
        """
        image_name = self.__recipe_name + "_visual.png"
        return image_generator().text_to_image([visual_description], image_name)

    def move_assets_to_story_folder(self, asset_list: list[Path]) -> list[Path]:
        """Move generated assets to the story folder."""
        new_path_list = []
        for asset in asset_list:
            asset_path = Path(asset)
            if asset_path.exists():
                target_path = self.__assets_path / asset_path.name
                asset_path.rename(target_path)
                new_path_list.append(target_path)

        return new_path_list

    def create_video_recipe(self) -> None:
        """Create a video recipe from the story.

        Args:
            chapter_index: Index of the chapter to process

        Returns:
            VideoRecipe instance

        Raises:
            ValueError: If prompt data is invalid
        """

        narrators = []
        visual_descriptions = []
        for prompt in self.__video_prompt:
            if not prompt.narrator or not prompt.visual_description:
                raise ValueError(
                    f"Invalid prompt data for chapter {self.__recipe_name}: "
                    f"narrator='{prompt.narrator}', "
                    f"visual_description='{prompt.visual_description}'"
                )

            narrators.append(prompt.narrator)
            visual_descriptions.append(prompt.visual_description)

        generated_audio_files = []
        generated_image_files = []
        for narrator, visual_description in zip(narrators, visual_descriptions):
            generated_audio_files.extend(self.generate_narration_audio(narrator))
            generated_image_files.extend(
                self.generate_visual_description(visual_description)
            )

        # Move generated assets to the story folder
        generated_audio_files = self.move_assets_to_story_folder(generated_audio_files)
        generated_image_files = self.move_assets_to_story_folder(generated_image_files)

        # Create VideoRecipe instance
        recipe = VideoRecipe(
            voice_audios=generated_audio_files,
            images=generated_image_files,
        )

        return recipe
