"""
Custom logger for ComfyUI automation.
"""

import logging
from datetime import datetime

from .environment_variables import COMFYUI_OUTPUT_FOLDER

# Define the global logger
# LOG_FILE = os.path.join(os.path.dirname(__file__), "automation.log")
# LOG_FILE = "ComfyUI_automation.log"
UNIQUE_SUFFIX = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
LOG_FILE = f"{COMFYUI_OUTPUT_FOLDER}/{UNIQUE_SUFFIX}_comfyui_output_sweep.log"
logger = logging.getLogger("ComfyUIAutomationLogger")
logger.setLevel(logging.INFO)

# Avoid adding multiple handlers
if not logger.handlers:
    formatter = logging.Formatter(
        "%(message)s | %(asctime)s - %(levelname)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)


class OldCustomLogger:
    """
    Custom logger class to log messages to a file with a specific format.
    """

    def __init__(self, file_name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level)

        # unique_suffix = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")  # Timestamp
        # self.log_file_name = f"{output_folder}/{unique_suffix}_comfyui_output_sweep.log"

        # Create formatter and add it to the handler
        formatter = logging.Formatter(
            "%(message)s | %(asctime)s - %(levelname)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler = logging.FileHandler(file_name)
        file_handler.setLevel(logging.INFO)

        # Add formatter to ch
        file_handler.setFormatter(formatter)

        # Add ch to logger
        self.logger.addHandler(file_handler)

    def debug(self, *args, **kwargs):
        """
        Log a debug message.
        """
        self.logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        """
        Log an info message.
        """
        self.logger.info(*args, **kwargs)

    def warning(self, *args, **kwargs):
        """
        Log a warning message.
        """
        self.logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        """
        Log an error message.
        """
        self.logger.error(*args, **kwargs)

    def critical(self, *args, **kwargs):
        """
        Log a critical message.
        """
        self.logger.critical(*args, **kwargs)
