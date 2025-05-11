"""
Audio Generation Module
"""

import os

from .audio_generation import Pyttsx3AudioGenerator, ElevenLabsAudioGenerator


def test_elevenlabs():
    generator = ElevenLabsAudioGenerator()

    generator.play("The quick brown fox jumped over the lazy dog.")


def test_pyttsx3():
    """
    Main function to generate audio from text.
    """
    generator = Pyttsx3AudioGenerator()
    voices = generator.get_property("voices")
    for voice in voices:
        generator.set_property("voice", voice.id)
        print(f"Voice: {voice.name}, ID: {voice.id}")
        generator.play("The quick brown fox jumped over the lazy dog.")


if __name__ == "__main__":
    test_elevenlabs()
    # test_pyttsx3()
