"""
Video Creator Module

This module contains the VideoCreator class that orchestrates the entire video creation process
by coordinating image generation, audio generation, and video composition.
"""

from pathlib import Path
import ffmpeg

from ai_video_creator.generators import SubtitleGenerator

from .video_recipe_paths import VideoRecipePaths
from .video_asset_manager import VideoAssets


class VideoAssembler:
    """
    A class that orchestrates the video creation process by coordinating
    image generation, audio generation, and video composition.
    """

    def __init__(self, story_folder: Path, chapter_index: int):
        """
        Initialize VideoCreator with the required generators.
        """
        self.__paths = VideoRecipePaths(story_folder, chapter_index)
        self.__subtitle_generator = SubtitleGenerator()

        self.assets = VideoAssets(self.__paths.video_asset_file)
        self.output_path = self.__paths.video_output_file
        self._temp_files = []

    def __get_audio_duration(self, path: str) -> float:
        """
        Get the duration of an audio file using ffmpeg.probe
        """
        probe = ffmpeg.probe(path)
        duration = float(probe["format"]["duration"])
        return duration

    def _generate_image_audio_video_segment(
        self, image_path: str, audio_path: str
    ) -> str:
        """
        Generate a video segment from an image and audio file.
        """
        image_path_obj = Path(image_path)
        temp_file = Path(f"temp_{image_path_obj.stem}.ts")
        duration = self.__get_audio_duration(audio_path)
        video_input = ffmpeg.input(image_path, loop=1, t=duration)
        audio_input = ffmpeg.input(audio_path)
        if not temp_file.exists():
            (
                ffmpeg.output(
                    video_input,
                    audio_input,
                    temp_file.name,
                    r=24,  # Frame rate
                    vf="scale=1280:720",  # Ensure 720p resolution
                    f="mpegts",  # Use MPEG-TS format for concatenation
                    shortest=None,
                    **{
                        "c:v": "h264_nvenc",  # Re-encode video to H.264
                        "preset": "p5",  # Encoding speed/quality tradeoff
                        "crf": "23",  # Video quality (lower is better, 18–28 range)
                        "c:a": "aac",  # Audio codec
                        "pix_fmt": "yuv420p",
                    },
                )
                .overwrite_output()
                .run()
            )

        self._temp_files.append(temp_file)
        return temp_file

    def _compose(self, video_segments: list[str]):
        """
        Generate a video from a list of images.
        """
        # Concatenate all the ImageClips into a single video

        assert len(video_segments) > 0, "No clips to compose."

        # Step 2: Create concat list
        concat_list_path = "concat_list.txt"
        if len(video_segments) > 1:
            with open(concat_list_path, "w", encoding="utf-8") as f:
                for path in video_segments:
                    f.write(f"file '{Path(path).resolve()}'\n")

            self._temp_files.append(concat_list_path)

            if not self.output_path.exists():
                (
                    ffmpeg.input(concat_list_path, format="concat", safe=0)
                    .output(
                        str(self.output_path), c="copy", **{"bsf:a": "aac_adtstoasc"}
                    )
                    .overwrite_output()
                    .run()
                )
            self._temp_files.append(self.output_path)
        elif len(video_segments) == 1:
            Path(video_segments[0]).rename(self.output_path)

        # Generate subtitles using SubtitleGenerator
        self.__subtitle_generator.generate_and_add_subtitles(self.output_path)

        for f in self._temp_files:
            file_path = Path(f)
            if file_path.exists():
                file_path.unlink()

    def assemble_video(self) -> None:
        """
        Create a video from a video recipe.

        Args:
            video_recipe: VideoRecipe object containing narrator text and visual descriptions
            output_filename: Name of the output video file
        """
        # Extract data from video recipe
        audio_prompts = self.assets.narrator_list
        visual_prompts = self.assets.image_list

        video_segments = []
        for image_path, audio_path in zip(visual_prompts, audio_prompts):
            video_segment = self._generate_image_audio_video_segment(
                image_path, audio_path
            )
            video_segments.append(video_segment)

        self._compose(video_segments)
