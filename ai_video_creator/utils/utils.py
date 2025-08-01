"""Utility functions for AI Video Creator project."""

import os


def get_next_available_filename(file_path: str) -> str:
    """
    Given a file path, return the next available file name by appending a number if the file already exists.

    :param file_path: The original file path.
    :return: The next available file path.
    """
    base, ext = os.path.splitext(file_path)  # Split the file into name and extension
    counter = 1

    # Check if the file exists and increment the counter until an available name is found
    while os.path.exists(file_path):
        file_path = f"{base}_{counter}{ext}"
        counter += 1

    return file_path
