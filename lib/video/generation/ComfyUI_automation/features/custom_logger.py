import logging


class CustomLogger:
    """
    Custom logger class to log messages to a file with a specific format.	
    """
    
    def __init__(self, file_name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level)

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
