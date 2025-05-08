"""
Video Generation Module
"""
import os

from .video_generation import VideoGenerator


def main():
    """ "
    Main function to generate a video from a list of images.
    """
    # Example list of image paths
    current_dir = os.path.dirname(os.path.abspath(__file__))

    image_paths = [
        f"{current_dir}/test_pictures/1.png",
        f"{current_dir}/test_pictures/2.png",
        f"{current_dir}/test_pictures/3.png",
        f"{current_dir}/test_pictures/4.png",
        f"{current_dir}/test_pictures/5.png",
        f"{current_dir}/test_pictures/6.png",
        f"{current_dir}/test_pictures/7.png",
        f"{current_dir}/test_pictures/8.png",
    ]

    # Output video path
    output_path = f"{current_dir}/video_generation_test.mp4"

    # Duration each image will be displayed (in seconds)
    duration_per_image = 3

    # Create an instance of VideoGenerator
    video_generator = VideoGenerator()

    # Generate the video
    for image_path in image_paths:
        # Add each image to the video generator
        video_generator.add_image(image_path, duration_per_image)

    video_generator.compose(output_path)


if __name__ == "__main__":
    main()
