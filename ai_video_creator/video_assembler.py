"""
Video Creator Module

This module contains the VideoCreator class that orchestrates the entire video creation process
by coordinating image generation, audio generation, and video composition.
"""

from pathlib import Path
import ffmpeg

from .video_asset_manager import VideoAssetManager


class VideoAssembler:
    """
    A class that orchestrates the video creation process by coordinating
    image generation, audio generation, and video composition.
    """

    def __init__(self, asset_manager: VideoAssetManager):
        """
        Initialize VideoCreator with the required generators.
        """
        self.asset_manager = asset_manager
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
        temp_file = Path(f"temp_{image_path_obj.stem}.mp4")
        duration = self.__get_audio_duration(audio_path)
        video_input = ffmpeg.input(image_path, loop=1, t=duration)
        audio_input = ffmpeg.input(audio_path)
        ffmpeg.output(
            video_input,
            audio_input,
            temp_file.name,
            r=24,  # Frame rate
            vf="scale=1280:720",  # Ensure 720p resolution
            **{
                "c:v": "libx264",  # Re-encode video to H.264
                "preset": "fast",  # Encoding speed/quality tradeoff
                "crf": "23",  # Video quality (lower is better, 18–28 range)
                "c:a": "aac",  # Audio codec
                "movflags": "+faststart",  # Ensures proper mobile streaming
                "pix_fmt": "yuv420p",
            },
        ).overwrite_output().run()

        self._temp_files.append(temp_file)
        return temp_file

    def _compose(
        self, video_segments: list[str], output_path: Path, output_filename: str
    ):
        """
        Generate a video from a list of images.
        """
        # Concatenate all the ImageClips into a single video

        assert len(self._clips) > 0, "No clips to compose."

        # Step 2: Create concat list
        concat_list_path = "concat_list.txt"
        if len(self._clips) > 1:
            with open(concat_list_path, "w", encoding="utf-8") as f:
                for path in self._clips:
                    f.write(f"file '{Path(path).resolve()}'\n")

            self._temp_files.append(concat_list_path)

            (
                ffmpeg.input(concat_list_path, format="concat", safe=0)
                .output(output_path, c="copy")
                .overwrite_output()
                .run()
            )
            self._temp_files.append(output_path)
        elif len(self._clips) == 1:
            Path(self._clips[0]).rename(output_path)

        # Generate subtitles using SubtitleGenerator
        self.__subtitle_generator.generate_and_add_subtitles(output_path)

        for f in self._temp_files:
            file_path = Path(f)
            if file_path.exists():
                file_path.unlink()

    def create_video_from_recipe(self, output_filename: str) -> None:
        """
        Create a video from a video recipe.

        Args:
            video_recipe: VideoRecipe object containing narrator text and visual descriptions
            output_filename: Name of the output video file
        """
        if not video_recipe.voice_audios or not video_recipe.visual_description:
            raise ValueError(
                "Video recipe cannot have empty narrator or visual_description"
            )

        if len(video_recipe.voice_audios) != len(video_recipe.visual_description):
            raise ValueError(
                "Narrator and visual_description lists must have the same length"
            )

        # Extract data from video recipe
        audio_prompts = video_recipe.voice_audios
        visual_prompts = video_recipe.visual_description

        video_segments = []
        for image_path, audio_path in zip(image_files, audio_files):
            video_segment = self._generate_image_audio_video_segment(
                image_path, audio_path
            )
            video_segments.append(video_segment)

        self._compose(video_segments, output_path, output_filename)

    def create_video_from_single_scene(
        self,
        narrator_text: str,
        visual_description: str,
        output_path: Path,
        output_filename: str,
    ) -> None:
        """
        Create a video from a single scene.

        Args:
            narrator_text: Single narrator text
            visual_description: Single visual description
            output_filename: Name of the output video file
        """
        video_recipe = VideoRecipe(
            narrator=[narrator_text], visual_description=[visual_description]
        )
        self.create_video_from_recipe(video_recipe, output_path, output_filename)
