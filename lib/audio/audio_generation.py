"""
Audio Generation Module
"""

import pyttsx3


class AudioGenerator:
    """
    A class to generate audio from text using pyttsx3.
    """

    def __init__(self):
        """
        Initialize the AudioGenerator class and configure the pyttsx3 engine.
        """
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 150)  # Set speech rate
        self.engine.setProperty("volume", 1.0)  # Set volume (0.0 to 1.0)

    def text_to_audio(self, text: str, output_path: str) -> None:
        """
        Convert the given text to audio and save it to the specified file.

        :param text: The text to convert to audio.
        :param output_path: The path to save the generated audio file.
        """
        self.engine.save_to_file(text, output_path)
        self.engine.runAndWait()
