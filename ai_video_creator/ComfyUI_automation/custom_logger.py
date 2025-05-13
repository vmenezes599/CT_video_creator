import logging
import os
from datetime import datetime
from threading import Lock

from ai_video_creator.environment_variables import (
    COMFYUI_OUTPUT_FOLDER,
)  # Adjust as needed


class SingletonLogger:
    """
    Thread-safe Singleton logger class for ComfyUI automation.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls, file_name: str = None, level: int = logging.INFO):
        with cls._lock:
            if cls._instance is None:
                # Auto-generate log file if none provided
                if file_name is None:
                    unique_suffix = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
                    file_name = os.path.join(
                        COMFYUI_OUTPUT_FOLDER, f"{unique_suffix}_comfyui_output.log"
                    )
                cls._instance = super(SingletonLogger, cls).__new__(cls)
                cls._instance._initialize(file_name, level)
        return cls._instance

    def _initialize(self, file_name: str, level: int):
        """
        Initializes the logger with file and formatter.
        """
        self.logger = logging.getLogger("ComfyUIAutomationLogger")
        self.logger.setLevel(level)

        if not self.logger.handlers:
            formatter = logging.Formatter(
                "%(message)s | %(asctime)s - %(levelname)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            file_handler = logging.FileHandler(file_name)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def delete_open_handlers(self):
        """
        Safely closes and removes all file handlers from the logger.
        """
        handlers_to_remove = []
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                log_file_path = handler.baseFilename
                handler.close()
                handlers_to_remove.append((handler, log_file_path))

        for handler, log_file_path in handlers_to_remove:
            self.logger.removeHandler(handler)
            if os.path.exists(log_file_path):
                os.remove(log_file_path)

    def debug(self, *args, **kwargs):
        self.logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        self.logger.info(*args, **kwargs)

    def warning(self, *args, **kwargs):
        self.logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        self.logger.error(*args, **kwargs)

    def critical(self, *args, **kwargs):
        self.logger.critical(*args, **kwargs)
