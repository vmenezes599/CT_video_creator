"""
ComfyUI Automation Helper Functions
"""

import requests
from .environment_variables import CONFYUI_URL


def comfyui_get_queue() -> tuple[bool, int]:
    """
    Get the queue information from ComfyUI.
    """
    response = requests.get(f"{CONFYUI_URL}/prompt", timeout=10)

    if response.ok:
        queue_data = response.json()
        return (True, queue_data["exec_info"]["queue_remaining"])

    print(f"Failed to fetch queue. Status code: {response.status_code}")
    return (False, -1)


def comfyui_get_history() -> tuple[bool, list]:
    """
    Get the history information from ComfyUI.
    """
    try:
        response = requests.get(f"{CONFYUI_URL}/history", timeout=10)

        if response.ok:
            history_data = response.json()
            return (True, history_data)

        print(f"Failed to fetch history. Status code: {response.status_code}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return (False, [])


def comfyui_get_last_history_entry() -> tuple[bool, list]:
    """
    Get the history information from ComfyUI.
    """
    response = requests.get(f"{CONFYUI_URL}/history", timeout=10)

    if response.ok:
        history_data = response.json()
        last_key = list(history_data.keys())[-1]
        return (True, history_data[last_key])

    print(f"Failed to fetch history. Status code: {response.status_code}")
    return (False, [])


def comfyui_get_history_output_name(
    history_entry_dict: dict, use_full_path: bool = False
) -> list[str]:
    """
    Get the output names from a history entry dictionary.
    """
    try:
        result = []
        for _, output_types in history_entry_dict.get("outputs", {}).items():
            for _, value in output_types.items():
                for v in value:
                    if use_full_path:
                        result.append(v["fullpath"])
                    else:
                        result.append(v["filename"])
        return result
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []
