"""
Video Creator Module

This module contains the VideoCreator class that orchestrates the entire video creation process
by coordinating image generation, audio generation, and video composition.
"""

from pathlib import Path

from logging_utils import logger

from ct_video_creator.comfyui import ComfyUIRequests
from ct_video_creator.modules.background_music import BackgroundMusicAssets, BackgroundMusicAsset
from ct_video_creator.modules.sub_video import SubVideoAssets
from ct_video_creator.modules.narrator import NarratorAssets
from ct_video_creator.modules.image import ImageAssets
from ct_video_creator.generators import ZonosTTSRecipe
from ct_video_creator.comfyui import VideoUpscaleFrameInterpWorkflow
from ct_video_creator.generators import SubtitleGenerator
from ct_video_creator.utils import (  # pylint: disable=unused-import
    burn_subtitles_to_video,
    create_video_segment_from_sub_video_and_audio_freeze_last_frame,
    create_video_segment_from_sub_video_and_audio_reverse_video,
    create_video_segment_from_image_and_audio,
    concatenate_audio_with_silence_inbetween,
    concatenate_videos_with_fade_in_out,
    concatenate_videos_with_reencoding,
    blit_overlay_video_onto_main_video,
    concatenate_videos_no_reencoding,
    add_background_music_to_video,
    reencode_to_reference_basic,
    get_media_resolution,
    get_media_duration,
    safe_move,
    VideoCreatorPaths,
    VideoBlitPosition,
)

from .video_assembler_recipe import VideoAssemblerRecipe, VideoEndingRecipe
from .video_assembler_assets import VideoAssemblerAssets


