"""
Video Generation Module
"""

import os
from pathlib import Path

import ffmpeg
import stable_whisper

# Stable Whisper Model Sizes
# Model	        Size on Disk	VRAM/Memory Needed	Speed	    Accuracy	Use Case
# tiny	        ~39 MB	        ~1 GB	            Very Fast	Low	        Quick drafts, short/simple audio
# base	        ~74 MB	        ~1.5 GB	            Fast	    Decent	    Podcasts, phone recordings
# small	        ~244 MB	        ~2.5 GB	            Moderate	Good	    General transcription
# medium	    ~769 MB	        ~5 GB	            Slower	    Very Good	Accurate transcriptions, most content
# large-v2/v3	~1.5 GB	        ~8–10 GB+	        Slowest	    Best	    Highest accuracy, multi-language, long files


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

    def _generate_subtitle(self, video_path: str):
        """
        Generate an SRT file from the audio and adds it to the video.

        :param video_path: Path to output .srt file.
        """
        video_path_split = video_path.split(".")

        model = stable_whisper.load_model("medium")

        result = model.transcribe(video_path)

        srt_output_path = f"{video_path_split[0]}.srt"
        stable_whisper.result_to_srt_vtt(result=result, filepath=srt_output_path)

        self.temp_files.append(srt_output_path)

        video_output_path = f"{video_path_split[0]}_subtitled.{video_path_split[1]}"
        (
            ffmpeg.input(video_path)
            .output(
                video_output_path,
                vf=f"subtitles={srt_output_path}",
                **{
                    "c:v": "libx264",
                    "preset": "fast",
                    "crf": "23",
                    "c:a": "aac",
                    "movflags": "+faststart",
                    "pix_fmt": "yuv420p"
                },
            )
            .overwrite_output()
            .run()
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
        ffmpeg.output(
            video_input,
            audio_input,
            temp_file,
            r=24,  # Frame rate
            vf="scale=1280:720",  # Ensure 720p resolution
            **{
                "c:v": "libx264",  # Re-encode video to H.264
                "preset": "fast",  # Encoding speed/quality tradeoff
                "crf": "23",  # Video quality (lower is better, 18–28 range)
                "c:a": "aac",  # Audio codec
                "movflags": "+faststart",  # Ensures proper mobile streaming
                "pix_fmt": "yuv420p"
            },
        ).overwrite_output().run()

        self.temp_files.append(temp_file)
        return temp_file

    def add_scene(self, image_path: str, audio_path: str) -> None:
        """
        Generate a video from a list of images.
        """

        video_audio_segment = self._generate_image_audio_video_segment(
            image_path, audio_path
        )

        self.clips.append(video_audio_segment)

    def add_all_scenes(self, image_paths: list[str], audio_paths: list[str]) -> None:
        """
        Generate a video from a list of images.

        :param image_paths : List of paths to the images.
        :param audio_paths: List of paths to the audio files.
        :param image_duration: Duration (in seconds) each image will be displayed.
        """
        assert len(image_paths) == len(
            audio_paths
        ), "Image and audio lists must be of the same length."

        for image_path, audio_path in zip(image_paths, audio_paths):
            self.add_scene(image_path, audio_path)

    def compose(self, output_path: str):
        """
        Generate a video from a list of images.
        """
        # Concatenate all the ImageClips into a single video

        assert len(self.clips) > 0, "No clips to compose."

        # Step 2: Create concat list
        concat_list_path = "concat_list.txt"
        if len(self.clips) > 1:
            with open(concat_list_path, "w", encoding="utf-8") as f:
                for path in self.clips:
                    f.write(f"file '{Path(path).resolve()}'\n")

            self.temp_files.append(concat_list_path)

            (
                ffmpeg.input(concat_list_path, format="concat", safe=0)
                .output(output_path, c="copy")
                .overwrite_output()
                .run()
            )
            self.temp_files.append(output_path)

        self._generate_subtitle(output_path)

        for f in self.temp_files:
            os.remove(f)
