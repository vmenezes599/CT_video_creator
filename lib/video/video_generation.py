"""
Video Generation Module
"""

import os
import subprocess
from pathlib import Path

import ffmpeg
import pysrt


class VideoGenerator:
    """
    A class to generate a video from a list of images.
    """

    def __init__(self):
        """
        Initialize the VideoGenerator class.

        :param duration_per_image: Duration (in seconds) each image will be displayed.
        """
        self.clips: list[str] = []  # List to hold video clips
        self.subtitles_data: list[tuple[str, float]] = (
            []
        )  # List to hold subtitles and their durations
        self.temp_files: list[str] = []  # List to hold temporary files

    def _format_timestamp(self, seconds: float) -> str:
        """
        Convert seconds to 'HH:MM:SS,mmm' format.
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    def _generate_subtitle(self, output_path: str):
        """
        Generate an SRT file from a list of subtitles and durations.

        :param subtitles: List of subtitle strings.
        :param durations: List of durations for each subtitle (in seconds).
        :param output_path: Path to output .srt file.
        """
        subs = pysrt.SubRipFile()
        current_time = 0.0

        for i, (text, duration) in enumerate(self.subtitles_data, start=1):
            start = self._format_timestamp(current_time)
            end = self._format_timestamp(current_time + duration)
            subs.append(pysrt.SubRipItem(index=i, start=start, end=end, text=text))
            current_time += duration

        path_split = os.path.splitext(output_path)
        srt_output_path = path_split[0] + ".srt"
        subs.save(srt_output_path, encoding="utf-8")

        self.temp_files.append(srt_output_path)

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                output_path,
                "-vf",
                f"subtitles={srt_output_path}",
                f"{path_split[0]}_subtitled{path_split[1]}",
            ],
            check=True,
        )

    def _get_audio_duration(self, path: str) -> float:
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
        temp_file = f"temp_{os.path.splitext(os.path.basename(image_path))[0]}.mp4"
        duration = self._get_audio_duration(audio_path)
        video_input = ffmpeg.input(image_path, loop=1, t=duration)
        audio_input = ffmpeg.input(audio_path)
        (
            ffmpeg.output(
                video_input,
                audio_input,
                temp_file,
                r=24,
                vf="scale=1280:720",
                **{"c:v": "libx264", "c:a": "aac"},
            )
            .overwrite_output()
            .run()
        )

        self.temp_files.append(temp_file)
        return temp_file

    def add_scene(self, image_path: str, audio_path: str, subtitle: str) -> None:
        """
        Generate a video from a list of images.
        """

        video_audio_segment = self._generate_image_audio_video_segment(
            image_path, audio_path
        )

        self.subtitles_data.append((subtitle, self._get_audio_duration(audio_path)))
        self.clips.append(video_audio_segment)

    def add_all_scenes(
        self, image_paths: list[str], audio_paths: list[str], subtitles: list[str]
    ) -> None:
        """
        Generate a video from a list of images.

        :param image_paths : List of paths to the images.
        :param audio_paths: List of paths to the audio files.
        :param image_duration: Duration (in seconds) each image will be displayed.
        """
        assert len(image_paths) == len(
            audio_paths
        ), "Image and audio lists must be of the same length."

        for image_path, audio_path, subtitle in zip(
            image_paths, audio_paths, subtitles
        ):
            self.add_scene(image_path, audio_path, subtitle)

    def compose(self, output_path: str):
        """
        Generate a video from a list of images.
        """
        # Concatenate all the ImageClips into a single video

        assert len(self.clips) > 0, "No clips to compose."

        # Step 2: Create concat list
        with open("concat_list.txt", "w", encoding="utf-8") as f:
            for path in self.clips:
                f.write(f"file '{Path(path).resolve()}'\n")

        self.temp_files.append("concat_list.txt")

        subprocess.run(
            [
                "ffmpeg",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                "concat_list.txt",
                "-c",
                "copy",
                output_path,
            ],
            check=True,
        )
        self.temp_files.append(output_path)

        self._generate_subtitle(output_path)

        for f in self.temp_files:
            os.remove(f)
