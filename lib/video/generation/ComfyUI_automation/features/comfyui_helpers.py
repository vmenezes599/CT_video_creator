"""
ComfyUI Automation Helper Functions
"""


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
