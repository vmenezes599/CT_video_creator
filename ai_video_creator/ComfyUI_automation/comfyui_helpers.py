"""
ComfyUI Automation Helper Functions
"""


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