class VideoAssembler:
    """
    A class that orchestrates the video creation process by coordinating
    image generation, audio generation, and video composition.
    """

    DEFAULT_WIDTH = 1920
    DEFAULT_HEIGHT = 1080

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """
        Initialize VideoCreator with the required generators.
        """
        self._paths = video_creator_paths

        self._subtitle_generator = SubtitleGenerator()

        # Load separate narrator and image assets
        self.background_music_assets = BackgroundMusicAssets(video_creator_paths)
        self.narrator_assets = NarratorAssets(video_creator_paths)
        self.image_assets = ImageAssets(video_creator_paths)

        self.video_assets = SubVideoAssets(video_creator_paths)
        if not self.video_assets.is_complete():
            raise ValueError("Video assets are incomplete. Please ensure all required assets are present.")

        self.video_assembler_assets = VideoAssemblerAssets(video_creator_paths)

        self.video_assembler_recipe = VideoAssemblerRecipe(self._paths)

        self.output_path = self._paths.video_output_file
        self.subtitle_file: Path | None = None

        self._temp_folder = self._paths.video_assembler_asset_folder / "temp_files"
        self._temp_folder.mkdir(parents=True, exist_ok=True)
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

        for f in self._temp_folder.iterdir():
            f.unlink()
            logger.debug(f"Removing temporary file: {f.name}")

        self._temp_folder.rmdir()
        logger.info("Cleanup completed")

    def _combine_image_with_audio(self, image_path: str, audio_path: str) -> str:
        """
        Generate a video segment from a image and audio file.
        """
        image_path_obj = Path(image_path)
        temp_file = self._temp_folder / f"{image_path_obj.stem}_with_audio.mp4"

        output_path = create_video_segment_from_image_and_audio(
            image_path=image_path, audio_path=audio_path, output_path=temp_file
        )

        self._temp_files.append(output_path)
        return output_path

    def _get_desired_video_resolution(self, video_path: Path) -> tuple[int, int]:
        """
        Get the desired video resolution from the recipe.
        """
        width = self.DEFAULT_WIDTH
        height = self.DEFAULT_HEIGHT

        video_width, video_height = get_media_resolution(video_path)
        if video_height > video_width:
            width = self.DEFAULT_HEIGHT
            height = self.DEFAULT_WIDTH
        return width, height

    def _combine_sub_video_with_audio(self, video_path: Path, audio_path: Path) -> Path:
        """
        Generate a video segment from a video and audio file.
        """
        temp_file_base = f"{video_path.stem}_with_audio"
        temp_file = self._temp_folder / f"{temp_file_base}.mp4"
        index = 1
        while temp_file.exists():
            temp_file = temp_file.with_stem(f"{temp_file_base}_{index}")
            index += 1

        width, height = self._get_desired_video_resolution(video_path)

        output_path = create_video_segment_from_sub_video_and_audio_freeze_last_frame(
            sub_video_path=video_path, audio_path=audio_path, output_path=temp_file, width=width, height=height
        )

        return output_path

    def _compose(self, video_segments: list[Path]):
        """
        Generate a video from a list of images.
        """
        assert len(video_segments) > 0, "No clips to compose."

        output_video_path = self._temp_folder / f"{self.output_path.stem}_composed{self.output_path.suffix}"

        logger.info(f"Composing final video from {len(video_segments)} segments")

        width, height = self._get_desired_video_resolution(video_segments[0])

        return concatenate_videos_with_fade_in_out(
            video_segments=video_segments, output_path=output_video_path, width=width, height=height
        )

    def _apply_narrator_effects(self, narrator_file_paths: list[Path]) -> list[Path]:
        """
        Apply media effects to the audio files.
        """
        processed_narrators: list[Path] = []
        for index, audio_path in enumerate(narrator_file_paths):
            audio_effects = self.video_assembler_recipe.get_narrator_effects(index)
            processed_narrator_path = audio_path
            for effect in audio_effects:
                if effect:
                    processed_narrator_path = effect.apply(processed_narrator_path, self._temp_folder)
                    self._temp_files.append(processed_narrator_path)
            processed_narrators.append(processed_narrator_path)

        return processed_narrators

    def _move_asset_to_output_path(self, target_path: Path, asset_path: Path) -> Path:
        """Move asset to the database folder and return the new path."""
        if not asset_path.exists():
            logger.warning(f"Asset file does not exist while trying to move it: {asset_path}")
            logger.warning("Sometimes ComfyUI return temporary files. Ignoring...")
            return Path("")

        complete_target_path = target_path / asset_path.name
        complete_target_path = safe_move(asset_path, complete_target_path)
        logger.trace(f"Asset moved successfully to: {complete_target_path}")
        return complete_target_path

    def _upscale_and_frame_interp_video_list(self, sub_video_file_paths: list[Path]) -> list[Path]:
        """
        Upscale and apply frame interpolation to the video files if needed.
        """
        logger.info(f"Upscaling and frame interpolating {len(sub_video_file_paths)} videos")
        requests = ComfyUIRequests()

        processed_videos_paths: list[Path] = []
        for index, video_path in enumerate(sub_video_file_paths):
            if self.video_assembler_assets.has_video(index):
                logger.info(f"Video already set for scene {index+1}, skipping upscale and frame interpolation.")
                processed_videos_paths.append(self.video_assembler_assets.final_sub_videos[index])
                continue

            comfyui_video_path = requests.upload_file(video_path)

            output_file_name = f"{comfyui_video_path.stem}_upscaled"

            workflow = VideoUpscaleFrameInterpWorkflow()
            workflow.set_video_path(comfyui_video_path.name)
            workflow.set_output_filename(output_file_name)

            result_files = requests.ensure_send_all_prompts([workflow], self._paths.video_assembler_asset_folder)
            processed_video_path = Path(result_files[0]) if result_files else None

            self.video_assembler_assets.set_final_sub_video_video(index, processed_video_path)
            processed_videos_paths.append(processed_video_path)

        logger.info(f"Finished upscaling and frame interpolating videos: {len(sub_video_file_paths)}")

        return processed_videos_paths

    def _combine_video_with_audio(self, video_segments: list[Path], audio_segments: list[Path]) -> list[Path]:
        """
        Create video segments from the sub-videos defined in the video recipe.
        """

        processed_narrators = self._apply_narrator_effects(audio_segments)

        results = []
        for i, (video_path, audio_path) in enumerate(zip(video_segments, processed_narrators), 1):
            logger.info(f"Processing segment {i}/{len(audio_segments)}: {Path(video_path).name}")

            video_segment = self._combine_sub_video_with_audio(video_path, audio_path)
            self._temp_files.append(video_segment)
            results.append(video_segment)

        logger.info(f"Created {len(results)} video segments")

        return results

    def _add_intro_video_segment(self, video_segments: list[Path]) -> list[Path]:
        """
        Add intro video segment to the list of video segments if defined.
        """
        intro_recipe = self.video_assembler_recipe.get_video_intro_recipe()
        if not intro_recipe:
            logger.info("No intro recipe defined, skipping intro video segment.")
            return video_segments

        intro_video_path = intro_recipe.intro_asset
        if not intro_video_path or not intro_video_path.exists():
            logger.warning("Intro video path is invalid or does not exist.")
            return video_segments

        reencoded_intro = intro_video_path

        logger.info(f"Adding intro video segment: {intro_video_path.name}")

        return [reencoded_intro, *video_segments]

    def _generate_ending_narrators(self, ending_recipe: VideoEndingRecipe) -> list[Path]:
        """
        Generate ending narrators if they are missing.
        """
        logger.info("Generating ending narrators")

        narrator_text_list = ending_recipe.narrator_text_list
        clone_voice_path = ending_recipe.narrator_clone_voice
        seed = ending_recipe.seed

        base_name = "video_assembler_ending_narrator"
        output_path_base = self._temp_folder / f"{base_name}.mp3"

        generated_audio_paths = []
        for index, narrator_text in enumerate(narrator_text_list):
            recipe = ZonosTTSRecipe(prompt=narrator_text, seed=seed, clone_voice_path=clone_voice_path)
            output_name = output_path_base.with_stem(f"{base_name}_{index + 1}")
            tts_generator = ZonosTTSRecipe.GENERATOR_TYPE()
            generated_audio = tts_generator.clone_text_to_speech(recipe=recipe, output_file_path=output_name)

            self._temp_files.append(generated_audio)
            generated_audio_paths.append(generated_audio)

        logger.info("Finished generating ending narrators")

        return generated_audio_paths

    def _concatenate_ending_narrators(self, narrator_path_list: list[Path]) -> Path:
        """
        Concatenate ending narrators into a single audio file.
        """
        logger.info("Concatenating ending narrators")

        concatenated_narrator_path = self._temp_folder / "ending_narrator_concatenated.mp3"

        concatenated_narrator_path = concatenate_audio_with_silence_inbetween(
            narrator_path_list, concatenated_narrator_path
        )

        self._temp_files.append(concatenated_narrator_path)
        logger.info("Finished concatenating ending narrators")
        return concatenated_narrator_path

    def _add_ending_video_segment(
        self, video_segments: list[Path], video_segments_without_audio: list[Path]
    ) -> list[Path]:
        """
        Add ending video segment to the list of video segments if defined.
        """
        ending_sub_video = self.video_assembler_assets.video_ending
        if ending_sub_video and ending_sub_video.exists():
            logger.info(f"Using existing ending video segment: {ending_sub_video.name}")
            return [*video_segments, ending_sub_video]

        ending_recipe = self.video_assembler_recipe.get_video_ending_recipe()
        if not ending_recipe:
            logger.info("No ending recipe defined, skipping ending video segment.")
            return video_segments

        if not ending_recipe.narrator_text_list or len(ending_recipe.narrator_text_list) == 0:
            logger.info("No ending narrator defined, skipping ending video segment.")
            return video_segments

        ending_video_path = ending_recipe.sub_video
        if not ending_video_path or not ending_video_path.exists():
            logger.warning("Ending video path 'None'. Setting to first video segment.")
            ending_video_path = video_segments_without_audio[0]
            self.video_assembler_recipe.set_video_ending_subvideo(ending_video_path)

        ending_narrator_paths = self._generate_ending_narrators(ending_recipe)

        concatenated_narrator_path = self._concatenate_ending_narrators(ending_narrator_paths)

        ending_sub_video = self._combine_sub_video_with_audio(ending_video_path, concatenated_narrator_path)

        previous_medias_length = 0.0
        target_index = ending_recipe.ending_overlay_start_narrator_index - 1
        for index in range(target_index):
            previous_narrator = ending_narrator_paths[index]
            previous_medias_length += get_media_duration(previous_narrator)

        start_time_seconds = previous_medias_length + ending_recipe.ending_start_delay_seconds

        output_path = (
            self._paths.video_assembler_asset_folder / f"{self.output_path.stem}_ending{self.output_path.suffix}"
        )
        if ending_recipe.ending_overlay_asset:

            self._temp_files.append(ending_sub_video)

            ending_sub_video = blit_overlay_video_onto_main_video(
                overlay_video=ending_recipe.ending_overlay_asset,
                main_video=ending_sub_video,
                output_path=output_path,
                position=VideoBlitPosition.CENTER,
                scale_percent=1.0,
                start_time_seconds=start_time_seconds,
                allow_extend_duration=True,
            )
        else:
            ending_sub_video = ending_sub_video.rename(output_path)

        self.video_assembler_assets.set_video_ending(ending_sub_video)

        logger.info("Created ending video segment.")

        return [*video_segments, ending_sub_video]

    def _add_overlay_to_video(self, video_path: Path) -> Path:
        """
        Apply post-compose effects to the final video.
        """

        overlay_recipe = self.video_assembler_recipe.get_video_overlay_recipe()
        if not overlay_recipe:
            logger.info("No outro effects defined, skipping post-compose effects.")
            return video_path

        overlay_asset_path = overlay_recipe.overlay_asset
        if not overlay_asset_path or not overlay_asset_path.exists():
            logger.warning("Overlay video path is invalid or does not exist.")
            return video_path

        logger.info(f"Adding outro video segment: {overlay_asset_path.name}")

        output_video_path = self._temp_folder / f"{self.output_path.stem}_with_overlay{self.output_path.suffix}"
        self._temp_files.append(video_path)

        output_path = blit_overlay_video_onto_main_video(
            overlay_video=overlay_asset_path,
            main_video=video_path,
            output_path=output_video_path,
            start_time_seconds=overlay_recipe.start_time_seconds,
            repeat_every_seconds=overlay_recipe.interval_seconds,
        )

        return output_path

    def _generate_background_music_duration_dict(self, video_segments: list[Path]) -> list[dict]:
        """
        Get a dictionary of background music asset paths and their durations.
        """
        background_music_assets = self.background_music_assets.background_music_assets

        if video_segments[0] == self.video_assembler_recipe.get_video_intro_recipe().intro_asset:
            # Intro has no background music
            background_music_assets = [BackgroundMusicAsset("", 0.0, True), *background_music_assets]

        if video_segments[-1] == self.video_assembler_assets.video_ending:
            background_music_assets = [*background_music_assets, background_music_assets[-1]]

        assert len(background_music_assets) >= len(
            video_segments
        ), "Background music must be bigger or equal length than video_segments."

        duration_dict: list[tuple[BackgroundMusicAsset, float]] = []
        previous_bgm_asset = None
        for bgm_asset, video_segment in zip(background_music_assets, video_segments):

            if bgm_asset.skip:
                active_bgm_asset = None
            else:
                active_bgm_asset = bgm_asset.asset

            if active_bgm_asset is None:
                active_bgm_asset = ""

            if previous_bgm_asset == active_bgm_asset:
                duration_dict[-1] = (duration_dict[-1][0], duration_dict[-1][1] + get_media_duration(video_segment))
            else:
                duration_dict.append((bgm_asset, get_media_duration(video_segment)))
                previous_bgm_asset = active_bgm_asset

        result = []
        beginning = 0.0
        for item in duration_dict:
            if item[0].asset:
                result.append(
                    {
                        "asset": item[0].asset,
                        "start_time": beginning,
                        "duration": item[1],
                        "end_time": beginning + item[1],
                        "volume": item[0].volume,
                    }
                )
            beginning += item[1]

        return result

    def _add_background_music_to_video(self, video_path: Path, video_segments: list[Path]) -> Path:
        """
        Add background music to the final video.
        """
        background_music_assets = self.background_music_assets.background_music_assets
        if not background_music_assets:
            logger.info("No background music recipe defined, skipping background music addition.")
            return video_path

        music_duration_dict = self._generate_background_music_duration_dict(video_segments)

        output_path = self._temp_folder / f"{self.output_path.stem}_bgm{self.output_path.suffix}"

        music_assets = [segment["asset"] for segment in music_duration_dict]
        start_times = [segment["start_time"] for segment in music_duration_dict]
        durations = [segment["duration"] for segment in music_duration_dict]
        volumes = [segment["volume"] for segment in music_duration_dict]

        output_path = add_background_music_to_video(
            video_path=video_path,
            music_assets=music_assets,
            start_times=start_times,
            durations=durations,
            volumes=volumes,
            output_path=output_path,
            main_audio_volume=1.0,
        )

        self._temp_files.append(video_path)

        return output_path

    def _pre_process(self) -> list[Path]:
        """
        Pre-process video segments before composition.
        """
        # Currently a placeholder for any pre-processing steps needed
        logger.info("Pre-processing video segments before composition")

        video_segments: list[Path] = self.video_assets.assembled_sub_videos
        audio_segments: list[Path] = self.narrator_assets.narrator_assets

        video_segments = self._upscale_and_frame_interp_video_list(video_segments)
        video_segments_without_audio = video_segments.copy()
        video_segments = self._combine_video_with_audio(video_segments, audio_segments)

        if not self.video_assembler_recipe.get_video_ending_recipe().skip:
            video_segments = self._add_ending_video_segment(video_segments, video_segments_without_audio)

        if not self.video_assembler_recipe.get_video_intro_recipe().skip:
            video_segments = self._add_intro_video_segment(video_segments)

        return video_segments

    def _post_process(self, video_path: Path, video_segments: list[Path]) -> Path:
        """
        Apply post-compose effects to the final video.
        """
        output_path = video_path

        output_path = self._add_background_music_to_video(video_path, video_segments)

        if not self.video_assembler_recipe.get_video_overlay_recipe().skip:
            output_path = self._add_overlay_to_video(output_path)

        return output_path

    def _subtitle_process(self, video_path: Path) -> Path:
        """
        Generate and burn subtitles into the final video.
        """
        subtitle_recipe = self.video_assembler_recipe.get_subtitle_recipe()

        if not subtitle_recipe:
            logger.info("No subtitle recipe defined, skipping subtitle generation.")
            return video_path

        if subtitle_recipe.skip:
            logger.info("Subtitle generation is skipped as per the recipe.")
            return video_path

        ass_subtitle, self.subtitle_file = self._subtitle_generator.generate_subtitles_from_audio(
            video_path=video_path,
            word_level=subtitle_recipe.word_level_timestamps,
            segment_level=subtitle_recipe.segment_level_timestamps,
            font_size=subtitle_recipe.font_size,
            position=subtitle_recipe.position,
            margin=subtitle_recipe.subtitle_margin,
            alignment=subtitle_recipe.alignment,
        )
        self._temp_files.append(ass_subtitle)

        output_file = video_path
        if subtitle_recipe.burn_subtitles_into_video:
            self._temp_files.append(video_path)

            output_file = self._temp_folder / f"{self.output_path.stem}_subtitled{self.output_path.suffix}"
            output_file = burn_subtitles_to_video(
                video_path=video_path,
                subtitle_path=ass_subtitle,
                output_path=output_file,
            )

        return output_file

    def _rename_outputs(self, video_path: Path) -> Path:
        """
        Rename the final output video and subtitle files to match the desired output path.
        """
        output_file = video_path.rename(self.output_path)

        if self.subtitle_file:
            subtitle_target = output_file.with_suffix(self.subtitle_file.suffix)
            self.subtitle_file = self.subtitle_file.rename(subtitle_target)

        return output_file

    def assemble_video(self) -> None:
        """
        Create a video from a video recipe.

        Args:
            video_recipe: VideoRecipe object containing narrator text and visual descriptions
            output_filename: Name of the output video file
        """

        logger.info("Starting video assembly process")

        video_segments = self._pre_process()

        output_file = self._compose(video_segments)

        output_file = self._post_process(output_file, video_segments)

        output_file = self._subtitle_process(output_file)

        output_file = self._rename_outputs(output_file)

        self._cleanup()

        logger.info(f"Video assembly completed successfully: {output_file.name}")
