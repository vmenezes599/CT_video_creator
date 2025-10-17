"""
ComfyUI Automation Helper Functions
"""

from pathlib import Path
from logging_utils import logger

from ai_video_creator.environment_variables import COMFYUI_INPUT_FOLDER
from ai_video_creator.utils import safe_copy


def comfyui_get_history_output_name(history_entry_dict: dict) -> list[str]:
    """
    Get the output names from a history entry dictionary.
    """

    result = []
    for _, output_types in history_entry_dict.get("outputs", {}).items():
        for _, value in output_types.items():
            for v in value:
                if isinstance(v, dict) and "filename" in v:
                    result.append(v["filename"])
    return result


def copy_media_to_comfyui_input_folder(media_path: Path) -> Path:
    """Copy media file to ComfyUI input folder and return the new path."""

    if not media_path:
        logger.debug("No media path provided, skipping copy.")
        return None

    media_path = Path(media_path)

    if not media_path.exists():
        logger.error(f"Media file does not exist: {media_path}")
        raise FileNotFoundError(f"Media file does not exist: {media_path}")

    comfyui_input_folder = Path(COMFYUI_INPUT_FOLDER)
    complete_target_path = comfyui_input_folder / media_path.name
    complete_target_path = safe_copy(media_path, complete_target_path)
    logger.debug(f"Media copied successfully to: {complete_target_path}")
    return complete_target_path


def delete_media_from_comfyui_input_folder(media_path: Path) -> None:
    """Delete asset from the ComfyUI input folder."""

    if not media_path:
        logger.debug("No media path provided, skipping deletion.")
        return

    media_path = Path(media_path)

    if not media_path.exists():
        logger.error(f"Media file does not exist, cannot delete: {media_path}")
        return

    try:
        media_path.unlink()
        logger.debug(f"Media deleted successfully from: {media_path}")
    except OSError as e:
        logger.error(f"Error deleting media file {media_path}: {e}")


def delete_media_from_comfyui_output_folder(media_path: Path) -> None:
    """Delete asset from the ComfyUI output folder."""
    if not media_path.exists():
        logger.error(f"Media file does not exist, cannot delete: {media_path}")
        return

    try:
        media_path.unlink()
        logger.debug(f"Media deleted successfully from: {media_path}")
    except OSError as e:
        logger.error(f"Error deleting media file {media_path}: {e}")
