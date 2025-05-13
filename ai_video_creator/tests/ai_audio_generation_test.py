import os
import threading
import time
import sys
import pytest
from ai_video_creator.audio.audio_generation import (
    Pyttsx3AudioGenerator,
    ElevenLabsAudioGenerator,
    SparkTTSComfyUIAudioGenerator,
)
from ai_video_creator.utils.utils import get_next_available_filename
from ai_video_creator.ComfyUI_automation.custom_logger import SingletonLogger


@pytest.fixture
def setup_output_directory():
    """Fixture to create and clean up the output directory."""
    output_dir = os.path.abspath("output")
    os.makedirs(output_dir, exist_ok=True)

    yield output_dir

    # Cleanup after the test
    for file in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, file))
    os.rmdir(output_dir)


@pytest.fixture
def init_server_manager():
    """Fixture to initialize the ComfyUIServerManager."""
    from ai_video_creator.ComfyUI_automation.comfyui_server_manager import (
        cli,
        start_comfyui,
        stop_comfyui,
    )
    from ai_video_creator.ComfyUI_automation.comfyui_requests import ComfyUIRequests
    from .environment_variables import TEST_SYS_ARGV

    requests = ComfyUIRequests()
    try:
        requests.comfyui_get_heartbeat()
        yield  # This is where the test runs

    except Exception as e:
        print(f"Server not started yet. Starting server...")

        sys.argv = TEST_SYS_ARGV

        command = cli()

        server_thread = threading.Thread(
            target=start_comfyui, daemon=True, args=(command,)
        )
        server_thread.start()

        # Wait briefly to ensure the server starts

        while True:
            try:
                requests.comfyui_get_heartbeat()
                break
            except Exception as e:
                print(f"Waiting for server to start: {e}")
            time.sleep(2)

        yield  # This is where the test runs

        SingletonLogger().delete_open_handlers()
        SingletonLogger._instance = None  # Reset the singleton instance

        # Stop the server after the test
        stop_comfyui()
        server_thread.join()  # Wait for the thread to finish


def test_get_next_available_filename(setup_output_directory):
    """Test the get_next_available_filename function."""
    output_dir = setup_output_directory
    file_path = os.path.join(output_dir, "test_file.mp3")

    # Create a dummy file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("dummy content")

    # Check the next available filename
    next_file = get_next_available_filename(file_path)
    assert next_file == os.path.join(output_dir, "test_file_1.mp3")


def test_pyttsx3_audio_generator_text_to_audio():
    """Test the Pyttsx3AudioGenerator's text_to_audio method."""
    generator = Pyttsx3AudioGenerator()

    text_list = ["Hello, world!", "This is a test."]
    output_files = generator.text_to_audio(text_list, "output")

    # Check that the correct number of files were generated
    assert len(output_files) == len(text_list)

    # Check that the files exist
    for file in output_files:
        assert os.path.exists(file)

    for file in output_files:
        os.remove(file)


def test_spark_tts_audio_generator_text_to_audio(init_server_manager):
    """Test the SparkTTSComfyUIAudioGenerator's text_to_audio method."""
    generator = SparkTTSComfyUIAudioGenerator()

    text_list = ["Hello, world!", "This is a test."]
    output_files = generator.text_to_audio(text_list, "output")

    # Check that the correct number of files were generated
    assert len(output_files) == len(text_list)

    # Check that the files exist
    for file in output_files:
        assert os.path.exists(file)

    for file in output_files:
        os.remove(file)


@pytest.mark.skip(reason="Skipping this test because it cost money to run.")
def test_elevenlabs_audio_generator_text_to_audio():
    """Test the ElevenLabsAudioGenerator's text_to_audio method."""
    generator = ElevenLabsAudioGenerator()  # Replace with a valid API key

    text_list = ["Hello, world!", "This is a test."]
    output_files = generator.text_to_audio(text_list, "output")

    # Check that the correct number of files were generated
    assert len(output_files) == len(text_list)

    # Check that the files exist
    for file in output_files:
        assert os.path.exists(file)

    for file in output_files:
        os.remove(file)
