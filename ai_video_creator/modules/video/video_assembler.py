"""
Video Creator Module

This module contains the VideoCreator class that orchestrates the entire video creation process
by coordinating image generation, audio generation, and video composition.
"""

from pathlib import Path

from logging_utils import begin_file_logging, logger

from ai_video_creator.modules.narrator_and_image import NarratorAndImageAssets
from ai_video_creator.generators import SubtitleGenerator
from ai_video_creator.utils import (
    burn_subtitles_to_video,
    create_video_segment_from_image_and_audio,
    concatenate_videos,
    VideoCreatorPaths,
)

from .video_effect_manager import MediaEffects


class VideoAssembler:
    """
    A class that orchestrates the video creation process by coordinating
    image generation, audio generation, and video composition.
    """

    def __init__(self, story_folder: Path, chapter_index: int):
        """
        Initialize VideoCreator with the required generators.
        """
        self.__paths = VideoCreatorPaths(story_folder, chapter_index)

        with begin_file_logging(
            name="VideoAssembler",
            log_level="TRACE",
            base_folder=self.__paths.video_path,
        ):
            self.__subtitle_generator = SubtitleGenerator()

            self.assets = NarratorAndImageAssets(
                self.__paths.narrator_and_image_asset_file
            )
            if not self.assets.is_complete():
                raise ValueError(
                    "Video assets are incomplete. Please ensure all required assets are present."
                )

            self.effects = MediaEffects(
                effects_file_path=self.__paths.video_effects_file
            )

            self.output_path = self.__paths.video_output_file
            self._temp_files = []

    def _combine_image_audio_video_segment(
        self, image_path: str, audio_path: str
    ) -> str:
        """
        Generate a video segment from an image and audio file.
        """
        image_path_obj = Path(image_path)
        temp_file = (
            self.__paths.narrator_and_image_asset_folder
            / f"temp_{image_path_obj.stem}.mp4"
        )

        output_path = create_video_segment_from_image_and_audio(
            image_path=image_path, audio_path=audio_path, output_path=temp_file
        )

        self._temp_files.append(output_path)
        return output_path

    def _concat_video_segments(self, video_segments: list[Path]) -> Path:
        """
        Concatenate video segments into a single video file.

        :param video_segments: List of paths to video segment files
        :return: Path to the concatenated video file
        """
        output_video_path = self.output_path.with_stem(f"{self.output_path.stem}_raw")

        return concatenate_videos(
            video_segments=video_segments, output_path=output_video_path
        )

    def _compose(self, video_segments: list[Path]):
        """
        Generate a video from a list of images.
        """
        assert len(video_segments) > 0, "No clips to compose."

        logger.info(f"Composing final video from {len(video_segments)} segments")

        # Step 2: Create concat list
        raw_video_path = self._concat_video_segments(video_segments)
        # self._temp_files.append(raw_video_path)

        # Generate subtitles using SubtitleGenerator
        str_file = self.__subtitle_generator.generate_subtitles_from_audio(  # pylint:disable=unused-variable
            raw_video_path
        )
        # self._temp_files.append(str_file)

        # Add subtitles to the final video
        # burn_subtitles_to_video(
        #    video_path=video_path, srt_path=srt_path, output_path=self.output_path
        # )

        logger.info(f"Cleaning up {len(self._temp_files)} temporary files")
        for f in self._temp_files:
            file_path = Path(f)
            if file_path.exists():
                logger.debug(f"Removing temporary file: {file_path.name}")
                file_path.unlink()
        logger.info("Cleanup completed")

    def _apply_media_effects(
        self, narrator_file_paths: list[Path], image_file_paths: list[Path]
    ) -> tuple[Path, Path]:
        """
        Apply media effects to the audio and image files.
        """
        processed_images: list[Path] = []
        for image_path, image_effects in zip(
            image_file_paths, self.effects.image_effects
        ):
            processed_image_path = image_path
            for effect in image_effects:
                if effect:
                    processed_image_path = effect.apply(processed_image_path)
                    self._temp_files.append(processed_image_path)
            processed_images.append(processed_image_path)

        processed_narrators: list[Path] = []
        for audio_path, audio_effects in zip(
            narrator_file_paths, self.effects.narrator_effects
        ):
            processed_narrator_path = audio_path
            for effect in audio_effects:
                if effect:
                    processed_narrator_path = effect.apply(processed_narrator_path)
                    self._temp_files.append(processed_narrator_path)
            processed_narrators.append(processed_narrator_path)

        return processed_narrators, processed_images

    def _create_video_segments(self) -> None:
        """
        Create video segments from the assets defined in the video recipe.
        """

        # Extract data from video recipe
        narrator_file_paths = self.assets.narrator_assets
        image_file_paths = self.assets.image_assets

        logger.info(
            f"Processing {len(narrator_file_paths)} audio files and {len(image_file_paths)} images"
        )

        processed_narrators, processed_images = self._apply_media_effects(
            narrator_file_paths, image_file_paths
        )

        video_segments = []
        for i, (image_path, audio_path) in enumerate(
            zip(processed_images, processed_narrators), 1
        ):
            logger.info(
                f"Processing segment {i}/{len(narrator_file_paths)}: {Path(image_path).name}"
            )

            video_segment = self._combine_image_audio_video_segment(
                image_path, audio_path
            )
            video_segments.append(video_segment)

        logger.info(f"Created {len(video_segments)} video segments")

        return video_segments

    def assemble_video(self) -> None:
        """
        Create a video from a video recipe.

        Args:
            video_recipe: VideoRecipe object containing narrator text and visual descriptions
            output_filename: Name of the output video file
        """
        with begin_file_logging(
            name="VideoAssembler",
            log_level="TRACE",
            base_folder=self.__paths.video_path,
        ):
            logger.info("Starting video assembly process")

            video_segments = self._create_video_segments()
            self._compose(video_segments)

            logger.info(f"Video assembly completed successfully: {self.output_path}")
