"""
Audio Generation Module
"""
import os

from .audio_generation import AudioGenerator


def main():
    """
    Main function to generate audio from text.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    generator = AudioGenerator()
    generator.text_to_audio("Hello, this is a test audio.", f"{current_dir}/output_audio.mp3")


if __name__ == "__main__":
    main()
