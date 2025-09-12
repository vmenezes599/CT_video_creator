"""Utility functions for AI Video Creator project."""

import os
import copy


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


def ensure_collection_index_exists(
    collection: list, index: int, empty_value=None
) -> None:
    """
    Ensure that the collection has enough elements to include the specified index.

    :param collection: The list to check and potentially extend.
    :param index: The index that needs to be accessible in the list.
    :param empty_value: The value to append to the list if it needs to be extended. Defaults to None.
    """
    while len(collection) <= index:
        collection.append(copy.deepcopy(empty_value))
