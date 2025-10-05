"""
Video Creator Module

This module contains the VideoCreator class that orchestrates the entire video creation process
by coordinating image generation, audio generation, and video composition.
"""

from pathlib import Path

from logging_utils import begin_file_logging, logger

from ai_video_creator.ComfyUI_automation import (
    ComfyUIRequests,
    copy_media_to_comfyui_input_folder,
    delete_media_from_comfyui_input_folder,
)
from ai_video_creator.modules.narrator import NarratorAssets
from ai_video_creator.modules.image import ImageAssets
from ai_video_creator.generators.ComfyUI_automation import (
    VideoUpscaleFrameInterpWorkflow,
)
from ai_video_creator.generators import SubtitleGenerator
from ai_video_creator.utils import (
    burn_subtitles_to_video,
    create_video_segment_from_sub_video_and_audio_freeze_last_frame,
    create_video_segment_from_sub_video_and_audio_reverse_video,
    create_video_segment_from_image_and_audio,
    concatenate_videos_with_reencoding,
    concatenate_videos_no_reencoding,
    safe_move,
    VideoCreatorPaths,
)

from .sub_video_assets import SubVideoAssets
from .video_effect_manager import MediaEffects
from .video_assembler_assets import VideoAssemblerAssets


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

        self.__subtitle_generator = SubtitleGenerator()

        # Load separate narrator and image assets
        self.narrator_assets = NarratorAssets(self.__paths.narrator_asset_file)
        self.image_assets = ImageAssets(self.__paths.image_asset_file)

        self.video_assets = SubVideoAssets(self.__paths.sub_video_asset_file)
        if not self.video_assets.is_complete():
            raise ValueError(
                "Video assets are incomplete. Please ensure all required assets are present."
            )

        self.video_assembler_assets = VideoAssemblerAssets(
            self.__paths.video_assembler_asset_file
        )

        self.effects = MediaEffects(effects_file_path=self.__paths.video_effects_file)

        self.output_path = self.__paths.video_output_file
        self._temp_files = []

    def _cleanup(self):
        """
        Clean up temporary files.
        """
        logger.info(f"Cleaning up {len(self._temp_files)} temporary files")
        for f in self._temp_files:
            file_path = Path(f)
            if file_path.exists():
                logger.debug(f"Removing temporary file: {file_path.name}")
                file_path.unlink()
        logger.info("Cleanup completed")

    def _combine_image_with_audio(self, image_path: str, audio_path: str) -> str:
        """
        Generate a video segment from a image and audio file.
        """
        image_path_obj = Path(image_path)
        temp_file = (
            self.__paths.video_assembler_asset_folder
            / f"temp_{image_path_obj.stem}.mp4"
        )

        output_path = create_video_segment_from_image_and_audio(
            image_path=image_path, audio_path=audio_path, output_path=temp_file
        )

        self._temp_files.append(output_path)
        return output_path

    def _combine_sub_video_with_audio(self, video_path: str, audio_path: str) -> str:
        """
        Generate a video segment from a video and audio file.
        """
        video_path_obj = Path(video_path)
        temp_file = (
            self.__paths.video_assembler_asset_folder
            / f"temp_{video_path_obj.stem}.mp4"
        )

        output_path = create_video_segment_from_sub_video_and_audio_freeze_last_frame(
            sub_video_path=video_path, audio_path=audio_path, output_path=temp_file
        )

        self._temp_files.append(output_path)
        return output_path

    def _compose(self, video_segments: list[Path]):
        """
        Generate a video from a list of images.
        """
        assert len(video_segments) > 0, "No clips to compose."

        logger.info(f"Composing final video from {len(video_segments)} segments")

        # Step 2: Create concat list
        output_video_path = self.output_path.with_stem(f"{self.output_path.stem}_raw")
        raw_video_path = concatenate_videos_with_reencoding(
            video_segments=video_segments, output_path=output_video_path
        )
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

    def _apply_image_effects(self, image_file_paths: list[Path]) -> list[Path]:
        """
        Apply media effects to the image files.
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

        return processed_images

    def _apply_video_effects(self, video_file_paths: list[Path]) -> list[Path]:
        """
        Apply media effects to the video files.
        """
        processed_videos: list[Path] = []
        for image_path, image_effects in zip(
            video_file_paths, self.effects.image_effects
        ):
            processed_video_path = image_path
            for effect in image_effects:
                if effect:
                    processed_video_path = effect.apply(processed_video_path)
                    self._temp_files.append(processed_video_path)
            processed_videos.append(processed_video_path)

        return processed_videos

    def _apply_narrator_effects(self, narrator_file_paths: list[Path]) -> list[Path]:
        """
        Apply media effects to the audio files.
        """
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

        return processed_narrators

    def _create_video_segments_from_images(self) -> list[Path]:
        """
        Create video segments from the assets defined in the video recipe.
        """

        # Extract data from video recipe
        narrator_file_paths = self.narrator_assets.narrator_assets
        image_file_paths = self.image_assets.image_assets

        logger.info(
            f"Processing {len(narrator_file_paths)} audio files and {len(image_file_paths)} image files"
        )

        processed_narrators = self._apply_narrator_effects(narrator_file_paths)
        processed_images = self._apply_image_effects(image_file_paths)

        video_segments = []
        for i, (image_path, audio_path) in enumerate(
            zip(processed_images, processed_narrators), 1
        ):
            logger.info(
                f"Processing segment {i}/{len(narrator_file_paths)}: {Path(image_path).name}"
            )

            video_segment = self._combine_image_with_audio(image_path, audio_path)
            video_segments.append(video_segment)

        logger.info(f"Created {len(video_segments)} video segments")

        return video_segments

    def _move_asset_to_output_path(self, target_path: Path, asset_path: Path) -> Path:
        """Move asset to the database folder and return the new path."""
        if not asset_path.exists():
            logger.warning(
                f"Asset file does not exist while trying to move it: {asset_path}"
            )
            logger.warning("Sometimes ComfyUI return temporary files. Ignoring...")
            return Path("")

        complete_target_path = target_path / asset_path.name
        complete_target_path = safe_move(asset_path, complete_target_path)
        logger.trace(f"Asset moved successfully to: {complete_target_path}")
        return complete_target_path

    def _upscale_and_frame_interp_video_list(
        self, sub_video_file_paths: list[Path]
    ) -> list[Path]:
        """
        Upscale and apply frame interpolation to the video files if needed.
        """
        logger.info(
            f"Upscaling and frame interpolating {len(sub_video_file_paths)} videos"
        )
        requests = ComfyUIRequests()

        processed_videos_paths: list[Path] = []
        for index, video_path in enumerate(sub_video_file_paths):
            if self.video_assembler_assets.has_video(index):
                logger.info(
                    f"Video already set for scene {index+1}, skipping upscale and frame interpolation."
                )
                processed_videos_paths.append(
                    self.video_assembler_assets.final_sub_videos[index]
                )
                continue

            comfyui_video_path = copy_media_to_comfyui_input_folder(video_path)

            output_file_name = f"{comfyui_video_path.stem}_upscaled"

            workflow = VideoUpscaleFrameInterpWorkflow()
            workflow.set_video_path(comfyui_video_path.name)
            workflow.set_output_filename(output_file_name)

            processed_videos = requests.comfyui_ensure_send_all_prompts([workflow])
            processed_video_path = Path(processed_videos[0])
            moved_path = self._move_asset_to_output_path(
                self.__paths.video_assembler_asset_folder, processed_video_path
            )
            self.video_assembler_assets.set_final_sub_video_video(index, moved_path)
            processed_videos_paths.append(moved_path)

            delete_media_from_comfyui_input_folder(comfyui_video_path)

        logger.info(
            f"Finished upscaling and frame interpolating videos: {len(sub_video_file_paths)}"
        )

        return processed_videos_paths

    def _upscale_and_frame_interp_sub_videos(
        self, sub_video_file_paths: list[list[Path]]
    ) -> list[Path]:
        """
        Upscale and apply frame interpolation to the video files if needed.
        """
        logger.info(
            f"Upscaling and frame interpolating {len(sub_video_file_paths)} videos"
        )

        scalled_fragments: list[Path] = []

        for sublist in sub_video_file_paths:
            logger.info(f"Sublist with {len(sublist)} videos")

            scalled_sub_videos = self._upscale_and_frame_interp_video_list(sublist)

            first_in_sublist = scalled_sub_videos[0]
            output_file_path = first_in_sublist.with_stem(
                f"{first_in_sublist.stem}_upscaled_and_concatenated"
            )
            contatenated_scalled_sub_videos = concatenate_videos_no_reencoding(
                video_segments=scalled_sub_videos,
                output_path=output_file_path,
            )
            scalled_fragments.append(contatenated_scalled_sub_videos)
            self._temp_files.append(contatenated_scalled_sub_videos)

        return scalled_fragments

    def _create_video_segments_from_sub_videos(self):
        """
        Create video segments from the sub-videos defined in the video recipe.
        """

        # Extract data from video recipe
        narrator_file_paths = self.narrator_assets.narrator_assets
        sub_video_file_paths = self.video_assets.sub_video_assets
        video_file_paths = self.video_assets.assembled_sub_video

        logger.info(
            f"Processing {len(narrator_file_paths)} audio files and {len(sub_video_file_paths)} video files"
        )

        # processed_videos = self._upscale_and_frame_interp_sub_videos(
        #    sub_video_file_paths
        # )
        processed_videos = self._upscale_and_frame_interp_video_list(video_file_paths)

        processed_videos = self._apply_video_effects(processed_videos)
        processed_narrators = self._apply_narrator_effects(narrator_file_paths)

        video_segments = []
        for i, (video_path, audio_path) in enumerate(
            zip(processed_videos, processed_narrators), 1
        ):
            logger.info(
                f"Processing segment {i}/{len(narrator_file_paths)}: {Path(video_path).name}"
            )

            video_segment = self._combine_sub_video_with_audio(video_path, audio_path)
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
            log_level="TRACE",
            name="assemble_final_video",
            base_folder=self.__paths.chapter_folder,
        ):
            logger.info("Starting video assembly process")

            # video_segments = self._create_video_segments_from_images()
            video_segments = self._create_video_segments_from_sub_videos()
            self._compose(video_segments)

            self._cleanup()

            logger.info(f"Video assembly completed successfully: {self.output_path}")

    def clean_unused_assets(self):
        """Clean up video assets for a specific story folder."""

        logger.info("Starting video asset cleanup process")

        assets_to_keep = [
            asset
            for asset in self.video_assembler_assets.final_sub_videos
            if asset is not None
        ]

        for file in self.__paths.video_assembler_asset_folder.glob("*"):
            if file.is_file():
                if file in assets_to_keep:
                    continue
                file.unlink()
                logger.info(f"Deleted asset file: {file}")

        logger.info("Video asset cleanup process completed successfully")
