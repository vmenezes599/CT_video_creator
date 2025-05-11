"""
ComfyUI Automation Helper Functions
"""
from .comfyui_requests import ComfyUIRequests
from .comfyui_helpers import *

if __name__ == "__main__":
    # print(comfyui_get_queue())
    # print(comfyui_get_history())

    request = ComfyUIRequests()
    status, last = request.comfyui_get_last_history_entry()
    if status:
        output_names = comfyui_get_history_output_name(last)
        print("Output names:", output_names)
