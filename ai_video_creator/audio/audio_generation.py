"""
Audio Generation Module
"""

import os
from abc import ABC, abstractmethod
from typing_extensions import override
from ai_video_creator.utils.utils import get_next_available_filename
from .environment_variables import ELEVENLABS_API_KEY
from ai_video_creator.environment_variables import COMFYUI_OUTPUT_FOLDER

# Pyttsx3AudioGenerator
import pyttsx3

# ElevenLabsAudioGenerator
from elevenlabs import save
from elevenlabs.client import ElevenLabs

# SparkTTSComfyUIAudioGenerator
from ai_video_creator.ComfyUI_automation.comfyui_requests import ComfyUIRequests
from .ComfyUI_automation.comfyui_audio_workflows import SparkTTSVoiceCloneWorkflow


class IAudioGenerator(ABC):
    """
    An interface for audio generation classes.
    """

    @abstractmethod
    def text_to_audio(self, text_list: list[str], output_file_name: str) -> list[str]:
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

    def get_output_directory(self) -> str:
        """
        Get the output directory for generated audio files.

        :return: The output directory path.
        """
        return COMFYUI_OUTPUT_FOLDER


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
    def text_to_audio(self, text_list: list[str], output_file_name: str) -> list[str]:
        """
        Convert the given text to audio and save it to the specified file.

        :param text: The text to convert to audio.
        :param output_path: The path to save the generated audio file.
        """
        output_file_name = os.path.splitext(output_file_name)[0] + ".mp3"

        output_list: list[str] = []
        for text in text_list:
            name = get_next_available_filename(
                f"{COMFYUI_OUTPUT_FOLDER}/{output_file_name}"
            )
            self.engine.save_to_file(text, name)
            self.engine.runAndWait()
            output_list.append(name)

        return output_list

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
    def text_to_audio(self, text_list: list[str], output_file_name: str) -> list[str]:
        """
        Convert the given text to audio and save it to the specified file.
        """
        # Extract the file name without the extension
        output_file_name = os.path.splitext(output_file_name)[0] + ".mp3"

        os.makedirs(
            COMFYUI_OUTPUT_FOLDER, exist_ok=True
        )  # Ensure the output directory exists

        output_list: list[str] = []
        for text in text_list:
            # Generate a unique filename for each audio file
            name = get_next_available_filename(
                f"{COMFYUI_OUTPUT_FOLDER}/{output_file_name}"
            )

            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )

            save(audio, name)
            output_list.append(name)

        return output_list

    @override
    def play(self, text: str) -> None:
        """
        Play the given text as audio.

        :param text: The text to play as audio.
        """
        raise NotImplementedError(
            "Playing audio directly is not implemented in ElevenLabsAudioGenerator."
        )


class SparkTTSComfyUIAudioGenerator(IAudioGenerator):
    """
    A class to generate audio from text using Spark TTS ComfyUI.
    """

    def __init__(self):
        """
        Initialize the SparkTTSComfyUIAudioGenerator class.
        """
        self.requests = ComfyUIRequests()  # Initialize ComfyUI requests

    @override
    def text_to_audio(self, text_list: list[str], output_file_name: str) -> list[str]:
        """
        Convert the given text to audio and save it to the specified file.

        :param text: The text to convert to audio.
        :param output_path: The path to save the generated audio file.
        """
        output_file_name = os.path.splitext(output_file_name)[0]
        workflow_list: list[SparkTTSVoiceCloneWorkflow] = []

        for text in text_list:
            # Generate a unique filename for each audio file
            workflow = SparkTTSVoiceCloneWorkflow()
            workflow.set_prompt(text)
            workflow.set_output_filename(output_file_name)

            workflow_list.append(workflow)

        return self.requests.comfyui_ensure_send_all_prompts(workflow_list)

    @override
    def play(self, text: str) -> None:
        """
        Play the given text as audio.

        :param text: The text to play as audio.
        """
        raise NotImplementedError(
            "Playing audio directly is not implemented in ElevenLabsAudioGenerator."
        )
