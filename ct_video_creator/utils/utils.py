"""Utility functions for AI Video Creator project."""

import os
import copy
import shutil

from pathlib import Path


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


def ensure_collection_index_exists(collection: list, index: int, empty_value=None) -> None:
    """
    Ensure that the collection has enough elements to include the specified index.

    :param collection: The list to check and potentially extend.
    :param index: The index that needs to be accessible in the list.
    :param empty_value: The value to append to the list if it needs to be extended. Defaults to None.
    """
    while len(collection) <= index:
        collection.append(copy.deepcopy(empty_value))


def safe_move(src, dst):
    """
    Move src to dst, avoiding overwrites by appending a numeric suffix.
    If dst is a directory, the source filename is preserved.
    If dst is a file path, it uses that as the target name.
    Returns the final destination path resolved.
    """
    src = Path(src).resolve()
    dst = Path(dst).resolve()

    # If dst is a directory or doesn't exist but has no suffix, treat as directory
    if dst.is_dir() or (not dst.exists() and not dst.suffix):
        dst_dir = dst
        dst = dst_dir / src.name
    else:
        dst_dir = dst.parent

    # Ensure destination directory exists
    dst_dir.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        stem, suffix = dst.stem, dst.suffix
        counter = 1
        # Keep incrementing until we find a free filename
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_dst = dst_dir / new_name
            if not new_dst.exists():
                dst = new_dst
                break
            counter += 1

    shutil.move(str(src), str(dst))
    return dst


def safe_copy(src, dst):
    """
    Copy src to dst, avoiding overwrites by appending a numeric suffix.
    If dst is a directory, the source filename is preserved.
    If dst is a file path, it uses that as the target name.
    Preserves metadata like shutil.copy2.
    Returns the final destination path resolved.
    """
    src = Path(src).resolve()
    dst = Path(dst).resolve()

    # If dst is a directory or doesn't exist but has no suffix, treat as directory
    if dst.is_dir() or (not dst.exists() and not dst.suffix):
        dst_dir = dst
        dst = dst_dir / src.name
    else:
        dst_dir = dst.parent

    # Ensure destination directory exists
    dst_dir.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        stem, suffix = dst.stem, dst.suffix
        counter = 1
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_dst = dst_dir / new_name
            if not new_dst.exists():
                dst = new_dst
                break
            counter += 1

    shutil.copy2(src, dst)
    return dst


def backup_file_to_old(file_path: Path) -> None:
    """
    Back up a file by copying it to a .old version before it gets overwritten.

    This is useful when a file has validation errors (JSON decode, value, type errors)
    and needs to be replaced with a fresh version, but you want to preserve the
    corrupted content for debugging.

    :param file_path: Path to the file to back up.
    """
    if not file_path.exists():
        return

    old_file_path = Path(str(file_path) + ".old")

    # Copy corrupted content to .old (overwrite if exists)
    with open(file_path, "rb") as src:
        with open(old_file_path, "wb") as dst:
            dst.write(src.read())
