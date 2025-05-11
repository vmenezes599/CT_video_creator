"""
Audio Generation Module
"""

from abc import ABC, abstractmethod
from typing_extensions import override

import pygame
import pyttsx3
from elevenlabs import save
from elevenlabs.client import ElevenLabs

from .environment_variables import ELEVENLABS_API_KEY


class IAudioGenerator(ABC):
    """
    An interface for audio generation classes.
    """

    @abstractmethod
    def text_to_audio(self, text: str, output_path: str) -> None:
        """
        Convert the given text to audio and save it to the specified file.

        :param text: The text to convert to audio.
        :param output_path: The path to save the generated audio file.
        """

    @abstractmethod
    def play(self, text: str) -> None:
        """
        Play the given text as audio.

        :param text: The text to play as audio.
        """


class Pyttsx3AudioGenerator(IAudioGenerator):
    """
    A class to generate audio from text using pyttsx3.
    """

    def __init__(self):
        """
        Initialize the AudioGenerator class and configure the pyttsx3 engine.
        """
        self.engine = pyttsx3.init()
        self.engine.setProperty(
            "voice",
            "HKEY_LOCAL_MACHINE/SOFTWARE/Microsoft/Speech/Voices/Tokens/TTS_MS_EN-GB_HAZEL_11.0",
        )
        self.engine.setProperty("rate", 150)  # Set speech rate
        self.engine.setProperty("volume", 1.0)  # Set volume (0.0 to 1.0)

    @override
    def text_to_audio(self, text: str, output_path: str) -> None:
        """
        Convert the given text to audio and save it to the specified file.

        :param text: The text to convert to audio.
        :param output_path: The path to save the generated audio file.
        """
        self.engine.save_to_file(text, output_path)
        self.engine.runAndWait()

    @override
    def play(self, text: str) -> None:
        """
        Play the given text as audio.

        :param text: The text to play as audio.
        """
        self.engine.say(text)
        self.engine.runAndWait()

    def set_property(self, args, kwargs):
        """
        Set properties for the pyttsx3 engine.

        :param args: The property name.
        :param kwargs: The property value.
        """
        self.engine.setProperty(args, kwargs)

    def get_property(self, args):
        """
        Get properties from the pyttsx3 engine.

        :param args: The property name.
        :return: The property value.
        """
        return self.engine.getProperty(args)


class ElevenLabsAudioGenerator(IAudioGenerator):
    """
    A class to generate audio from text using ElevenLabs API.
    """

    def __init__(self):
        """
        Initialize the ElevenLabsAudioGenerator class with the provided API key.
        """
        self.client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    @override
    def text_to_audio(self, text: str, output_path: str) -> None:
        """
        Convert the given text to audio and save it to the specified file.

        :param text: The text to convert to audio.
        :param output_path: The path to save the generated audio file.
        """
        if not output_path.endswith(".mp3"):
            raise ValueError("Output file must have an .mp3 extension.")

        audio = self.client.text_to_speech.convert(
            text=text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )

        save(audio, output_path)

    @override
    def play(self, text: str) -> None:
        """
        Play the given text as audio.

        :param text: The text to play as audio.
        """
        raise NotImplementedError(
            "Playing audio directly is not implemented in ElevenLabsAudioGenerator."
        )
        # self.text_to_audio(text, "temp_audio.mp3")

        # pygame.mixer.init()
        # pygame.mixer.music.load("temp_audio.mp3")
        # pygame.mixer.music.play()

        # Keep the script running until music finishes
        # while pygame.mixer.music.get_busy():
        #     pygame.time.Clock().tick(10)
