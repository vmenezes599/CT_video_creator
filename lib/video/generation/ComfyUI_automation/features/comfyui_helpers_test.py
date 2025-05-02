"""
ComfyUI Automation Helper Functions
"""
from .comfyui_helpers import *

from .environment_variables import CONFYUI_URL

if __name__ == "__main__":
    # print(comfyui_get_queue())
    # print(comfyui_get_history())

    status, last = comfyui_get_last_history_entry()
    if status:
        output_names = comfyui_get_history_output_name(last)
        print("Output names:", output_names)
