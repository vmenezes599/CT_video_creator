"""
Video Generation Module
"""

from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips


class VideoGenerator:
    """
    A class to generate a video from a list of images.
    """

    def __init__(self):
        """
        Initialize the VideoGenerator class.

        :param duration_per_image: Duration (in seconds) each image will be displayed.
        """
        self.clips: list[ImageClip] = []  # List to hold ImageClip objects

    def add_image(self, image_path: str, image_duration: int = 4) -> None:
        """
        Generate a video from a list of images.

        :param image_paths: List of paths to the images.
        :param image_duration: Duration (in seconds) each image will be displayed.
        """
        clip = ImageClip(image_path)

        clip = clip.with_duration(image_duration)

        self.clips.append(clip)

    def compose(self, output_path: str):
        """
        Generate a video from a list of images.
        """
        # Concatenate all the ImageClips into a single video
        video = concatenate_videoclips(clips=self.clips)

        # Write the video to the output file
        video.write_videofile(output_path, fps=24, codec="libx264")
